# Product specification & TODO list

Status: proposed work, not implemented by this deployment kit.

## Goal

Read an EPUB on an e-ink device, handwrite against a passage, see that note on a phone, and switch to natural-sounding generated audio from the current text position. Keep ownership of the library and support native Mac hosting plus Linux deployment.

## P0 — Preserve and export handwriting

- [ ] Reproduce the reported displaced/small handwriting on an Android e-reader using Stylus Annotations. Record KOReader/plugin versions, orientation, screen dimensions, and layout settings.
- [ ] Fix coordinate mapping where needed; test a pen stroke at all four corners and across a paragraph. Verify persistence after page turns and reopening.
- [ ] Design a versioned stroke format with book identity, chapter/text anchor, original layout, timestamps, and stroke coordinates. Treat reader Lua metadata as untrusted data; never execute uploaded Lua on the server.
- [ ] Upload changed handwriting to BookOrbit with authenticated, per-user ownership checks, retry-safe IDs, offline queueing, and deletion/conflict handling.
- [ ] Preserve original stroke data and a rendered passage snapshot. When EPUB layout changes, show the original snapshot rather than silently placing ink against the wrong words.
- [ ] Add a book-level handwritten-notes gallery, including a mobile layout.
- [ ] Export one passage or selected passages as PNG and PDF, containing the passage, handwriting, title, author, and location. Keep editable originals separately.
- [ ] Include uploaded strokes and images in server backup/restore. Document local `.sdr` backup until synchronization exists.

Acceptance: write on an EPUB, close it, sync, and see the same passage and handwriting on a phone. Export it and verify that no stroke is clipped or displaced. Reconnect after offline edits without duplicates or lost deletions. Confirm another user cannot fetch the notes.

## P1 — On-demand Kokoro listening

- [ ] Evaluate native Kokoro through MLX Audio on Apple Silicon; compare voices before choosing defaults. Provide a separate CPU-capable Linux backend path.
- [ ] Connect through BookOrbit's existing OpenAI-compatible TTS interface where practical. Check response formats, voice discovery, and caption/timing support; do not assume all compatible endpoints supply timestamps.
- [ ] Start from the current EPUB passage. Generate bounded text chunks, prepare upcoming chunks during playback, and cache by content/model/voice/speed.
- [ ] Measure first-audio delay, sustained generation speed, peak memory, and idle memory. Consider idle unloading to reduce background usage.
- [ ] Map playback position back to stable EPUB anchors; test reading → listening → reading across KOReader and iPhone.
- [ ] Test real iPhone lock-screen/background playback, interruptions, seeking, and cellular/Tailscale reconnection.
- [ ] Offer chapter downloads for offline walks with storage limits, progress recovery, and explicit cache deletion.

Acceptance: launch Listen from a passage, hear continuous audio, lock the phone for a walk, and reopen KOReader near the last spoken passage. Download a chapter and play it in airplane mode. Record measured performance rather than promising untested latency.

## P2 — Portable deployment and device experience

- [ ] Review the [community self-hosting guide](#further-reading) when refining the Linux deployment and cross-format workflow; compare its Storyteller/read-aloud, shared-media, and phone-client options with this kit before adopting changes.

- [ ] Reproduce a clean native Mac install and restore on a separate machine.
- [ ] Deploy Linux Compose on a fresh host; verify containers, DNS/TLS, library discovery, phone access, and backup/restore; pin tested image digests.
- [ ] Design Railway deployment around per-service persistent volumes and media distribution. Do not assume services can share a local filesystem.
- [ ] Consider a native Linux/systemd installer after establishing a tested dependency matrix.
- [ ] Document iPhone/Android reader capabilities separately from audio clients.
- [ ] Add a device compatibility matrix for pen latency, palm rejection, EPUB positioning, and PDF exports. Test each device independently; do not infer compatibility across platforms.
- [ ] Add an optional plugin update check that shows versions and preserves notes before an update.

## Design constraints

- Fresh deployments generate fresh credentials; no public demo password or personal provisioning ZIP.
- Handwriting is not currently part of BookOrbit text-highlight sync.
- Text-to-speech is synthesized narration; an EPUB does not contain a commercial audiobook recording.
- Prefer extending existing integrations over replacing the library apps. Review upstream licensing before modifying or redistributing plugins.
- EPUB pagination varies across fonts, screens, and margins. Page numbers alone are not reliable cross-device anchors.
- Handwriting recognition/OCR is a possible later feature; it is distinct from ink capture and is not yet committed scope.

## Further reading

- [The Ultimate Guide for EPUB & Audiobooks Self-Hosting — r/kindlejailbreak](https://www.reddit.com/r/kindlejailbreak/comments/1wt94k6/the_ultimate_guide_for_epub_audiobooks_selfhosting/) by u/Foreignwelcome2. Background on BookOrbit, BookBridge, Storyteller, Audiobookshelf, shared media storage, KOReader, and phone clients. Use it as a reference for future implementation; verify version-specific details against upstream documentation. Its Docker-oriented setup differs from this kit's native Mac installation, and Storyteller/Double Commander are not included here.
