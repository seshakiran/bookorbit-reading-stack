#!/usr/bin/env python3
"""Check public source paths and common credential shapes without printing values."""
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
allowed = {
    'README.md', 'LICENSE', 'THIRD_PARTY.md', 'CONTRIBUTING.md', '.gitignore',
    '.github/workflows/validate.yml',
    *('docs/' + n for n in ['SPEC.md', 'PLUGINS.md', 'VALIDATION.md']),
    *('scripts/' + n for n in ['check_public_tree.py', 'validate.py']),
    *('native/' + n for n in ['README.md', 'install.sh', 'configure.py', 'run.py',
        'manage.py', 'migrate.py', 'onboard.py', 'connect.py', 'backup.py',
        'maintenance.py', 'versions.json', 'requirements.lock.txt', '.gitignore']),
    *('cloud/' + n for n in ['README.md', 'compose.yaml', 'Caddyfile',
        'prepare.py', 'deploy.sh', 'backup.sh', '.gitignore']),
}
patterns = [
    r'gh[pousr]_[A-Za-z0-9]{30,}', r'github_pat_[A-Za-z0-9_]{30,}',
    r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
    r'eyJ[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}',
    r'postgres(?:ql)?://[^\s:]+:[A-Za-z0-9_!@#$%^&*+-]{16,}@',
    r'/Users/' + r'[A-Za-z0-9_.-]+/',
]
if (ROOT / '.git').exists():
    result = subprocess.run(['git', '-C', str(ROOT), 'ls-files', '-z'], capture_output=True, check=True)
    names = [n for n in result.stdout.decode().split('\0') if n]
    if not names:
        sys.exit('No tracked files; stage the reviewed release files first.')
else:
    names = [str(p.relative_to(ROOT)) for p in ROOT.rglob('*') if p.is_file()]
errors = []
for name in names:
    path = ROOT / name
    if name not in allowed:
        errors.append(f'{name}: not in public release allowlist')
        continue
    if path.is_symlink():
        errors.append(f'{name}: symlinks are not allowed')
        continue
    content = path.read_text()
    if any(re.search(pattern, content) for pattern in patterns):
        errors.append(f'{name}: possible private value; review locally')
if errors:
    sys.exit('\n'.join(errors))
print(f'PASS: {len(names)} public files checked; no flagged paths or credential patterns.')
