# CLAUDE.md

## Project Overview

TG Harvest — Telegram channel/chat data harvester via MTProto API (Telethon). Extracts messages, media metadata, reactions, views, forwards from any channel the user has access to — including restricted ones. Includes Streamlit web UI, search, incremental parsing, and analytics.

## Tech Stack

- Python 3.11+, Telethon (MTProto), Pydantic v2, Click, Rich, aiofiles
- Streamlit + Plotly for web UI
- Package: `src/tg_harvest/` (src layout)
- CLI entry: `tg-harvest` (defined in pyproject.toml `[project.scripts]`)
- Web entry: `tg-harvest web` or `tg-harvest-web`

## Architecture

- **config/** — Settings from `.env` via pydantic-settings, constants
- **models/** — Pure Pydantic models (no Telethon imports): ParsedMessage, ChannelInfo, MediaInfo, ReactionsInfo, ParseResult
- **client/** — TelegramSession (Telethon wrapper), RateLimiter
- **parsers/** — Converts raw Telethon objects to Pydantic models: ChannelParser, MessageParser, MediaParser
- **exporters/** — BaseExporter ABC (with field selection), JsonExporter, CsvExporter, XlsxExporter
- **storage/** — StateManager for incremental parsing state (parse_state.json)
- **search/** — SearchEngine for full-text search across parsed JSON files
- **analytics/** — ChannelStats for statistics and chart data
- **cli/** — Click command groups: auth, channels, parse, search, web
- **web/** — Streamlit app with pages: auth, channels, parser, search, analytics
- **utils/** — Logging (Rich), date parsing

## Key Rules

- Only `client/` and `parsers/` may import Telethon
- All data flows through Pydantic models between layers
- Async throughout (Telethon requires it); Click commands use `asyncio.run()`
- Environment variables prefixed with `TG_` (TG_API_ID, TG_API_HASH, TG_PHONE)
- Web UI runs on port 8777 by default (configurable via TG_WEB_PORT)
- **README is bilingual (EN + UK in one file)**: whenever README.md is updated, both the English and Ukrainian sections must be updated together — never update one without the other

## Commands

```bash
pip install -e .              # Install in dev mode
tg-harvest auth login         # Authenticate
tg-harvest channels list      # List channels
tg-harvest parse @channel     # Parse channel
tg-harvest parse @channel -i  # Incremental parse
tg-harvest search "keyword"   # Search parsed data
tg-harvest web                # Start web UI (port 8777)
```

## Testing

```bash
pip install -e ".[dev]"
pytest -v
ruff check src/ tests/
ruff format src/ tests/
```

## CI

GitHub Actions workflow at `.github/workflows/ci.yml` runs lint + test on push/PR to main.
