# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.6.0] - 2026-02-19

### Added

- **Web — Channels → Parse bridge**: Quick Actions block on Channels page — selectbox with
  all loaded channels + ⚡ Go to Parse button that auto-navigates and pre-fills the channel
  input; eliminates manual copy-paste of numeric IDs for private/restricted channels
- **Web — Sidebar status indicators**: always-visible auth status (✅/❌) and parsed file
  count (📄 N files) in sidebar — no need to navigate to Auth page to check session state
- **Web — Programmatic navigation**: `session_state["nav_page"]` support in `app.py` so
  any page can redirect to another page on next rerun
- **Web — Theming**: Telegram blue `#0088cc` primary color via `.streamlit/config.toml`
  and `--theme.*` subprocess args; `src/tg_harvest/web/theme.py` with `apply_custom_css()`
  (nav-style sidebar radio without circles, hover highlight, status badge styles) and
  `CHART_COLORS` / `CHART_LAYOUT` constants for consistent Plotly chart styling
- **Web — Navigation icons**: `🔑 Auth`, `📋 Channels`, `⚡ Parse`, `🔍 Search`,
  `📊 Analytics` in sidebar nav labels (both EN and UK)
- **Web — Toast notifications**: `st.toast()` after successful parse and channel load
- **Web — Cache control**: automatic invalidation of Search/Analytics caches after a
  successful parse; manual 🔄 refresh buttons on Search and Analytics pages
- **Web — Parser `st.status()`**: replaces `st.progress()` + `st.empty()` — shows
  step-by-step status (Connecting → Parsing → complete/error) with collapsible container
- **Web — Parser reorganized layout**: quick options (format, incremental, limit) on one
  row; Advanced expander for date range, output dir, field selection; Parse button
  full-width (`use_container_width=True`)
- **Web — Message detail viewer**: expander below results table with selectbox to view
  full text and media JSON for any parsed message
- **Web — Analytics tabs**: Single Channel | Compare Channels tabs at top of Analytics page
- **Web — Channel comparison**: multiselect (2–5 datasets), metrics comparison table,
  overlay grouped bar charts for messages-per-day and activity-by-hour
- **Web — Chart data export**: Download chart data CSV button under messages-per-day chart
- **Web — Private channel column**: 🔐 indicator column in Channels table for channels
  without a public username; 🔒 emoji for restricted channels
- `src/tg_harvest/web/helpers.py`: shared `truncate(text, limit)` utility (was duplicated
  in parser.py, search.py, analytics.py)
- `tests/test_web/test_helpers.py`: unit tests for `truncate()`
- `tests/test_web/test_i18n.py`: locale consistency tests (EN/UK key parity, no empty values)

### Changed

- **Web — i18n**: ~25 new translation keys added to both `en.json` and `uk.json`; text
  truncation in results tables increased from 100 to 200 characters
- **Web — Plotly charts**: all 5 charts in Analytics now use Telegram-inspired color palette
  and transparent background instead of default Plotly theme
- Tests: 504 total (+15 new web tests)

## [0.5.0] - 2026-02-18

### Added

- **Internationalization (i18n)**: language switcher in sidebar (English / Українська)
  - All UI strings translated — pages, tips, error messages, column names, chart labels
  - Locale files: `src/tg_harvest/web/locales/en.json`, `uk.json` (131 keys each)
  - `src/tg_harvest/web/i18n.py` — `t(key, **kwargs)` helper with EN fallback
- **Help guides** on every web page (collapsible expanders):
  - Auth: step-by-step instructions to get API ID/Hash from my.telegram.org, create `.env`, log in, access private/restricted channels
  - Channels: tips on finding private channel IDs, restricted flag meaning
  - Parse: channel format examples, options explained, private channel notes
  - Search: filter usage, empty-query browse mode
  - Analytics: metric explanations, UTC note, incremental tracking tip

### Changed

- **Web — Parse page**: fixed broken progress bar (`min(count % 100, 99)` loop);
  now shows real 0–100% when limit is set, or a message counter when limit = 0
- **Web — Parse page**: categorized error messages (flood wait, auth, channel not
  found, network) instead of a generic `st.error(f"Parse error: {e}")`
- **Web — Channels page**: added `@st.cache_data(ttl=300)` — no refetch on rerun
- **Web — Search page**: added `@st.cache_data(ttl=60)` on result loading;
  configurable result limit via sidebar slider (50–500, default 200);
  fixed channel dedup bug (now deduplicates by channel ID, not title)
- **Web — Analytics page**: added `@st.cache_data(ttl=60)`; fixed metric layout
  from 4+2 split to clean 3+3 grid
- **Web — All pages**: consistent text truncation at 100 chars; `column_config`
  with proper types on all dataframes
- **Config**: API credentials (`TG_API_ID`, `TG_API_HASH`, `TG_PHONE`) are now
  optional in `Settings` (default `None`); empty strings converted to `None`
- **Client**: `TelegramSession` now raises `ValueError` with a clear message if
  credentials are missing, instead of a cryptic Telethon error
- **Web — Auth page**: shows actionable warning when credentials are missing
  instead of crashing; `None`-safe config display

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
