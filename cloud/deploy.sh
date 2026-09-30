#!/bin/sh
set -eu
cd "$(dirname "$0")"
test -f .env || { echo 'Run python3 prepare.py --domain YOUR_DOMAIN --email YOUR_EMAIL first.'; exit 1; }
docker compose config --quiet
docker compose pull
docker compose up -d
docker compose ps
