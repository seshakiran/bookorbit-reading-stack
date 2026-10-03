# Create an audiobook inside BookOrbit

The native Mac installer applies a small patch to the pinned upstream BookOrbit source. Each book's Details page gains **Listen or create an audiobook**. Existing audio uses BookOrbit's player. A configured Apple Silicon worker can narrate an EPUB into a chaptered M4B locally.

## Use it

1. Open a book in BookOrbit and select **Details**.
2. If the entry already contains audio, click **Listen to existing audiobook**.
3. If the audio is a separate BookOrbit entry, expand **Already have audio in another BookOrbit entry?** Enter that entry's numeric book ID from its URL and click **Link existing audio**. Links belong to the signed-in user, and both books must be accessible to that user. This is an explicit edition choice; titles alone are not reliable matches.
4. If no audio is linked, an account with **App settings** permission can click **Create audiobook**. EPUB is currently required. The initial narrator is configured by the administrator; this release does not provide a voice picker.
5. Keep the Mac awake. The page polls progress every five seconds; leaving the page does not stop creation. Only one studio job can run at a time. A second request receives a busy message, rather than starting another GPU job.
6. After interruption or failure, return to the same book and choose **Resume audiobook creation**. Matching audio checkpoints are reused. A changed source or narrator is rejected instead of silently combining incompatible takes. Check the private worker log if a run fails.
7. The result is available as a preview and **Download M4B**. Automated transcription flags identify passages to listen to; they are not proof that the narration is wrong or that the remainder is perfect.
8. A completed M4B is also copied alongside the source EPUB. Existing media is never overwritten. Let BookOrbit and Audiobookshelf scan that watched folder. If the audio imports as a separate BookOrbit entry, link it with step 3.
9. In Prologue, refresh the Audiobookshelf library and download the book. Pair the exact EPUB and audio edition in BookBridge before expecting KOReader handoff. Follow the [walk-and-read workflow](../README.md#read--walk-and-listen--keep-reading).

The studio preview has no progress sync. BookOrbit playback and an edition link alone do not establish Audiobookshelf/KOReader alignment. The first release deliberately keeps that explicit BookBridge pairing step.

## Configure Apple Silicon narration

Install the normal native stack first. From the repository root:

```sh
python3.11 studio/setup.py
```

This creates an isolated environment and private configuration, generates an original synthetic narrator reference, and creates a six-second musical cue. The initial model downloads require disk space and internet access. FFmpeg must be installed. No credentials or book text are sent to a hosted speech API.

For an existing installation, apply the patch and rebuild once:

```sh
python3.11 scripts/apply_studio.py native/sources/bookorbit
export PATH="/opt/homebrew/opt/node@24/bin:$PWD/native/tools/node_modules/.bin:$PATH"
(cd native/sources/bookorbit && pnpm run build:server && pnpm --filter client run build-only)
python3.11 native/manage.py stop bookorbit
python3.11 native/manage.py start bookorbit
```

The normal Mac installer applies the patch automatically before building. A different upstream revision is rejected to avoid silently applying incompatible changes. Refresh the browser after rebuilding.

You may supply an original or authorized narrator WAV and its adjacent matching `.txt` transcript:

```sh
python3.11 studio/setup.py --reference /absolute/private/path/narrator.wav
```

Optional `--python` and `--qa-python` reuse existing MLX Audio and faster-whisper environments. All reference assets remain private. The generated default reference is a new audition, not the exact private voice heard in the public sample.

Private settings live in `native/data/audiobook-studio/config.json`. The native server configuration receives `STUDIO_PYTHON`, `STUDIO_WORKER`, and `STUDIO_CONFIG`; these contain local paths, not browser-visible secrets. `model_cache` can optionally point to an existing Hugging Face cache. Each job lives under `jobs/<user-id>-<book-id>/` with source script, checkpoint WAVs, logs, quality reports and the final M4B. Include these in private backups if you want resumability; raw audio can consume substantial disk space.

## Narration behavior and limits

- Qwen3-TTS Base 1.7B through MLX with a fixed synthetic reference, preserving a stable narrator across passages.
- Sequential generation with a 50% synthesis duty cycle, followed by CPU transcription and mastering. This is pacing, not an instantaneous GPU utilization or temperature limit.
- Pitch-preserving 0.93 mastering pace; adjust the player speed later.
- Six-second chapter cues, chapter markers, and title/author metadata.
- EPUB spine order with text extracted from headings, paragraphs, lists and tables. Sections follow EPUB spine items, which do not always correspond to printed chapters. Images, equations, DRM-protected content, complex layout and editorial front matter need manual review.
- No automatically invented quotes, author biographies or spoken opinions. The earlier curated Marvin production included reviewed additions; this one-click path does not invent them for arbitrary books.
- Creation is currently Apple Silicon only. The existing Linux Compose stack still supports playback and BookBridge, but its prebuilt BookOrbit image does not include this source patch or an MLX worker. Do not expect creation controls on Linux until deploying a compatible custom build and worker backend.
- Generated media is placed in the source library and follows that library's sharing/access rules. Job state and edition links remain per user.
- Failed jobs retain checkpoints for explicit resume. There is no automatic queue, cancellation UI, or automatic BookBridge alignment in this release.

The BookOrbit patch and derived UI/server code retain upstream's AGPL-3.0-only license. Original studio helper scripts follow the repository license. Keep books, models, reference recordings, private configuration and generated full audiobooks out of public commits.
