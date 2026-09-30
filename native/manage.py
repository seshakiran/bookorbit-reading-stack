#!/opt/homebrew/bin/python3.11
"""Manage native BookOrbit services through macOS launchd."""
import json
import os
from pathlib import Path
import plistlib
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parent
SERVICES = ['postgres', 'bookorbit', 'audiobookshelf', 'bookbridge']
DOMAIN = f'gui/{os.getuid()}'
AGENTS = Path.home() / 'Library/LaunchAgents'
command = sys.argv[1] if len(sys.argv) > 1 else 'status'
selected = sys.argv[2:] or SERVICES
if any(s not in SERVICES for s in selected):
    sys.exit('Unknown service')
for service in selected:
    label = f'app.bookorbit.native.{service}'
    plist = AGENTS / f'{label}.plist'
    if command == 'start':
        AGENTS.mkdir(parents=True, exist_ok=True)
        settings = {'Label': label, 'ProgramArguments': ['/opt/homebrew/bin/python3.11', str(ROOT / 'run.py'), service],
            'RunAtLoad': True, 'KeepAlive': True, 'ThrottleInterval': 15,
            'WorkingDirectory': str(ROOT), 'StandardOutPath': str(ROOT / 'logs' / f'{service}.log'),
            'StandardErrorPath': str(ROOT / 'logs' / f'{service}.log')}
        with plist.open('wb') as out:
            plistlib.dump(settings, out)
        exists = subprocess.run(['launchctl', 'print', f'{DOMAIN}/{label}'], capture_output=True).returncode == 0
        if not exists:
            subprocess.run(['launchctl', 'bootstrap', DOMAIN, str(plist)], check=True)
        print(f'{service}: started; starts automatically at login')
    elif command == 'stop':
        subprocess.run(['launchctl', 'bootout', f'{DOMAIN}/{label}'], check=False)
        for _ in range(30):
            if subprocess.run(['launchctl', 'print', f'{DOMAIN}/{label}'], capture_output=True).returncode != 0:
                break
            time.sleep(1)
        else:
            sys.exit(f'{service}: still stopping; retry status before starting')
    elif command == 'status':
        result = subprocess.run(['launchctl', 'print', f'{DOMAIN}/{label}'], text=True, capture_output=True)
        status = [line.strip() for line in result.stdout.splitlines() if 'state =' in line or 'pid =' in line]
        print(service + ': ' + (', '.join(status) or 'not loaded'))
    elif command == 'logs':
        subprocess.run(['tail', '-n', '30', str(ROOT / 'logs' / f'{service}.log')])
    else:
        sys.exit('Usage: manage.py start|stop|status|logs [postgres|bookorbit|audiobookshelf|bookbridge]')
