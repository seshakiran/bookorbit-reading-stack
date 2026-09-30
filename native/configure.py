#!/opt/homebrew/bin/python3.11
"""Generate native settings once; preserve all existing secrets on reruns."""
import json
import os
from pathlib import Path
import secrets
import subprocess

ROOT = Path(__file__).resolve().parent
for folder in ['config', 'logs', 'backups', 'data/bookorbit', 'data/bookbridge', 'data/audiobookshelf/config', 'data/audiobookshelf/metadata', 'library/books', 'library/comics', 'library/podcasts', 'dock']:
    (ROOT / folder).mkdir(parents=True, exist_ok=True)
os.chmod(ROOT / 'config', 0o700)

def save(name, values):
    path = ROOT / 'config' / f'{name}.json'
    if not path.exists():
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w') as out:
            json.dump(values, out, indent=2)
    return json.loads(path.read_text())

common = {'TZ': 'UTC'}
db = save('postgres', {'PGPASSWORD': secrets.token_hex(24)})
save('bookorbit', {**common, 'NODE_ENV': 'production', 'HOST': '0.0.0.0', 'PORT': '3000',
    'DATABASE_URL': f'postgres://bookorbit:{db["PGPASSWORD"]}@127.0.0.1:54329/bookorbit',
    'APP_URL': 'http://localhost:3000', 'APP_DATA_PATH': str(ROOT / 'data/bookorbit'),
    'LIBRARY_BROWSE_ROOT': str(ROOT / 'library'), 'BOOK_DOCK_PATH': str(ROOT / 'dock'),
    'KOREADER_PLUGIN_PATH': str(ROOT / 'sources/bookorbit/koreader-plugin/bookorbit.koplugin'),
    **{key: secrets.token_hex(32) for key in ['JWT_SECRET', 'PODCAST_ENCRYPTION_KEY', 'EMAIL_ENCRYPTION_KEY', 'BOOK_REQUEST_ENCRYPTION_KEY', 'MIGRATION_ENCRYPTION_KEY', 'SETUP_BOOTSTRAP_TOKEN']}})
save('audiobookshelf', {**common, 'NODE_ENV': 'production', 'HOST': '0.0.0.0', 'PORT': '13378',
    'CONFIG_PATH': str(ROOT / 'data/audiobookshelf/config'), 'METADATA_PATH': str(ROOT / 'data/audiobookshelf/metadata'),
    'FFMPEG_PATH': '/opt/homebrew/bin/ffmpeg', 'FFPROBE_PATH': '/opt/homebrew/bin/ffprobe',
    'SKIP_BINARIES_CHECK': '1', 'SOURCE': 'local'})
save('bookbridge', {**common, 'DATA_DIR': str(ROOT / 'data/bookbridge'), 'BOOKS_DIR': str(ROOT / 'library/books'),
    'STATIC_DIR': str(ROOT / 'sources/bookbridge/static'), 'TEMPLATE_DIR': str(ROOT / 'sources/bookbridge/templates'),
    'HF_HOME': str(ROOT / 'data/bookbridge/huggingface'), 'XDG_CACHE_HOME': str(ROOT / 'data/bookbridge/cache'),
    'BOOKBRIDGE_SECRET_KEY': secrets.token_hex(32), 'PYTHONUNBUFFERED': '1', 'OMP_NUM_THREADS': '2'})
if not (ROOT / 'data/postgres/PG_VERSION').exists():
    pwfile = ROOT / 'config/db-password.tmp'
    pwfile.write_text(db['PGPASSWORD'])
    pwfile.chmod(0o600)
    try:
        subprocess.run(['/opt/homebrew/opt/postgresql@18/bin/initdb', '-D', str(ROOT / 'data/postgres'),
            '-U', 'bookorbit', '--pwfile', str(pwfile), '--auth-local=trust', '--auth-host=scram-sha-256', '--encoding=UTF8'], check=True)
    finally:
        pwfile.unlink()
    with (ROOT / 'data/postgres/postgresql.conf').open('a') as out:
        out.write("\nlisten_addresses = '127.0.0.1'\nport = 54329\nshared_buffers = '128MB'\nmax_connections = 30\n")
public = ROOT / 'sources/bookorbit/server/public'
if not public.exists():
    public.symlink_to(ROOT / 'sources/bookorbit/client/dist', target_is_directory=True)
versions = {}
for service in ['bookorbit', 'bookbridge', 'audiobookshelf']:
    versions[service] = subprocess.check_output(['git', '-C', str(ROOT / 'sources' / service), 'rev-parse', 'HEAD'], text=True).strip()
(ROOT / 'versions.json').write_text(json.dumps(versions, indent=2) + '\n')
print('Native settings prepared. Secrets are private in native/config.')
