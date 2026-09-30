#!/opt/homebrew/bin/python3.11
import json
import os
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parent
env = os.environ.copy()
env.update(json.loads((root / 'config/bookorbit.json').read_text()))
env['PGPASSWORD'] = json.loads((root / 'config/postgres.json').read_text())['PGPASSWORD']
env['PATH'] = '/opt/homebrew/opt/node@24/bin:/opt/homebrew/opt/postgresql@18/bin:/opt/homebrew/bin:/usr/bin:/bin'
pg = '/opt/homebrew/opt/postgresql@18/bin/'
exists = subprocess.check_output([pg+'psql', '-h', '127.0.0.1', '-p', '54329', '-U', 'bookorbit', '-d', 'postgres', '-tAc', "SELECT 1 FROM pg_database WHERE datname='bookorbit'"], env=env, text=True).strip()
if exists != '1':
    subprocess.run([pg+'createdb', '-h', '127.0.0.1', '-p', '54329', '-U', 'bookorbit', 'bookorbit'], env=env, check=True)
subprocess.run(['/opt/homebrew/opt/node@24/bin/node', 'dist/scripts/migrate.js'], cwd=root/'sources/bookorbit/server', env=env, check=True)
