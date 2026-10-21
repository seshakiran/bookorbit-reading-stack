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

## Kindle Fetch automatic reader uploads — October 20, 2026

User-confirmed on the originating **Viwoods AiPaper Mini** with **Kindle Fetch 0.9.0** and the existing BookOrbit installation:

- A manual upload of an existing reader book succeeded.
- After applying the [documented Tailscale setup](PLUGINS.md#tailscale-settings-confirmed-on-the-original-reader), a newly downloaded book appeared automatically in BookOrbit without a manual Send action or VPN toggle.
- Tailscale stayed connected; the reader used no exit node, Tailscale DNS was disabled, and Kindle Fetch encrypted DNS stayed enabled. The saved server URL used a numeric tailnet address.
- Before the live test, all 52 installed plugin package files were read back through OpenMTP and matched the source package byte for byte.
- The [plugin repository](https://github.com/seshakiran/kindlefetch.koplugin) passed Lua 5.1 and 5.4 CI checks. Its mocked regressions cover native sessions, multipart streaming, queue persistence, duplicate suppression, and failure handling. A separate local LuaSocket wire test exercised login, token refresh and multipart bytes against a test server.

The live success was reported by the user; automated tests did not operate the physical reader. This does not establish every network/VPN combination, a fresh device install, metadata-processing completion, resumable transfers, or all recovery scenarios. No BookOrbit server code change was required for this file-upload workflow. It is separate from the reading/audio progress round trip still listed above.

## BookOrbit reader dashboard search integration

The optional BookOrbit reader **1.5.5** patch is tested against the exact catalog file from the pinned upstream revision. Automated checks exercise the actual patched search-dialog function with reader-widget mocks: library search and scope/recent behavior remain intact, the new Z-Library action hands off the entered query, blank queries do nothing, missing/failed handoffs show a controlled message, and the catalog is retained underneath. Patch application is hash-guarded, idempotent, and refuses unknown local modifications. Kindle Fetch 0.9.1 adds its own regression for query normalization and handoff ownership/teardown.

Kindle Fetch 0.9.1 and the BookOrbit 1.5.5 catalog patch were installed on the originating Viwoods reader through OpenMTP. All 54 deployed files were read back and matched the reviewed payload byte for byte. These automated tests and readback checks do not operate the physical reader UI. The prior live download → automatic upload confirmation above covers the reused Kindle Fetch path; the later 0.10.0 user-confirmed dashboard test is recorded below.

## BookOrbit import-before-open update (Kindle Fetch 0.10.0)

New automated coverage verifies explicit BookOrbit context, completion only after a persisted upload confirmation, retained source identity, reuse of pending/completed and compatible legacy jobs, no opening of uncertain jobs, server-destination validation, imports with standalone auto-upload off, prompt-free transfers without a duplicate automatic enqueue, and concurrent-download rejection. The actual patched BookOrbit callback is exercised with widget/API mocks: it persists the confirmed book/file/local-path association before opening, uses no second file-transfer call, handles missing local files, and avoids stealing focus after the catalog closes. Both original-catalog application and previous-patch upgrade are hash-checked and tested for idempotency.

Kindle Fetch 0.10.0 and the companion BookOrbit catalog patch were installed on the originating Viwoods through OpenMTP. All 55 payload files were copied back and matched the reviewed source byte for byte. Both repositories passed their GitHub checks. On **October 20, 2026**, the user confirmed the restarted reader flow: **“Uploads and opens; no second prompt.”** This verifies the BookOrbit dashboard import and subsequent opening without another download prompt on the originating setup. The result is user-reported; automated tests did not operate the physical reader. It does not establish fresh-device compatibility, every network setup, long transfers, or all interrupted-upload recovery paths. Standalone Kindle Fetch retains its existing auto-upload setting.
