#!/usr/bin/env python3
"""Configure BookBridge through its settings form, preserving existing values."""
import json
from pathlib import Path
import re
import requests
from bs4 import BeautifulSoup

root = Path(__file__).resolve().parent
accounts = json.loads((root/'config/accounts.json').read_text())
config = json.loads((root/'config/bookbridge.json').read_text())
s = requests.Session()
r = s.post('http://127.0.0.1:5757/login', data=accounts['bookbridge'], timeout=20)
r.raise_for_status()
r = s.get('http://127.0.0.1:5757/settings', timeout=20)
r.raise_for_status()
soup = BeautifulSoup(r.text, 'html.parser')
form = soup.find('input', {'name':'ABS_SERVER'}).find_parent('form')
values = {}
for node in form.select('input[name], select[name], textarea[name]'):
    name = node['name']
    if node.has_attr('disabled') or node.get('type') in ['submit','button','file']:
        continue
    if node.get('type') in ['checkbox','radio'] and not node.has_attr('checked'):
        continue
    if node.name == 'select':
        option = node.find('option', selected=True) or node.find('option')
        values[name] = option.get('value', option.text) if option else ''
    elif node.name == 'textarea':
        values[name] = node.text
    else:
        values[name] = node.get('value','')
values.update({k:config[k] for k in ['ABS_ENABLED','ABS_SERVER','ABS_KEY','BOOKORBIT_ENABLED','BOOKORBIT_SERVER','BOOKORBIT_USER','BOOKORBIT_PASSWORD']})
match = re.search(r'var t = "([^"]+)"', r.text) or re.search(r'var t="([^"]+)"', r.text)
if not match:
    raise RuntimeError('Could not find CSRF token; no settings changed')
values['csrf_token'] = match.group(1)
r = s.post('http://127.0.0.1:5757/settings', data=values, timeout=30)
r.raise_for_status()
print('BookBridge settings saved through authenticated UI form.')
r = s.get('http://127.0.0.1:5757/account/integrations', timeout=20)
r.raise_for_status()
soup = BeautifulSoup(r.text, 'html.parser')
form = soup.find('input', {'name':'ABS_KEY'}).find_parent('form')
values = {}
for node in form.select('input[name], select[name]'):
    if node.get('type') in ['checkbox','radio'] and not node.has_attr('checked'):
        continue
    if node.name == 'select':
        option = node.find('option', selected=True) or node.find('option')
        values[node['name']] = option.get('value', option.text) if option else ''
    else:
        values[node['name']] = node.get('value','')
values.update({k:config[k] for k in ['ABS_ENABLED','ABS_SERVER','ABS_KEY','BOOKORBIT_ENABLED','BOOKORBIT_SERVER','BOOKORBIT_USER','BOOKORBIT_PASSWORD']})
values['csrf_token'] = match.group(1)
r = s.post('http://127.0.0.1:5757/account/integrations', data=values, timeout=30)
r.raise_for_status()
for service in ['abs','bookorbit']:
    r = s.post('http://127.0.0.1:5757/api/account/test-connection/'+service, json={}, headers={'X-CSRF-Token':match.group(1)}, timeout=30)
    r.raise_for_status()
    result = r.json()
    assert result.get('ok'), f'{service}: {result.get("message", "Connection failed")}'
    print(f'PASS: BookBridge account connection to {service}')
