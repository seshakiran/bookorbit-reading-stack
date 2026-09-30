#!/usr/bin/env python3
"""Prepare a fresh Linux deployment without copying anyone else's secrets."""
import argparse
import os
from pathlib import Path
import re
import secrets

p = argparse.ArgumentParser()
p.add_argument('--domain', required=True, help='Parent domain: creates books, audio and bridge subdomains')
p.add_argument('--email', required=True, help='Certificate contact email')
args = p.parse_args()
if not re.fullmatch(r'[a-zA-Z0-9](?:[a-zA-Z0-9.-]*[a-zA-Z0-9])?', args.domain) or '.' not in args.domain:
    p.error('Supply a domain name, without a scheme or path')
if not re.fullmatch(r'[^\s@=]+@[^\s@=]+\.[^\s@=]+', args.email):
    p.error('Supply a valid contact email')
root = Path(__file__).resolve().parent
env = root/'.env'
if env.exists():
    raise SystemExit('.env already exists; preserving existing secrets. Edit it directly if needed.')
os.umask(0o077)
values = {'BOOKS_DOMAIN':f'books.{args.domain}','AUDIO_DOMAIN':f'audio.{args.domain}', 'BRIDGE_DOMAIN':f'bridge.{args.domain}', 'ADMIN_EMAIL':args.email,'TZ':'UTC'}
values.update({key:secrets.token_hex(32) for key in ['POSTGRES_PASSWORD','JWT_SECRET','PODCAST_ENCRYPTION_KEY','EMAIL_ENCRYPTION_KEY','BOOK_REQUEST_ENCRYPTION_KEY','MIGRATION_ENCRYPTION_KEY','SETUP_BOOTSTRAP_TOKEN','BOOKBRIDGE_SECRET_KEY']})
with env.open('x') as out:
    out.write('\n'.join(f'{k}={v}' for k,v in values.items())+'\n')
os.umask(0o022)
for folder in ['library/books','library/comics','dock','bookorbit','bookbridge','podcasts','audiobookshelf/config','audiobookshelf/metadata']:
    path = root/'storage'/folder
    path.mkdir(parents=True,exist_ok=True)
    if os.geteuid() == 0:
        os.chown(path,1000,1000)
print('Fresh configuration generated. Set DNS, then run: docker compose up -d')
