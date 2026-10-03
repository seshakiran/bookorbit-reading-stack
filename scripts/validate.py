#!/usr/bin/env python3
"""Side-effect-free source checks plus disposable deployment configuration tests."""
import ast
import json
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
# Limit discovery to source files: never walk installed dependencies or user data.
for folder in ['native', 'cloud', 'scripts', 'studio']:
    for path in (ROOT / folder).glob('*.py'):
        ast.parse(path.read_text(), filename=str(path.relative_to(ROOT)))
    for path in (ROOT / folder).glob('*.sh'):
        subprocess.run(['bash' if folder == 'native' else 'sh', '-n', str(path)], check=True)
versions = json.loads((ROOT / 'native/versions.json').read_text())
assert set(versions) == {'bookorbit', 'audiobookshelf', 'bookbridge'}
assert all(re.fullmatch(r'[0-9a-f]{40}', value) for value in versions.values())
for path in [*ROOT.glob('*.md'), *(ROOT / 'docs').glob('*.md'), ROOT/'native/README.md', ROOT/'cloud/README.md']:
    for target in re.findall(r'\]\(([^\s)]+)\)', path.read_text()):
        if '://' in target or target.startswith('#'):
            continue
        assert (path.parent / target.split('#')[0]).exists(), f'Broken link: {path.name}: {target}'
with tempfile.TemporaryDirectory(prefix='reading-stack-validation-') as tmp:
    stage = Path(tmp)
    shutil.copy2(ROOT / 'cloud/prepare.py', stage / 'prepare.py')
    command = [sys.executable, str(stage/'prepare.py'), '--domain', 'example.com', '--email', 'reader@example.com']
    subprocess.run(command, check=True, capture_output=True)
    env = stage / '.env'
    original = env.read_bytes()
    values = dict(line.split('=', 1) for line in original.decode().splitlines())
    secret_keys = ['POSTGRES_PASSWORD', 'JWT_SECRET', 'PODCAST_ENCRYPTION_KEY',
        'EMAIL_ENCRYPTION_KEY', 'BOOK_REQUEST_ENCRYPTION_KEY', 'MIGRATION_ENCRYPTION_KEY',
        'SETUP_BOOTSTRAP_TOKEN', 'BOOKBRIDGE_SECRET_KEY']
    secrets = [values[k] for k in secret_keys]
    assert len(set(secrets)) == len(secret_keys)
    assert all(re.fullmatch(r'[0-9a-f]{64}', value) for value in secrets)
    assert stat.S_IMODE(env.stat().st_mode) == 0o600
    assert values['BOOKS_DOMAIN'] == 'books.example.com'
    assert (stage/'storage/library/books').is_dir()
    retry = subprocess.run(command, capture_output=True)
    assert retry.returncode != 0 and env.read_bytes() == original
print('PASS: Python, shell, documentation links, revisions, and private configuration smoke checks.')
