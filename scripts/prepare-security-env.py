#!/usr/bin/env python3
"""Move the existing provisioning password out of Git without changing it.

Runs before Compose validation; never prints the credential. On a shallow clone
without the previous provisioning file, require an explicit local env file.
"""
import os
from pathlib import Path
import re
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
target = root / '.secrets/monitoring.env'
key = 'PROMETHEUS_BASIC_AUTH_PASSWORD'
relative = 'grafana/provisioning/datasources/prometheus.yml'

def literal(content):
    match = re.search(r'^\s*basicAuthPassword:\s*(.*?)\s*$', content, re.M)
    if not match:
        return None
    raw = match[1]
    quoted = re.fullmatch(r'''(["'])(.*?)\1(?:\s+#.*)?''', raw)
    value = quoted[2] if quoted else raw.split(' #', 1)[0].strip()
    # Legacy value is a simple literal; never evaluate YAML tags or shell syntax.
    return value if re.fullmatch(r'[A-Za-z0-9_@%+=:,./-]{1,256}', value) else None

def main():
    if target.exists():
        if not re.search(r'^' + key + r'=.+$', target.read_text(), re.M):
            sys.exit('Missing monitoring password in .secrets/monitoring.env')
        target.chmod(0o600)
        return
    value = os.environ.get(key) or literal((root / relative).read_text())
    if not value:
        revisions = subprocess.check_output(
            ['git', '-C', str(root), 'log', '-30', '--format=%H', '--', relative], text=True
        ).splitlines()
        for revision in revisions:
            result = subprocess.run(['git', '-C', str(root), 'show', f'{revision}:{relative}'],
                                    capture_output=True, text=True)
            if result.returncode == 0:
                value = literal(result.stdout)
                if value:
                    break
    if not value or not re.fullmatch(r'[A-Za-z0-9_@%+=:,./-]{1,256}', value):
        sys.exit('Set PROMETHEUS_BASIC_AUTH_PASSWORD or create .secrets/monitoring.env before deployment.')
    target.parent.mkdir(mode=0o700, exist_ok=True)
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as stream:
        stream.write(f'{key}={value}\n')
    print('Monitoring credential moved to ignored .secrets/monitoring.env (mode 600).')

if __name__ == '__main__':
    main()
