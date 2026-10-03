# Validation status

## Previously exercised on the original Apple Silicon installation

- Native BookOrbit, Audiobookshelf, BookBridge and PostgreSQL startup.
- Account setup and BookBridge service connection checks.
- Shared library import of an EPUB and a completed chaptered M4B.
- Local full-book generation experiment: about 3 hours 4 minutes of audio produced in about 2 hours 33 minutes, including configured idle intervals and checks; peak MLX memory about 14.2 GB. An optional generalized Mac studio worker and BookOrbit patch are now bundled. These measurements are specific to the originating installation.
- BookBridge pairing of an Audiobookshelf audiobook with a BookOrbit EPUB, transcription/alignment, and active mapping.
- Real listening progress transferred into BookOrbit and a retrievable KoSync text locator; KoSync login verified locally and over Tailscale.
- Prologue connection/playback reported working by the user. A full phone-to-reader-to-phone test has not yet been observed.
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
- Reader-device round-trip progress accuracy, including before/after narrator commentary and music. Server-side alignment alone does not establish exact device handoff.
- Android e-reader EPUB handwriting positioning across page turns and reopen.
- Handwriting server synchronization/export and Kokoro playback: not yet implemented.

Moving Linux image tags and upstream plugin versions may change behavior. Pin and record tested versions before relying on a production deployment.

## BookOrbit audiobook studio integration

Validated on the originating Apple Silicon Mac:

- Seven targeted server tests cover book access, linked-edition access, creation permission, existing-audio reuse, unsupported formats and invalid links.
- Two frontend composable tests cover navigation to the linked audio edition and visible error handling for a busy studio.
- Five CPU-only worker tests cover EPUB extraction, missing configuration, interrupted jobs, live progress, background-process locking, publication and repeat-start idempotency.
- Server/client typechecks, production builds and full server/client ESLint checks passed.
- A real original 41-word EPUB was created through the BookOrbit UI with the configured narrator. Generation, transcription, mastering and publication completed in approximately 44.5 seconds, producing a 22.9-second M4B with a chapter marker. Peak MLX memory was 9.38 GB; both passages had zero ASR flags. This small sample is not a long-book quality guarantee.
- Audiobookshelf detected the newly published test recording in the shared watched library.
- The completed preview played in the browser. The existing-audio action opened BookOrbit's audiobook player for the explicitly linked edition.
- Live HTTP checks confirmed authentication enforcement, byte-range streaming, invalid-range rejection, no regeneration when existing audio is linked, and rejection of an ebook-only link target.

Not established by these checks: an e-reader/Prologue round trip, fresh-machine dependency installation, Linux synthesis, arbitrary EPUB layout fidelity, or flawless narration of full books. The Linux prebuilt image does not include the optional studio patch.
