# Cloud reading stack

Deploy BookOrbit, Audiobookshelf, BookBridge, PostgreSQL, and automatic HTTPS on a Linux VPS with Docker Engine and Compose v2. This package does not install Docker on your Mac. It is a deployment configuration, not an official release of any upstream application.

## First deployment

1. Use a Linux VPS with persistent disk sized for your library. Start with 4 GB RAM for a small library; alignment and transcoding can require more. This is a starting configuration, not a measured capacity guarantee.
2. Install Docker Engine with its Compose plugin and Python 3 using your server distribution's instructions.
3. Upload this `cloud` directory to the server.
4. Point `books.example.com`, `audio.example.com`, and `bridge.example.com` DNS records at the server. Allow inbound TCP 80/443 and optionally UDP 443.
5. Run `sudo python3 prepare.py --domain example.com --email you@example.com`. This generates private, unique secrets and prepares writable storage. Use your actual domain and email.
6. Run `sudo sh deploy.sh` from this directory.
7. Open each HTTPS address promptly and create its administrator account. BookOrbit's setup token is in `.env`; retrieve it locally with `sudo sed -n 's/^SETUP_BOOTSTRAP_TOKEN=//p' .env`.

In BookOrbit, add `/books/books` and `/books/comics` as libraries. In Audiobookshelf, create a Book library at `/audiobooks`, with the watcher enabled. Add books through BookOrbit or copy them into `storage/library/books/Author/Title/`.

Configure BookBridge's global service settings and your account integrations:

| Service | Internal URL |
|---|---|
| BookOrbit | `http://bookorbit:3000` |
| Audiobookshelf | `http://audiobookshelf:80` (append `/audiobookshelf` if required by the deployed version) |

Use your BookOrbit username/password and an Audiobookshelf API key created in its settings. Pair an EPUB and its audiobook before expecting cross-format progress sync. Storyteller is not included; BookBridge offers read-along generation.

## Phones and sharing

- iPhone/iPad: Prologue supports Audiobookshelf and offline downloads: https://prologue.audio/
- Android: use the official Audiobookshelf Android client linked from https://github.com/advplyr/audiobookshelf-app.
- Enter your HTTPS audio address in the phone app. If the version serves under `/audiobookshelf`, include that suffix.
- Create a separate non-admin account for each listener. Share only content you are entitled to distribute.
- Offline downloads let a walk continue when reception drops.

## Backups and updates

Run `sudo sh backup.sh`; it briefly stops the three applications to snapshot their files consistently, then restarts them. It includes media and credentials. Copy the backups to separate storage.

Images default to upstream moving tags for initial deployment. After validating your install, set `BOOKORBIT_IMAGE`, `ABS_IMAGE`, `BOOKBRIDGE_IMAGE`, `POSTGRES_IMAGE`, and `CADDY_IMAGE` to tested version tags or image digests in `.env`. Updates are explicit: back up, pull selected images, then run `docker compose up -d`. Database migrations can prevent rolling back just an image; preserve the matching database backup.

## Railway

This release targets a Linux VPS because the applications share a filesystem. It is not a one-click Railway template. A Railway version requires persistent storage for every service and a deliberate replacement for the shared library (for example independent imports and API-based integration). Do not deploy this Compose file as stateless services or expect shared host paths to appear across separate Railway services. See https://docs.railway.com/volumes.

## Validation and upstream projects

The native Mac counterparts were built and locally exercised. This cloud Compose configuration has been statically checked but has not been launched against a cloud account. DNS, certificates, container startup, and phone access must be verified on the destination server.

Applications are downloaded from their upstream registries; no application code or personal credentials are bundled here. Preserve their licensing and attribution notices:

- https://github.com/bookorbit/bookorbit
- https://github.com/advplyr/audiobookshelf
- https://github.com/cporcellijr/bookbridge
- https://github.com/caddyserver/caddy
