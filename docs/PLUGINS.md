# KOReader, handwriting & fonts

Install plugins on the e-reader. A server installation does not install them on your device. Use official upstream releases and check their current version requirements.

## Choose by purpose

| Component | Purpose | Required for |
|---|---|---|
| [KOReader](https://github.com/koreader/koreader/releases) | Reader application | These reader plugins |
| [Kindle Fetch](https://github.com/seshakiran/kindlefetch.koplugin) | Z-Library search, local downloads and automatic BookOrbit uploads | Optional reader-to-library acquisition |
| [BookOrbit companion](https://github.com/bookorbit/bookorbit/tree/main/koreader-plugin) | Library access, progress and text annotation sync | BookOrbit integration |
| [Stylus Annotations](https://github.com/kerivin/stylus-annotations.koplugin/releases) | Ink over EPUB/PDF pages | EPUB handwriting |
| [Ink Away](https://github.com/EmirErtorer/ink-away.koplugin) | Notebook/PDF drawing and export | Optional PDF workflow |

Neither handwriting plugin is required just to read. KOReader is available on Android and supported e-readers, not iOS.

## BookOrbit connection

From your own BookOrbit installation, configure the KOReader integration and download its personalized plugin package. Use a server address reachable by the reader, not `localhost`. Extract `bookorbit.koplugin` into KOReader's plugins folder and restart. Open a book, tap the top-center, choose the crossed-tools tab, then BookOrbit. Follow the [upstream setup guide](https://github.com/bookorbit/bookorbit/tree/main/koreader-plugin).

Personalized packages can contain login credentials: never put them in Git, a shared release, or an issue attachment. For a two-device test, download the same book through the integration, sync after reading, and compare the paragraph on the other device rather than page numbers.

## Kindle Fetch → automatic BookOrbit uploads

[Kindle Fetch](https://github.com/seshakiran/kindlefetch.koplugin) **0.9.0** searches Z-Library, downloads a selected book to the reader, and can then upload the completed local file automatically into a chosen BookOrbit library. The original stays on the reader. Install it separately using its [installation guide](https://github.com/seshakiran/kindlefetch.koplugin#install); this deployment kit does not bundle a personalized plugin or books.

On the reader, open **Kindle Fetch → Settings → BookOrbit uploads**. Sign in with the **BookOrbit website username and password**, choose a destination book library, and leave **Upload after download: On**. The server address is filled from the installed BookOrbit companion when available. Its sync username/key are separate credentials and do not authorize file uploads. **Send an existing book** handles files already on the reader.

### Tailscale settings confirmed on the original reader

The user confirmed a new download appeared automatically in BookOrbit on **October 20, 2026**, using a **Viwoods AiPaper Mini** with:

- Tailscale connected on the reader and server throughout the download/upload.
- Reader **Exit node: None**.
- Reader **Use Tailscale DNS: Off**, where available.
- Kindle Fetch **Encrypted DNS: On**.
- A signed-in BookOrbit upload account, selected library, and automatic uploads enabled.

Before this adjustment, Z-Library worked with Tailscale off while BookOrbit needed it on. After the adjustment, the user reported the complete flow working without toggling the VPN or manually sending the book. Keep KOReader included in Tailscale: excluding the application also excludes the BookOrbit client running inside it. The tested BookOrbit URL used a numeric tailnet address; if you use a hostname, verify resolution before disabling Tailscale DNS. See Tailscale's [exit nodes](https://tailscale.com/docs/features/exit-nodes), [DNS preferences](https://tailscale.com/docs/features/client/manage-preferences), and [Android split tunneling](https://tailscale.com/docs/features/client/android-app-split-tunneling).

This is the confirmed setup for the original installation, not a universal network requirement. The plugin does not control the VPN. If BookOrbit is unreachable, local downloads remain usable. Safe preflight failures retry up to three times; restore connectivity and choose **Retry waiting/failed uploads** afterward. Interrupted file uploads require checking the website before an explicit retry because the server may already have received them.

Sessions and the upload queue live in the reader's private `kindlefetch_bookorbit.json` settings file. Never publish it. Native upload sessions refresh without storing the password. The server's confirmed book ID marks a file as sent; asynchronous metadata work may still be running. See the plugin's [integration notes](https://github.com/seshakiran/kindlefetch.koplugin/blob/main/docs/BOOKORBIT_ROADMAP.md) and this stack's [validation status](VALIDATION.md).

## Android folder layout

Locate the existing KOReader data directory; on many Android installations it is `Internal Storage/koreader`. Storage permissions and installation paths vary. Use the directory that already holds your working plugins.

```text
koreader/
├── plugins/
│   ├── bookorbit.koplugin/main.lua
│   ├── kindlefetch.koplugin/main.lua
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
