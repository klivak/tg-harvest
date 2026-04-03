# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.7] - 2026-04-03

### Added

- **No media size limit option**: checkbox "No file size limit" in web UI and `--max-media-size 0` in CLI to download all media regardless of file size
- **Increased max slider to 2 GB**: media size slider now goes up to 2048 MB (was 200 MB) to match Telegram's file size limit

## [1.2.6] - 2026-03-30

### Added

- **Download All channels as ZIP**: unified download section after multi-channel parse results — one ZIP with per-channel folders, supports splitting each channel into N parts (TXT, JSON, CSV, XLSX)

### Fixed

- **Per-channel error handling in web UI**: parsing one channel no longer crashes the entire queue — errors are caught per-channel and shown individually, successfully parsed channels are preserved

## [1.2.5] - 2026-03-28

### Added

- **Download JSON from analytics page**: download messages JSON (with split-into-parts support) directly from the analytics page

### Fixed

- **Duplicate widget key crash**: `text_area` in message detail viewer now uses unique key per channel result

## [1.2.4] - 2026-03-25

### Fixed

- **Duplicate key crash on multi-channel results**: `StreamlitDuplicateElementKey` error when displaying results for multiple parsed channels — widget keys are now unique per channel

## [1.2.3] - 2026-03-25

### Added

- **No-channels warning banner**: parser page shows a prominent warning at the top when no channels are loaded, directing user to the Channels page first

## [1.2.2] - 2026-03-25

### Added

- **Persist channel selection**: selected channels in web UI multiselect are automatically saved to browser localStorage and restored on page reload

### Changed

- Added `streamlit-js-eval` dependency for browser localStorage access

## [1.2.1] - 2026-03-25

### Added

- **Channel search filter**: text input to quickly filter channels by name/username in the web UI multiselect

## [1.2.0] - 2026-03-25

### Added

- **Multi-channel queue parsing**: parse multiple channels sequentially in a single session
  - CLI: `tg-harvest parse @chan1 @chan2 @chan3` — channels are parsed one after another
  - Web UI: multi-select from loaded channels or enter multiple channels (one per line)
  - Queue progress display in both CLI (Rich) and Web UI (Streamlit status)
- **Per-channel output folders**: when parsing multiple channels, each channel's exports are saved to a separate subfolder (`output/{channel_name}/`)
- **Queue summary**: after queue completes, shows a summary table with success/fail status, message counts per channel
- **Error resilience**: if one channel in the queue fails, parsing continues with the next channel (CLI only)

## [1.1.2] - 2026-03-07

### Added

- **Ko-fi funding**: added `.github/FUNDING.yml` and Ko-fi badge/link in README (EN + UK)

## [1.1.1] - 2026-03-03

### Improved

- **README**: added Python, License, Release badges to both EN and UK sections
- **README**: removed SEO keyword spam block
- **README**: removed duplicated Installation/Configuration/Requirements sections (already covered in Quick Start)
- **GitHub**: added Issue templates (bug report, feature request) and PR template

## [1.1.0] - 2026-03-01

### Added

- **File splitting for large exports**: split downloads into 2-10 parts packed in a ZIP archive
  - Web UI: split selector in results section (no re-parsing needed to change split count)
  - CLI: `--split-parts N` option for `tg-harvest parse`
- **Exporter `file_suffix` support**: all exporters (JSON, CSV, XLSX, HTML) accept `file_suffix` parameter for part naming (`_part1of3`)
- **New module** `tg_harvest.exporters.splitter` with `split_messages()`, `make_part_suffix()`, `make_part_result()`
- Tests for splitter module and exporter file_suffix (625 total)

## [1.0.0] - 2026-03-01

### Added

- **6-month date preset** on parser page
- **Web UI workflow guide** in README (EN + UK) — step-by-step: Auth → Channels → Parse → Explore
- **FloodWait info block** on parser page and in README — warns about ~3000 msg throttle pauses

## [0.11.0] - 2026-03-01

### Added

- **Channel selector on parser page**: selectbox with previously loaded channels instead of manual ID/username input; fallback to text input with hint
- **Date preset buttons**: added Week, Month, This year presets; active preset now highlighted
- **Navigation guard**: modal dialog warns when navigating away from parser during active parsing to prevent data loss

### Changed

- **Parsing speed**: removed per-message rate limiter from `iter_messages` loops and set `wait_time=0` — Telethon handles flood protection via `flood_sleep_threshold`; ~100x faster for text-only parses
- **Channels default limit**: reduced default "Max dialogs to scan" from 100 to 25
- **TXT export**: removed blank lines between text blocks (`\n` instead of `\n\n`)

## [0.10.0] - 2026-03-01

### Added

- **Text-only mode**: checkbox in parser results to show only message text, with TXT and text-only CSV export
- **TXT export**: download parsed messages as plain text file

### Fixed

- **Blank web pages**: renamed `pages/` → `views/` to prevent Streamlit auto-discovery conflict with custom navigation
- **KeyError on channels page**: use stable internal keys for channel data instead of translated keys that break on language change or cache reuse
- **Streamlit widget conflict**: removed duplicate `value=` + `key=` on date/limit inputs
- **Media duration validation**: changed `MediaInfo.duration` from `int` to `float` to accept Telegram's fractional durations

### Changed

- **Deprecation fix**: replaced `use_container_width=True` with `width="stretch"` across all web views (Streamlit deprecation)
- **Parser results table**: limited to last 50 messages to avoid UI overload on large parses

## [0.9.1] - 2026-03-01

### Fixed

- **Security**: path traversal check in CLI `parse --output` and web parser (replaced broken
  string prefix matching with proper `..` component rejection)
- **Security**: media filename sanitization in `MediaDownloader` — strip directory components
  and null bytes from Telegram-provided filenames to prevent path traversal
- **Bug**: swallowed exceptions in file manager `_scan_files()` — replaced bare
  `except: pass` with specific exception types and debug logging

### Changed

- Refactored `_render_single()` in analytics page (254→120 lines) — extracted
  `_render_top_table()` and `_render_word_frequency()` helpers
- Extracted `_build_user_info()` / `_build_channel_info()` helpers in `channel_parser.py`
  to eliminate ~40 lines of duplicated entity construction code
- Reduced parameter count in web `_do_parse` (13→10) and `_parse_async` (15→12) by
  grouping extended options into `ParseOptions` object
- Replaced broad `except Exception` with specific exception types (`ValueError`,
  `KeyError`, `TypeError`, `json.JSONDecodeError`, `ImportError`) across web pages
- Extracted 6 magic numbers to `constants.py`: `MIN_WORD_LENGTH`, `TOP_WORDS_COUNT`,
  `TOP_REACTIONS_DISPLAY`, `DEFAULT_TRUNCATE_LENGTH`, `PREVIEW_TRUNCATE_LENGTH`,
  `DEFAULT_DIALOG_LIMIT`

## [0.9.0] - 2026-03-01

### Added

- **Media download** (`--download-media`): download photos, videos, documents, audio,
  voice messages during parsing via `client.download_media()`; files organized into
  `photos/`, `videos/`, `docs/`, `audio/`, `voice/` subdirectories
  - `--max-media-size` flag (default 50 MB) to skip large files
  - `--media-dir` flag to specify download directory
  - Resume support: existing files are skipped automatically
  - Download stats (files, bytes, skipped, failed) shown in CLI summary
- **Sender enrichment** (`--enrich-senders`): resolve `sender_id` to username,
  first/last name via Telegram API; results cached in `.users_cache.json` to avoid
  repeated API calls; batch fetching for efficiency
- **Reply thread analytics**: `thread_stats()` and `top_threads()` methods in
  `ChannelStats`; thread metrics (total threads, avg/max replies) displayed on
  Analytics page; `reply_to_top_id` now exported in all formats
- **Reply thread fetching** (`--fetch-replies`): optionally fetch full reply messages
  for thread-starting posts (extra API calls, opt-in)
- `SenderInfo` model with `display_name` computed field
- `DownloadStats` model for tracking download results
- `ParseOptions` dataclass for extended parsing behavior
- `MediaDownloader` class for file downloads with rate limiting
- `SenderEnricher` class for batch user resolution
- `UserCache` storage class (follows `StateManager` pattern)
- 5 new export fields: `reply_to_top_id`, `sender_username`, `sender_name`,
  `sender_is_bot`, `media_local_path`
- `MediaInfo.local_path` field for downloaded file paths
- Web UI: 3 new checkboxes in parser (Download media, Fetch replies, Enrich senders)
  with max media size slider
- Web Analytics: "Reply Threads" section with metrics and top threads table
- i18n: 12 new translation keys in both `en.json` and `uk.json`
- 55 new tests (603 total)

### Changed

- `ChannelParser.parse()` now accepts optional `ParseOptions` parameter
- `ALL_EXPORT_FIELDS` expanded from 21 to 26 fields
- `build_row()` extended with 5 new field extractions

## [0.8.0] - 2026-03-01

### Added

- **Bot & private chat support**: parse messages from Telegram bots (`@bot_username`)
  and 1-to-1 private chats, not just channels and groups
- `ChannelInfo.is_bot` field to distinguish bot conversations in listings and exports
- `types.User` entity handling in `ChannelParser.list_channels()` and
  `ChannelParser.get_channel_info()` — bots and users now appear alongside
  channels and groups
- Web UI — "Bot" and "Private Chat" type labels in Channels table (EN + UK)
- 5 new tests for bot/user entity parsing (548 total)
- Beginner-friendly README: step-by-step installation guide for non-programmers,
  with numbered steps (0–5), Python install instructions, and "no programming
  knowledge needed" note (both EN and UK sections)

### Changed

- `list_channels()` no longer filters out `types.User` entities — all dialog
  types are now returned (channels, supergroups, basic groups, bots, private chats)
- Web UI page headers updated: "Channels & Groups" → "Channels, Groups & Bots",
  "Parse Channel" → "Parse Messages" (both EN and UK locales)
- CLI `parse` command help updated to mention bots and private chats
- i18n: 4 new translation keys (`channels.type_bot`, `channels.type_user`)
  in both `en.json` and `uk.json`; several existing keys updated to use
  "dialogs" instead of "channels/groups"

## [0.7.0] - 2026-02-27

### Added

- **HTML exporter** (`--format html`): self-contained single-file HTML report with
  embedded CSS/JS, dark/light theme toggle, sortable/filterable messages table,
  emoji reaction badges, media type icons, clickable message URLs
- **CLI `tg-harvest export` command**: re-export already parsed JSON files to
  CSV, XLSX, or HTML without re-connecting to Telegram; supports single file
  or directory batch mode, field selection (`--fields`)
- **Web — File Manager page** (`📁 Files`): browse all parsed output files
  (JSON/CSV/XLSX/HTML), view file size/channel/message count, re-export JSON
  to other formats, delete files — all from the web UI
- **Message URL field**: `ParsedMessage.url` computed field generates a direct
  Telegram link (`https://t.me/{username}/{id}` for public channels,
  `https://t.me/c/{channel_id}/{id}` for private); appears in all exports
- **Poll answers**: `MediaInfo.poll_answers` captures poll answer options and
  voter counts from `MessageMediaPoll`
- **Geo coordinates**: `MediaInfo.latitude` / `MediaInfo.longitude` extracted
  from `MessageMediaGeo` and `MessageMediaGeoLive`
- **Contact details**: `MediaInfo.contact_name` / `MediaInfo.contact_phone`
  extracted from `MessageMediaContact`
- **Analytics — weekly/monthly aggregation**: toggle between Day / Week / Month
  view for the message activity chart
- **Analytics — engagement rate**: avg reactions/views ratio metric
- **Analytics — avg message length**: average text length metric
- **Analytics — top by forwards**: new table alongside top by views/reactions
- **Analytics — word frequency**: top-20 words bar chart
- 39 new tests (543 total)

### Changed

- `SUPPORTED_FORMATS` updated: `("json", "csv", "xlsx", "html", "all")`
- `ALL_EXPORT_FIELDS` now includes `"url"` field
- Parser page download section expanded from 3 to 4 buttons (+ HTML)
- Analytics summary expanded from 6 to 9 metrics (3+3+3 layout)
- i18n: ~35 new translation keys in both `en.json` and `uk.json`

## [0.6.1] - 2026-02-21

### Changed

- **Web — Parser page UX**: date range and message limit controls moved out of the
  "Advanced options" expander and are now always visible
- **Web — Parser page**: added quick-preset buttons — **Test (100)**, **Last year**,
  **Last 2 years**, **Last 3 years**, **All time** — that set date range and limit in
  one click; presets update date inputs and limit widget via session state
- **Web — Parser page**: disabled Parse button now shows an explanatory warning when
  no fields are selected; progress counter updates on every message when `limit=0`
- **Web — Search page**: filters (media type, views, date range, channel) moved out
  of collapsed expander and are always visible in a 3-column layout; Search button
  logic fixed — results show when query is typed OR button is clicked
- **Web — Channels page**: "Max dialogs" slider moved from sidebar to main content
  area, placed inline next to the Load button so it's discoverable
- **Web — Analytics page**: "Activity by Hour" chart now guarded against empty data;
  added CSV download button for the by-hour chart (consistent with per-day chart)
- **Web — App sidebar**: navigation radio label is now visible

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
