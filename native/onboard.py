#!/usr/bin/env python3
"""Idempotent first-run accounts and libraries. Never prints credentials."""
import json
import os
from pathlib import Path
import secrets
import sys
import requests

if len(sys.argv) != 2 or '@' not in sys.argv[1]:
    sys.exit('Usage: venv/bin/python onboard.py YOUR_EMAIL')

ROOT = Path(__file__).resolve().parent
path = ROOT / 'config/accounts.json'
if not path.exists():
    accounts = {name: {'username': 'admin', 'password': 'Bo9!' + secrets.token_urlsafe(24)} for name in ['bookorbit', 'audiobookshelf', 'bookbridge']}
    accounts['bookorbit']['email'] = sys.argv[1]
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w') as out:
        json.dump(accounts, out, indent=2)
accounts = json.loads(path.read_text())

def call(session, method, url, **kwargs):
    response = session.request(method, url, timeout=30, **kwargs)
    if response.status_code >= 400:
        raise RuntimeError(f'{method} {url}: HTTP {response.status_code}: {response.text[:300]}')
    return response

absbase = 'http://127.0.0.1:13378/audiobookshelf'
abs_session = requests.Session()
if not call(abs_session, 'GET', absbase+'/status').json()['isInit']:
    call(abs_session, 'POST', absbase+'/init', json={'newRoot': accounts['audiobookshelf']})
user = call(abs_session, 'POST', absbase+'/login', json=accounts['audiobookshelf']).json()['user']
abs_session.headers['Authorization'] = 'Bearer '+user['accessToken']
libs = call(abs_session, 'GET', absbase+'/api/libraries').json()['libraries']
if not any(lib['name'] == 'Audiobooks' for lib in libs):
    call(abs_session, 'POST', absbase+'/api/libraries', json={'name': 'Audiobooks', 'mediaType': 'book', 'folders': [{'fullPath': str(ROOT/'library/books')}], 'settings': {'disableWatcher': False}})
keypath = ROOT/'config/abs-integration.json'
if not keypath.exists():
    key = call(abs_session, 'POST', absbase+'/api/api-keys', json={'name': 'BookBridge', 'userId': user['id'], 'isActive': True}).json()['apiKey']['apiKey']
    with os.fdopen(os.open(keypath, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w') as out:
        json.dump({'key': key}, out)
print('Audiobookshelf account, library watcher, and integration key ready.')

bo = requests.Session()
base = 'http://127.0.0.1:3000/api/v1'
settings = json.loads((ROOT/'config/bookorbit.json').read_text())
login = bo.post(base+'/auth/login', json={k: accounts['bookorbit'][k] for k in ['username','password']}, timeout=30)
if login.status_code == 401:
    login = call(bo, 'POST', base+'/auth/setup', json={**accounts['bookorbit'], 'name': 'BookOrbit Admin'}, headers={'x-setup-token': settings['SETUP_BOOTSTRAP_TOKEN']})
login.raise_for_status()
token = login.json().get('accessToken')
if token:
    bo.headers['Authorization'] = 'Bearer '+token
libs = call(bo, 'GET', base+'/libraries').json()
if isinstance(libs, dict):
    libs = libs.get('data', libs.get('items', []))
for name, folder, icon in [('Books & Audiobooks', 'books', 'BookOpen'), ('Comics', 'comics', 'BookImage')]:
    if not any(lib['name'] == name for lib in libs):
        call(bo, 'POST', base+'/libraries', json={'name':name, 'icon':icon, 'folders':[str(ROOT/'library'/folder)], 'watch':True})
print('BookOrbit account and shared libraries ready.')

bb = requests.Session()
response = call(bb, 'GET', 'http://127.0.0.1:5757/setup')
if '/setup' in response.url:
    call(bb, 'POST', 'http://127.0.0.1:5757/setup', data={**accounts['bookbridge'], 'confirm_password':accounts['bookbridge']['password']})
bbconfig = ROOT/'config/bookbridge.json'
values = json.loads(bbconfig.read_text())
values.update({'ABS_ENABLED':'true','ABS_SERVER':absbase,'ABS_KEY':json.loads(keypath.read_text())['key'],
    'BOOKORBIT_ENABLED':'true','BOOKORBIT_SERVER':'http://127.0.0.1:3000','BOOKORBIT_USER':accounts['bookorbit']['username'],'BOOKORBIT_PASSWORD':accounts['bookorbit']['password']})
bbconfig.write_text(json.dumps(values, indent=2))
print('BookBridge account created and service connections configured; restart BookBridge to apply.')
