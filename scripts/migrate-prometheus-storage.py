#!/usr/bin/env python3
"""Copy the stopped local Prometheus volume; retain the original for rollback."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

TARGET = 'g-stx-infra_prometheus-data'

def run(*args):
    return subprocess.check_output(args, text=True).strip()

def inventory(root):
    result = {}
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            raise RuntimeError(f'Unexpected symlink: {path}')
        if path.is_file():
            digest = hashlib.sha256()
            with path.open('rb') as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                    digest.update(chunk)
            result[str(path.relative_to(root))] = digest.hexdigest()
    return result

def main():
    if os.geteuid() != 0:
        raise RuntimeError('Run as root on the VPS Docker host.')
    container = json.loads(run('docker', 'inspect', 'prometheus'))[0]
    mounts = [m for m in container['Mounts'] if m['Destination'] == '/prometheus']
    if len(mounts) != 1 or mounts[0]['Type'] != 'volume':
        raise RuntimeError('Expected one Docker volume mounted at /prometheus.')
    mount = mounts[0]
    if mount.get('Name') == TARGET:
        print('Persistent volume already attached; nothing to copy.')
        return
    command = container['Config']['Cmd'] or []
    paths = [arg for arg in command if arg.startswith('--storage.tsdb.path')]
    if paths not in ([], ['--storage.tsdb.path=/prometheus/data']):
        raise RuntimeError(f'Unexpected TSDB path flags: {paths}')
    if not paths and container['Config']['WorkingDir'] != '/prometheus':
        raise RuntimeError('Unexpected working directory for default data/ path.')
    source = Path(mount['Source'])
    if not (source / 'data/wal').is_dir():
        raise RuntimeError('Existing TSDB WAL not found; refusing empty migration.')
    users = run('docker', 'ps', '-q', '--filter', f'volume={mount["Name"]}').splitlines()
    if any(not container['Id'].startswith(cid) for cid in users):
        raise RuntimeError('Another running container uses the source volume.')
    run('docker', 'volume', 'create', TARGET)
    target = Path(json.loads(run('docker', 'volume', 'inspect', TARGET))[0]['Mountpoint'])
    if any(target.iterdir()):
        raise RuntimeError('Destination is not empty. Original is untouched; inspect before retrying.')
    was_running = container['State']['Running']
    if was_running:
        run('docker', 'stop', '--time', '60', 'prometheus')
    copied = False
    try:
        before = inventory(source)
        if not before:
            raise RuntimeError('Source is empty.')
        subprocess.run(['cp', '-a', str(source) + '/.', str(target) + '/'], check=True)
        if before != inventory(target) or before != inventory(source):
            raise RuntimeError('Copy verification failed; do not switch volumes.')
        copied = True
        print(f'Verified {len(before)} files. Original volume retained: {mount["Name"]}')
        print('Copy ready. Recreate only Prometheus with the updated Compose file.')
    finally:
        if was_running and not copied:
            run('docker', 'start', 'prometheus')

if __name__ == '__main__':
    main()
