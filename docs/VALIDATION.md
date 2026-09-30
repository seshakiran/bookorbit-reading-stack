# Validation status

## Previously exercised on the original Apple Silicon installation

- Native BookOrbit, Audiobookshelf, BookBridge and PostgreSQL startup.
- Account setup and BookBridge service connection checks.
- Shared library import of an EPUB.
- Audiobookshelf test audio session, partial-content seek/download responses and progress requests.
- Native backup generation and launchd maintenance registration.

These observations describe the originating installation. They do not establish a successful clean install on every Mac or full phone/device compatibility.

## Release checks

`python3 scripts/check_public_tree.py` checks tracked paths, disallowed runtime files and common credential patterns without printing secret values.

`python3 scripts/validate.py` parses Python, checks shell syntax and relative documentation links, verifies pinned revision shapes, and exercises Linux configuration generation in a temporary directory. It verifies secret uniqueness, restrictive permissions and refusal to overwrite existing configuration. It does not start servers or alter an installed library.

CI also runs `docker compose config --quiet` with generated disposable settings. No images or databases are started by this check.

## Still required

- Clean install and full restore on a separate Mac.
- Linux container startup, permissions, TLS, DNS, library discovery and restore on a real host.
- iPhone/Android background playback, offline downloads and network reconnection.
- Matching EPUB/audiobook alignment and round-trip progress accuracy.
- Viwoods EPUB handwriting positioning across page turns and reopen.
- Handwriting server synchronization/export and Kokoro playback: not yet implemented.

Moving Linux image tags and upstream plugin versions may change behavior. Pin and record tested versions before relying on a production deployment.
