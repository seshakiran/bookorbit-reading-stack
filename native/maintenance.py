#!/opt/homebrew/bin/python3.11
"""Install nightly settings backups and prevent idle sleep while serving."""
import os
from pathlib import Path
import plistlib
import subprocess

root = Path(__file__).resolve().parent
agents = Path.home()/'Library/LaunchAgents'
for name, args, schedule in [
    ('backup', ['/opt/homebrew/bin/python3.11',str(root/'backup.py')], {'StartCalendarInterval':{'Hour':3,'Minute':0}}),
    ('awake', ['/usr/bin/caffeinate','-is'], {'RunAtLoad':True,'KeepAlive':True}),
]:
    label = f'app.bookorbit.native.{name}'
    path = agents/f'{label}.plist'
    values = {'Label':label,'ProgramArguments':args,**schedule,'StandardOutPath':str(root/'logs'/f'{name}.log'),'StandardErrorPath':str(root/'logs'/f'{name}.log')}
    with path.open('wb') as out:
        plistlib.dump(values,out)
    if subprocess.run(['launchctl','print',f'gui/{os.getuid()}/{label}'],capture_output=True).returncode != 0:
        subprocess.run(['launchctl','bootstrap',f'gui/{os.getuid()}',str(path)],check=True)
print('Nightly 3am backups and idle-sleep prevention enabled for the logged-in session.')
