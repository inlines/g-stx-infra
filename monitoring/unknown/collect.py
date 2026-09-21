#!/usr/bin/env python3
"""Collect the regional Unknown counters without changing application data."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time


def atomic_write(path, content):
    fd, name = tempfile.mkstemp(prefix='.' + path.name, dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(name, 0o644)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def render(rows, timestamp):
    lines = ['# HELP gstx_unknown_games Games missing the serial selected by the regional catalog card.',
             '# TYPE gstx_unknown_games gauge',
             '# HELP gstx_region_games Eligible games with a release in the UI region (denominator).',
             '# TYPE gstx_region_games gauge',
             '# HELP gstx_unknown_platform_games Unique games missing a serial in at least one UI region.',
             '# TYPE gstx_unknown_platform_games gauge']
    seen = set()
    for row in rows:
        platform = row['platform']
        if not isinstance(platform, str) or platform in seen:
            raise ValueError('Invalid or duplicate platform label')
        seen.add(platform)
        label = platform.replace('\\', '\\\\').replace('\n', '\\n').replace('"', '\\"')
        for key in ('total', 'jap', 'pal', 'usa', 'other', 'jap_total', 'pal_total', 'usa_total', 'other_total'):
            if type(row[key]) is not int or row[key] < 0:
                raise ValueError('Invalid count')
        lines.append(f'gstx_unknown_platform_games{{platform="{label}"}} {row["total"]}')
        for key in ('jap', 'pal', 'usa', 'other'):
            if row[key] > row[key + '_total']:
                raise ValueError('Unknown exceeds regional total')
            lines.append(f'gstx_region_games{{platform="{label}",region="{key.upper()}"}} {row[key + "_total"]}')
            lines.append(f'gstx_unknown_games{{platform="{label}",region="{key.upper()}"}} {row[key]}')
    lines += ['# HELP gstx_unknown_last_success_timestamp_seconds Last successful database snapshot.',
              '# TYPE gstx_unknown_last_success_timestamp_seconds gauge',
              f'gstx_unknown_last_success_timestamp_seconds {timestamp:.3f}']
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--infra-dir', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--output-dir', type=Path, default=Path('/var/lib/game-stockx-igdb/metrics'))
    # Explicit local-test overrides; production uses the existing Compose postgres service.
    parser.add_argument('--container')
    parser.add_argument('--database', default='gstx')
    parser.add_argument('--db-user', default='postgres')
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with (args.output_dir / '.unknown.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return 0
        start = time.time()
        success = False
        try:
            command = (['docker', 'exec', '-i', args.container] if args.container else
                       ['docker', 'compose', 'exec', '-T', 'postgres'])
            command += ['psql', '-XqAt', '-U', args.db_user, '-d', args.database,
                        '-v', 'ON_ERROR_STOP=1', '-f', '-']
            result = subprocess.run(command, cwd=args.infra_dir, text=True,
                                    input=Path(__file__).with_name('counts.sql').read_text(),
                                    capture_output=True, timeout=35, check=True)
            rows = json.loads(result.stdout)
            if not isinstance(rows, list) or not rows:
                raise ValueError('No active platforms returned; retain last good snapshot')
            atomic_write(args.output_dir / 'unknown.prom', render(rows, time.time()))
            success = True
            print(f'Unknown snapshot: {len(rows)} platforms, {len(rows)*4} regional counters')
        except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
            print(f'Unknown collection failed ({type(error).__name__}); previous snapshot retained.', file=sys.stderr)
        finally:
            atomic_write(args.output_dir / 'unknown-status.prom',
                '# HELP gstx_unknown_collection_success Whether the latest collection succeeded.\n'
                '# TYPE gstx_unknown_collection_success gauge\n'
                f'gstx_unknown_collection_success {int(success)}\n'
                '# HELP gstx_unknown_collection_duration_seconds Latest collection duration.\n'
                '# TYPE gstx_unknown_collection_duration_seconds gauge\n'
                f'gstx_unknown_collection_duration_seconds {time.time()-start:.3f}\n')
        return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
