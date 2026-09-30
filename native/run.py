#!/opt/homebrew/bin/python3.11
"""Launch one production service with private, project-local configuration."""
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
service = sys.argv[1]
env = os.environ.copy()
env.update(json.loads((ROOT / 'config' / f'{service}.json').read_text()))
env['LC_ALL'] = 'en_US.UTF-8'
env['LANG'] = 'en_US.UTF-8'
env['PATH'] = f'{ROOT}/venv/bin:/opt/homebrew/opt/node@24/bin:/opt/homebrew/opt/postgresql@18/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin'
commands = {
    'postgres': ['/opt/homebrew/opt/postgresql@18/bin/postgres', '-D', str(ROOT / 'data/postgres')],
    'bookorbit': ['/opt/homebrew/opt/node@24/bin/node', '--max-old-space-size=1024', 'dist/main.js'],
    'audiobookshelf': ['/opt/homebrew/opt/node@24/bin/node', '--max-old-space-size=768', 'dist-server/index.js'],
    'bookbridge': [str(ROOT / 'venv/bin/python'), '-m', 'src.web_server'],
}
cwd = ROOT if service == 'postgres' else ROOT / 'sources' / service
if service == 'bookorbit':
    cwd /= 'server'
os.chdir(cwd)
os.execve(commands[service][0], commands[service], env)
