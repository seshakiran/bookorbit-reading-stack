# KOReader, handwriting & fonts

Install plugins on the e-reader. A server installation does not install them on your device. Use official upstream releases and check their current version requirements.

## Choose by purpose

| Component | Purpose | Required for |
|---|---|---|
| [KOReader](https://github.com/koreader/koreader/releases) | Reader application | These reader plugins |
| [BookOrbit companion](https://github.com/bookorbit/bookorbit/tree/main/koreader-plugin) | Library access, progress and text annotation sync | BookOrbit integration |
| [Stylus Annotations](https://github.com/kerivin/stylus-annotations.koplugin/releases) | Ink over EPUB/PDF pages | EPUB handwriting |
| [Ink Away](https://github.com/EmirErtorer/ink-away.koplugin) | Notebook/PDF drawing and export | Optional PDF workflow |

Neither handwriting plugin is required just to read. KOReader is available on Android and supported e-readers, not iOS.

## BookOrbit connection

From your own BookOrbit installation, configure the KOReader integration and download its personalized plugin package. Use a server address reachable by the reader, not `localhost`. Extract `bookorbit.koplugin` into KOReader's plugins folder and restart. Open a book, tap the top-center, choose the crossed-tools tab, then BookOrbit. Follow the [upstream setup guide](https://github.com/bookorbit/bookorbit/tree/main/koreader-plugin).

Personalized packages can contain login credentials: never put them in Git, a shared release, or an issue attachment. For a two-device test, download the same book through the integration, sync after reading, and compare the paragraph on the other device rather than page numbers.

## Android folder layout

Locate the existing KOReader data directory; on many Android installations it is `Internal Storage/koreader`. Storage permissions and installation paths vary. Use the directory that already holds your working plugins.

```text
koreader/
├── plugins/
│   ├── bookorbit.koplugin/main.lua
│   ├── stylus-annotations.koplugin/main.lua
│   └── ink-away.koplugin/main.lua
└── fonts/
```

Extract downloaded archives. Copy the plugin directory, not the ZIP. Avoid an extra nested directory or a `-main` suffix. Fully exit and restart KOReader. Kindle and Kobo paths differ; consult each plugin's installation instructions.

## EPUB handwriting: Stylus Annotations

Requires KOReader `v2026.07.2-60` or later per the [upstream README](https://github.com/kerivin/stylus-annotations.koplugin). Open a book → tap the top-center → second menu tab → **Stylus annotations**, near Highlights → **Enable drawing**.

Adjust width and color; try Live refresh for immediate ink. Some e-ink configurations display strokes only after lifting the pen. EPUB strokes can shift as text reflows. Keep font, margins, and orientation stable for the initial test; device positioning still needs verification.

The plugin saves `stylus_annotations.lua` in the book's sidecar directory, commonly `Book Title.sdr/` beside the book. KOReader settings can relocate that directory. Back up the sidecar with the book. These strokes are separate from typed notes: the current BookOrbit integration does not upload them. The plugin does not currently offer a passage/PDF export; use a page screenshot for sharing. See [source](https://github.com/kerivin/stylus-annotations.koplugin/blob/main/stylus-annotations.koplugin/main.lua) and the [planned export/sync work](SPEC.md).

## PDF handwriting: Ink Away

Open a book → top-center → crossed wrench/screwdriver **Tools** tab → **Ink Away (drawing canvas)**. Its notebook workflow can open a PDF and export PNG, JPEG, or a paged PDF. It does not directly annotate reflowable EPUB text. Projects are stored in its `ink away` folder; back that up separately. Palm rejection depends on the KOReader version and device input support. See [Ink Away's current documentation](https://github.com/EmirErtorer/ink-away.koplugin).

If the menu entry is missing, check the folder layout above and restart. If it still fails, record the exact KOReader and plugin versions before troubleshooting.

## Bookerly and other fonts

Amazon provides a font collection on its [official typography page](https://developer.amazon.com/en-US/alexa/branding/echo-guidelines/identity-guidelines/typography). Download it yourself and review the supplied terms; this repository does not redistribute the fonts.

Copy the extracted Bookerly `.ttf` files into `koreader/fonts/` (create that folder if absent), restart KOReader, then choose Bookerly under **Font face**. If the EPUB's font overrides your choice, turn off **Embedded fonts**; changing embedded styles can also change layout. See the [KOReader user guide](https://koreader.rocks/user_guide/).

Change fonts before adding handwriting: reflow can change where strokes appear.
