# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2026-02-16

### Changed

- **Renamed project** from `tg-parser` to `tg-harvest`
- Package renamed: `tg_parser` -> `tg_harvest`
- CLI command renamed: `tg-parser` -> `tg-harvest`
- Web entry renamed: `tg-parser-web` -> `tg-harvest-web`
- Added MIT LICENSE file
- Added 138 integration tests (302 total): project structure, import isolation,
  CI config, export pipeline consistency, CLI structure verification

## [0.3.0] - 2026-02-16

### Added

- **Excel export** (`--format xlsx`) with openpyxl:
  - Colored headers (dark blue with white text)
  - Auto-width columns
  - Frozen header row
  - Autofilter
  - Separate "Channel Info" sheet
- **Field selection** for all export formats (JSON, CSV, XLSX):
  - CLI: `--fields id,text,date,views` to export only selected columns
  - Web UI: field selection checkboxes in parser page
  - 20 available fields: id, date, text, sender_id, post_author, views, forwards, etc.
- Export format `all` — exports to JSON + CSV + XLSX at once (replaces `both`)
- Shared `build_row()` utility for consistent row building across exporters

### Changed

- `BaseExporter` now accepts optional `fields` parameter for field filtering
- `SUPPORTED_FORMATS` updated: `("json", "csv", "xlsx", "all")`
- CSV exporter refactored to use shared `build_row()` from base
- JSON exporter supports flat field-filtered output when fields are selected

## [0.2.0] - 2026-02-16

### Added

- **Streamlit Web UI** (`tg-harvest web`) on port 8777:
  - Auth status page with config viewer
  - Channels browser with search filter
  - Parse page with date pickers, progress bar, results table, download buttons
  - Search page with full-text search and filters
  - Analytics page with interactive Plotly charts
- **Message search** (`tg-harvest search`) across parsed JSON files:
  - Text keyword search
  - Filters: media type, min views, has reactions, date range, channel
- **Incremental parsing** (`tg-harvest parse -i`):
  - Tracks last parsed message ID per channel
  - Only fetches new messages since last parse
- **Analytics** module:
  - Messages per day / activity by hour
  - Top posts by views and reactions
  - Media type distribution
  - Reactions breakdown
  - Summary statistics (avg views, avg reactions, forwarded, edited counts)
- **CI/CD**: GitHub Actions workflow (lint + test on push/PR)
- **Code quality**: pre-commit config with ruff check/format, trailing whitespace, EOF fixer
- **Ruff format** configuration in pyproject.toml

### Changed

- ChannelParser.parse() now accepts `min_id` parameter for incremental parsing
- Updated dependencies: added streamlit, plotly, pre-commit

## [0.1.0] - 2026-02-16

### Added

- Initial release
- Telegram authentication (login, logout, status)
- Channel/group listing with Rich table output
- Message parsing with full metadata extraction:
  - Text, sender, post author
  - Views, forwards, replies count
  - Reactions (emoji and custom emoji)
  - Media metadata (photo, video, document, audio, voice, sticker, GIF, poll, geo, contact, web page)
  - Forward info (source channel/user)
  - Reply info (reply-to message ID)
  - Message entities (links, mentions, formatting)
  - Edit status and date
  - Pinned status
  - Album grouping (grouped_id)
- Date range filtering (--from-date, --to-date)
- Message limit option
- JSON export (full structured data)
- CSV export (flattened table format)
- Async architecture with Telethon
- Rate limiting (configurable delay + FloodWait auto-handling)
- Rich CLI output (progress bars, summary panels, colored tables)
- Environment-based configuration via .env file
- Support for restricted channels (copy-disabled)
