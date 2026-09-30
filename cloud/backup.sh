#!/bin/sh
set -eu
cd "$(dirname "$0")"
umask 077
mkdir -p backups
stamp=$(date +%Y%m%d-%H%M%S)
docker compose stop bookorbit audiobookshelf bookbridge
trap 'docker compose start bookorbit audiobookshelf bookbridge' EXIT HUP INT TERM
docker compose exec -T postgres pg_dump -U bookorbit -d bookorbit -Fc > "backups/database-$stamp.dump"
tar -czf "backups/storage-$stamp.tar.gz" .env storage
echo "Backed up database, settings, and media. Copy backups off this server."
