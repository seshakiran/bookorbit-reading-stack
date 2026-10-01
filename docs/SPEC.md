# Product specification & TODO list

Status: roadmap, not features delivered by this deployment kit. A local full-book experiment, a public sample, and server-side audio-to-EPUB handoff have been exercised. The studio is not bundled; device round-trip validation and reproducible studio packaging remain outstanding.

## Goal

Read an EPUB on an e-ink device, handwrite against a passage, see that note on a phone, and switch to natural-sounding generated audio from the current text position. Keep ownership of the library and support native Mac hosting plus Linux deployment.

## P0 — Local audiobook production

Produce complete, chaptered audiobooks locally on Apple Silicon before building on-demand listening. Use the selected **Warm Storyteller** original synthetic voice as the starting narrator: conversational, expressive, moderate in pace, and restrained in drama.

- [ ] Extract EPUB text in reading order, including chapters inside a single HTML file. Review headings, front matter, scientific notation, pronunciation, and duplicate chapter labels before narration.
- [ ] Preserve a reusable voice reference so chapter-to-chapter identity stays consistent. Audition a new book before its full run; do not treat a repeated voice description as a fixed voice identity.
- [ ] Set genre and scene context separately from spoken text where the backend supports direction. Never narrate performance instructions. Document when reference-conditioned generation lacks instruction control.
- [ ] Generate bounded passages sequentially with resumable checkpoints and model/voice/text hashes. Retry or replace faulty passages without regenerating the whole book.
- [ ] Compare generated speech with the source using local transcription; flag missing text, repetitions, unusual pacing, and pronunciation for listening review. Automated checks do not establish studio quality.
- [ ] Master consistent loudness without clipping, retain lossless chapter masters, and assemble one M4B with named chapter markers and title/author/narrator metadata.
- [ ] Add spoken title/author credits and chapter announcements. Keep sourced author notes and related reading separate from the original text; resolve same-name author ambiguity before adding a biography.
- [ ] Offer brief original or appropriately licensed musical chapter transitions that end before speech. Preserve speech-only masters and calculate chapter markers after transitions and tempo changes.
- [ ] Support pitch-preserving mastering pace independently of GPU synthesis, with original recordings retained for reversible adjustments. Keep player speed controls available.
- [ ] Import the completed M4B into the audiobook library and test chapter navigation, adjustable player speed, offline playback, and resume on a phone.
- [ ] Measure wall time, active generation time, audio duration, peak MLX memory, and output size. Estimate remaining time from the current book's measured throughput.
- [ ] Provide one-job-at-a-time operation, configurable idle intervals, safe pause/resume, and model unloading when finished. Idle intervals reduce average load; they are not an instantaneous GPU limit or a hardware-lifespan guarantee.
- [ ] Package the experimental studio with reproducible setup instructions after the first complete-book test. Models, source books, generated recordings, personal configuration, and credentials remain outside the public repository.

Acceptance: convert a locally supplied EPUB into a complete, playable M4B with correct chapter boundaries, no detected missing passages, and reviewed sample passages from across the book. Resume an interrupted run without overwriting approved audio. Publish measured costs and known quality limits, not a promise of human-narrator equivalence.

## P1 — Preserve and export handwriting

- [ ] Reproduce the reported displaced/small handwriting on an Android e-reader using Stylus Annotations. Record KOReader/plugin versions, orientation, screen dimensions, and layout settings.
- [ ] Fix coordinate mapping where needed; test a pen stroke at all four corners and across a paragraph. Verify persistence after page turns and reopening.
- [ ] Design a versioned stroke format with book identity, chapter/text anchor, original layout, timestamps, and stroke coordinates. Treat reader Lua metadata as untrusted data; never execute uploaded Lua on the server.
- [ ] Upload changed handwriting to BookOrbit with authenticated, per-user ownership checks, retry-safe IDs, offline queueing, and deletion/conflict handling.
- [ ] Preserve original stroke data and a rendered passage snapshot. When EPUB layout changes, show the original snapshot rather than silently placing ink against the wrong words.
- [ ] Add a book-level handwritten-notes gallery, including a mobile layout.
- [ ] Export one passage or selected passages as PNG and PDF, containing the passage, handwriting, title, author, and location. Keep editable originals separately.
- [ ] Include uploaded strokes and images in server backup/restore. Document local `.sdr` backup until synchronization exists.

Acceptance: write on an EPUB, close it, sync, and see the same passage and handwriting on a phone. Export it and verify that no stroke is clipped or displaced. Reconnect after offline edits without duplicates or lost deletions. Confirm another user cannot fetch the notes.

## P2 — On-demand Kokoro listening

- [ ] Evaluate native Kokoro through MLX Audio on Apple Silicon; compare voices before choosing defaults. Provide a separate CPU-capable Linux backend path.
- [ ] Connect through BookOrbit's existing OpenAI-compatible TTS interface where practical. Check response formats, voice discovery, and caption/timing support; do not assume all compatible endpoints supply timestamps.
- [ ] Start from the current EPUB passage. Generate bounded text chunks, prepare upcoming chunks during playback, and cache by content/model/voice/speed.
- [ ] Measure first-audio delay, sustained generation speed, peak memory, and idle memory. Consider idle unloading to reduce background usage.
- [ ] Map playback position back to stable EPUB anchors; test reading → listening → reading across KOReader and iPhone.
- [ ] Test real iPhone lock-screen/background playback, interruptions, seeking, and cellular/Tailscale reconnection.
- [ ] Offer chapter downloads for offline walks with storage limits, progress recovery, and explicit cache deletion.

Acceptance: launch Listen from a passage, hear continuous audio, lock the phone for a walk, and reopen KOReader near the last spoken passage. Download a chapter and play it in airplane mode. Record measured performance rather than promising untested latency.

## P3 — Portable deployment and device experience

- [ ] Review the [community self-hosting guide](#further-reading) when refining the Linux deployment and cross-format workflow; compare its Storyteller/read-aloud, shared-media, and phone-client options with this kit before adopting changes.

- [ ] Reproduce a clean native Mac install and restore on a separate machine.
- [ ] Deploy Linux Compose on a fresh host; verify containers, DNS/TLS, library discovery, phone access, and backup/restore; pin tested image digests.
- [ ] Design Railway deployment around per-service persistent volumes and media distribution. Do not assume services can share a local filesystem.
- [ ] Consider a native Linux/systemd installer after establishing a tested dependency matrix.
- [ ] Document iPhone/Android reader capabilities separately from audio clients.
- [ ] Add a device compatibility matrix for pen latency, palm rejection, EPUB positioning, and PDF exports. Test each device independently; do not infer compatibility across platforms.
- [ ] Add an optional plugin update check that shows versions and preserves notes before an update.

## Deferred — Easier reading-profile transfer

Manual LocalSend/file-manager transfer remains documented, but reducing its friction is lower priority than audiobook production.

- [ ] Design an optional export/import bundle for a named KOReader profile such as **Kindle Reader**, using generic source/destination devices.
- [ ] Preview changes, back up existing settings, and merge a selected profile without replacing unrelated profiles. Handle font dependencies and device-specific adjustments explicitly.
- [ ] Exclude credentials, progress, and handwriting from appearance bundles; do not redistribute licensed font files without permission.

## Design constraints

- Fresh deployments generate fresh credentials; no public demo password or personal provisioning ZIP.
- Handwriting is not currently part of BookOrbit text-highlight sync.
- Text-to-speech is synthesized narration; an EPUB does not contain a commercial audiobook recording.
- Prefer extending existing integrations over replacing the library apps. Review upstream licensing before modifying or redistributing plugins.
- EPUB pagination varies across fonts, screens, and margins. Page numbers alone are not reliable cross-device anchors.
- Handwriting recognition/OCR is a possible later feature; it is distinct from ink capture and is not yet committed scope.

## Further reading

- [The Ultimate Guide for EPUB & Audiobooks Self-Hosting — r/kindlejailbreak](https://www.reddit.com/r/kindlejailbreak/comments/1wt94k6/the_ultimate_guide_for_epub_audiobooks_selfhosting/) by u/Foreignwelcome2. Background on BookOrbit, BookBridge, Storyteller, Audiobookshelf, shared media storage, KOReader, and phone clients. Use it as a reference for future implementation; verify version-specific details against upstream documentation. Its Docker-oriented setup differs from this kit's native Mac installation, and Storyteller/Double Commander are not included here.
