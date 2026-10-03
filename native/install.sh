#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
ROOT="$PWD"
[[ "$(uname -s)" == Darwin && "$(uname -m)" == arm64 ]] || { echo 'This installer targets Apple Silicon macOS.'; exit 1; }
command -v brew >/dev/null || { echo 'Install Homebrew first: https://brew.sh'; exit 1; }
brew install node@24 postgresql@18 pgvector ffmpeg poppler python@3.11
export PATH="/opt/homebrew/opt/node@24/bin:/opt/homebrew/bin:$PATH"
mkdir -p sources tools cache
python3.11 - <<'PY'
import json, subprocess
from pathlib import Path
versions = json.loads(Path('versions.json').read_text())
repos = {'bookorbit':'bookorbit/bookorbit','audiobookshelf':'advplyr/audiobookshelf','bookbridge':'cporcellijr/bookbridge'}
for name, repo in repos.items():
    path = Path('sources')/name
    if path.exists():
        actual = subprocess.check_output(['git','-C',str(path),'rev-parse','HEAD'],text=True).strip()
        if actual != versions[name]:
            raise SystemExit(f'{name}: existing version differs; refusing to overwrite')
        continue
    subprocess.run(['git','init',str(path)],check=True)
    subprocess.run(['git','-C',str(path),'remote','add','origin',f'https://github.com/{repo}.git'],check=True)
    subprocess.run(['git','-C',str(path),'fetch','--depth','1','origin',versions[name]],check=True)
    subprocess.run(['git','-C',str(path),'checkout','--detach','FETCH_HEAD'],check=True)
PY
npm install --prefix "$ROOT/tools" pnpm@11.22.0 --cache "$ROOT/cache/npm"
export PATH="$ROOT/tools/node_modules/.bin:$PATH"
python3.11 ../scripts/apply_studio.py "$ROOT/sources/bookorbit"
(cd sources/bookorbit && pnpm install --frozen-lockfile && pnpm run build:server && pnpm --filter client run build-only)
(cd sources/audiobookshelf && npm ci --cache "$ROOT/cache/npm" && npm run build:server && npm --prefix client ci --cache "$ROOT/cache/npm" && npm --prefix client run generate)
python3.11 -m venv venv
venv/bin/pip install -r requirements.lock.txt
python3.11 configure.py
python3.11 manage.py start postgres audiobookshelf bookbridge
for attempt in {1..30}; do /opt/homebrew/opt/postgresql@18/bin/pg_isready -h 127.0.0.1 -p 54329 >/dev/null && break; sleep 1; done
python3.11 migrate.py
python3.11 manage.py start bookorbit
echo 'Servers installed. Open http://localhost:3000, http://localhost:13378/audiobookshelf, and http://localhost:5757 to create accounts.'
echo 'Retrieve the BookOrbit setup token from config/bookorbit.json. See README.md.'
