# Upstream projects & attribution

This repository supplies deployment helpers and documentation. It downloads application code or container images from the upstream projects below. Their code and assets retain their own licenses; this repository's MIT license does not relicense them.

| Project | Role |
|---|---|
| [BookOrbit](https://github.com/bookorbit/bookorbit) | Ebook library, reader, KOReader integration |
| [Audiobookshelf](https://github.com/advplyr/audiobookshelf) | Audiobook library and playback server |
| [BookBridge](https://github.com/cporcellijr/bookbridge) | Reading/audio integrations |
| [KOReader](https://github.com/koreader/koreader) | Reader application |
| [Stylus Annotations](https://github.com/kerivin/stylus-annotations.koplugin) | Optional EPUB/PDF ink plugin |
| [Ink Away](https://github.com/EmirErtorer/ink-away.koplugin) | Optional PDF/notebook plugin |
| [PostgreSQL](https://www.postgresql.org/) / [pgvector](https://github.com/pgvector/pgvector) | Database and vector extension |
| [Caddy](https://github.com/caddyserver/caddy) | Linux HTTPS proxy |
| [MLX Audio](https://github.com/Blaizzy/mlx-audio) | Candidate for planned native TTS, not installed |

Native app revisions are recorded in `native/versions.json`. Python dependencies are in `native/requirements.lock.txt`; dependencies retain their respective licenses. Container image tags are configurable in the generated Linux `.env`.

Download plugins from their upstream maintainers. Check the applicable licenses before forking or redistributing them. No proprietary fonts, book covers, books, commercial recordings, or screenshots of a personal library are shipped here. Product names are used to identify integrations and do not imply endorsement.
