# CLAUDE.md

## Project Overview

Telegram channel/chat parser via MTProto API (Telethon). Extracts messages, media metadata, reactions, views, forwards from any channel the user has access to — including restricted ones.

## Tech Stack

- Python 3.11+, Telethon (MTProto), Pydantic v2, Click, Rich, aiofiles
- Package: `src/tg_parser/` (src layout)
- CLI entry: `tg-parser` (defined in pyproject.toml `[project.scripts]`)

## Architecture

- **config/** — Settings from `.env` via pydantic-settings, constants
- **models/** — Pure Pydantic models (no Telethon imports): ParsedMessage, ChannelInfo, MediaInfo, ReactionsInfo, ParseResult
- **client/** — TelegramSession (Telethon wrapper), RateLimiter
- **parsers/** — Converts raw Telethon objects to Pydantic models: ChannelParser, MessageParser, MediaParser
- **exporters/** — BaseExporter ABC, JsonExporter, CsvExporter
- **cli/** — Click command groups: auth, channels, parse
- **utils/** — Logging (Rich), date parsing

## Key Rules

- Only `client/` and `parsers/` may import Telethon
- All data flows through Pydantic models between layers
- Async throughout (Telethon requires it); Click commands use `asyncio.run()`
- Environment variables prefixed with `TG_` (TG_API_ID, TG_API_HASH, TG_PHONE)

## Commands

```bash
pip install -e .              # Install in dev mode
tg-parser auth login          # Authenticate
tg-parser channels list       # List channels
tg-parser parse @channel      # Parse channel
```

## Testing

```bash
pip install -e ".[dev]"
pytest
```
