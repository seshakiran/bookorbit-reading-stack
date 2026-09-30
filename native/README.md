# Native Mac reading stack

BookOrbit, Audiobookshelf, BookBridge, and PostgreSQL run as native Apple Silicon processes. Docker and a Linux virtual machine are not required. The source revisions used by this installer are recorded in `versions.json`; Python dependencies are recorded in `requirements.lock.txt`.

## Install on another Mac

Requires Apple Silicon macOS, Homebrew, and Apple's command-line tools. Run `bash install.sh`. Initial downloads and compilation take time. Installation creates per-user LaunchAgents, so servers start after login. Use the same account that owns the installation. Do not move the folder after registering services; the LaunchAgents use absolute paths.

After startup, use:

| Service | Local address |
|---|---|
| BookOrbit | http://localhost:3000 |
| Audiobookshelf | http://localhost:13378/audiobookshelf |
| BookBridge | http://localhost:5757 |

Choose either manual setup in the web interfaces or automated onboarding below; do not mix the two for the first accounts. BookOrbit's first-run token is `SETUP_BOOTSTRAP_TOKEN` in `config/bookorbit.json`. For automated first-run setup, run `venv/bin/python onboard.py YOUR_EMAIL`; it creates separate generated passwords in private `config/accounts.json`. After all services are ready, run `venv/bin/python connect.py` to connect BookBridge. Restart BookBridge to reload the global settings, then run the connection checks again if necessary.

## Add books

EPUBs can go directly in `library/books/`. For audiobooks, put each book in `library/books/Author/Title/`. Keep matching EPUB and M4B files in the same title folder. Both managers use the same folder; this avoids duplicate audiobook storage. Native processes run as your user, so this is not a read-only filesystem boundary: edits from either application can affect shared files.

The automated setup creates watched BookOrbit and Audiobookshelf libraries. For manual setup, add the absolute `library/books` path in both apps and enable watching. In BookOrbit also add `library/comics`. Upload through BookOrbit or place files in the watched library. The `dock` folder is available for BookOrbit ingestion; configure its import rules in BookOrbit before relying on automatic routing.

No books or audio are included. Server-side playback was previously tested with generated sample audio.

## Access from readers and phones

Follow the main README's [Mac network and Tailscale instructions](../README.md#reach-the-mac-from-another-device) for address templates, KOReader menu paths and troubleshooting. Replace placeholders locally; never publish your device addresses or personalized plugin packages.

Tailscale must be installed and connected on both the Mac and each supported client. Use the Mac's Tailscale address with the service port, and retain the appropriate application credentials. `localhost` works only on the server itself. Set `APP_URL` in private `config/bookorbit.json` to a reachable base URL and restart BookOrbit when changing it; update the KOReader plugin address separately.

Keep the Mac awake, online and logged in. The services start after user login, not before FileVault unlock. The optional maintenance helper prevents idle sleep during that session. No router port forwarding is required for tailnet access.

## Listening while walking

- iPhone: [Prologue](https://prologue.audio/) supports Audiobookshelf, background playback and offline downloads. Check its current in-app pricing for the features you want.
- Android: [Audiobookshelf Android](https://github.com/advplyr/audiobookshelf-app) connects to the same server.
- On home Wi-Fi, use your Mac's LAN address with port `13378` and the `/audiobookshelf` suffix.
- Away from home, install Tailscale on the phone, sign in to the same tailnet, and use the Mac's Tailscale address with the same port and suffix. Enable Tailscale while streaming.
- Download books to the phone before a walk for offline playback. The Mac does not have to stay online for already-downloaded content.
- Each application has its own login. Use the Audiobookshelf credentials in Prologue or the Android client.

Use BookBridge's account integration screen to connect individual users, then explicitly pair matching EPUBs and audiobooks. A connection test alone does not prove book alignment. Large transcription/alignment jobs can use substantial memory even without Docker. The optional CTC/PyTorch dependency set and Storyteller are not installed.

## Service controls

Run from this directory:

```sh
python3.11 manage.py status
python3.11 manage.py stop bookbridge
python3.11 manage.py start bookbridge
python3.11 manage.py logs audiobookshelf
python3.11 backup.py
python3.11 maintenance.py
```

`maintenance.py` registers a 3am settings backup and `caffeinate -is` to prevent idle sleep during the logged-in session. It does not disable FileVault or enable automatic login. After restarting the Mac, log in before expecting remote streaming. Stop the keep-awake agent with `launchctl bootout gui/$(id -u)/app.bookorbit.native.awake`. Services can be stopped with `manage.py stop`; their LaunchAgent files remain registered for future logins until removed through normal system administration.

Backups include a PostgreSQL dump, consistent SQLite snapshots, secrets, and service metadata. They exclude library media and caches. Back up `library` separately with Time Machine or another backup tool. Settings backups contain credentials and must remain private. No automatic backup retention/deletion is configured.

To restore, stop all applications, preserve the current data, restore the PostgreSQL dump with `pg_restore` into a fresh matching database, restore each SQLite snapshot and settings file, then restart. Paths in JSON configuration must match the destination. Restore should be rehearsed before depending on it; an end-to-end restore has not been tested here.

## Updates and limitations

These are production builds, with no development watcher. BookOrbit's JavaScript heap limit is 1024 MB and Audiobookshelf's is 768 MB; these are heap ceilings, not total process RAM limits. Database and Python processes have separate memory use.

The installer intentionally refuses to overwrite source checkouts at different revisions. For updates, take a backup and build/test a new pinned release separately; database migrations may require restoring a matching backup to roll back. Do not blindly update all Node packages. Upstream Audiobookshelf dependencies currently report npm audit findings, including high/critical items; its locked packages were retained to preserve compatibility. This installation is intended for LAN/Tailscale access.

FFmpeg and Poppler are native Homebrew tools. BookOrbit's optional Kobo conversion binaries and device workflows have not been verified. BookBridge uses its standard Whisper pipeline; CTC and Storyteller are optional future additions. End-to-end phone playback and EPUB/audio alignment require a real book and a connected phone; the server-side audio path was verified with a generated sample.

## Upstream projects

This repository contains deployment helpers. Application sources are fetched from upstream without modifying their interfaces or removing notices:

- https://github.com/bookorbit/bookorbit
- https://github.com/advplyr/audiobookshelf
- https://github.com/cporcellijr/bookbridge

The installed `config`, `data`, `library`, and `backups` directories are private. Share this public repository, not your installed project directory. See [the plugin guide](../docs/PLUGINS.md) and [feature specification](../docs/SPEC.md).
