#!/opt/homebrew/bin/python3.11
"""Consistent database snapshots plus service settings; media backed up separately."""
from datetime import datetime
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import tarfile
import tempfile

root = Path(__file__).resolve().parent
os.umask(0o077)
stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
target = root/'backups'/f'settings-{stamp}.tar.gz'
env = os.environ.copy()
env['PGPASSWORD'] = json.loads((root/'config/postgres.json').read_text())['PGPASSWORD']
with tempfile.TemporaryDirectory(dir=root/'backups') as staging:
    stage = Path(staging)
    subprocess.run(['/opt/homebrew/opt/postgresql@18/bin/pg_dump','-h','127.0.0.1','-p','54329','-U','bookorbit','-d','bookorbit','-Fc','-f',str(stage/'bookorbit.dump')],env=env,check=True)
    snapshots = []
    for service in ['bookbridge','audiobookshelf']:
        for source in (root/'data'/service).rglob('*.db'):
            relative = source.relative_to(root)
            dest = stage/relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(f'file:{source}?mode=ro', uri=True) as src, sqlite3.connect(dest) as dst:
                src.backup(dst)
            snapshots.append(source)
    with tarfile.open(target, 'w:gz') as archive:
        archive.add(stage, arcname='snapshots')
        archive.add(root/'config', arcname='config')
        archive.add(root/'versions.json', arcname='versions.json')
        for service in ['bookorbit','bookbridge','audiobookshelf']:
            for source in (root/'data'/service).rglob('*'):
                if not source.is_file() or source in snapshots or source.name.endswith(('-wal','-shm')):
                    continue
                if any(part in {'cache','.cache','huggingface','audio_cache','transcripts','streams','logs','backups'} for part in source.relative_to(root/'data'/service).parts):
                    continue
                archive.add(source, arcname=str(source.relative_to(root)))
print(f'Backup saved: {target.name} (private credentials included; media excluded)')
