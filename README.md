# TG Harvest

[![CI](https://github.com/klivak/telegram-api-parser/actions/workflows/ci.yml/badge.svg)](https://github.com/klivak/telegram-api-parser/actions/workflows/ci.yml)

Telegram channel/chat data harvester via MTProto API. Extracts messages, media metadata, reactions, views, forwards from any channel you have access to — including restricted channels where copying is disabled.

## Features

- **Full API access** — works at MTProto level, bypasses UI restrictions (copy-disabled channels)
- **Rich data extraction** — messages, media, reactions, views, forwards, replies, entities
- **Web UI** — Streamlit-based interface with parsing, search, and analytics
- **Message search** — full-text search across parsed data with filters
- **Incremental parsing** — only fetch new messages since last parse
- **Analytics** — message activity charts, top posts, reaction breakdown
- **Flexible filtering** — by date range, message limit
- **Multiple export formats** — JSON, CSV, Excel (.xlsx), or all at once
- **Field selection** — choose which columns to export (id, text, date, views, etc.)
- **Beautiful CLI** — progress bars, colored output, summary tables
- **Rate limiting** — respects Telegram API limits, auto-handles FloodWait errors
- **CI/CD** — GitHub Actions, ruff linting, pre-commit hooks

## Requirements

- Python 3.11+
- Telegram API credentials (get from [my.telegram.org/apps](https://my.telegram.org/apps))

## Installation

```bash
git clone https://github.com/klivak/telegram-api-parser.git
cd telegram-api-parser

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Install
pip install -e .

# Install dev dependencies (for testing/linting)
pip install -e ".[dev]"
```

## Configuration

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

```env
TG_API_ID=12345678
TG_API_HASH=your_api_hash_here
TG_PHONE=+380123456789
```

### Getting API Credentials

1. Go to [my.telegram.org/apps](https://my.telegram.org/apps)
2. Log in with your phone number
3. Create a new application
4. Copy `api_id` and `api_hash`

## Usage

### Authentication

```bash
# Log in (interactive: phone code + optional 2FA)
tg-harvest auth login

# Check auth status
tg-harvest auth status

# Log out
tg-harvest auth logout
```

### List Channels

```bash
# Show all accessible channels and groups
tg-harvest channels list

# Limit number of dialogs to scan
tg-harvest channels list -l 200
```

### Parse Messages

```bash
# Parse all messages from a channel
tg-harvest parse @channel_name

# Parse with date range
tg-harvest parse @channel -f 2024-01-01 -t 2024-12-31

# Limit number of messages
tg-harvest parse @channel --limit 5000

# Export to CSV
tg-harvest parse @channel --format csv

# Export to Excel (.xlsx) with formatting
tg-harvest parse @channel --format xlsx

# Export to all formats (JSON + CSV + XLSX)
tg-harvest parse @channel --format all

# Export only selected fields
tg-harvest parse @channel --fields id,text,date,views

# Export specific fields to Excel
tg-harvest parse @channel --format xlsx --fields text,date,views,reactions_total

# Custom output directory
tg-harvest parse @channel -o ./my_data

# Parse by numeric ID (for private channels)
tg-harvest parse -1001234567890

# Incremental mode (only new messages since last parse)
tg-harvest parse @channel -i

# Verbose mode (debug logging)
tg-harvest -v parse @channel
```

### Search Messages

```bash
# Search across all parsed data
tg-harvest search "keyword"

# Filter by media type
tg-harvest search "photo" --media-type photo

# Filter by minimum views
tg-harvest search "news" --min-views 1000

# Only messages with reactions
tg-harvest search "announcement" --has-reactions

# Date range filter
tg-harvest search "update" --from-date 2024-01-01 --to-date 2024-06-30

# Limit results
tg-harvest search "crypto" -n 100
```

### Web UI

```bash
# Start Streamlit web interface (port 8777)
tg-harvest web

# Custom port
tg-harvest web -p 9000
```

The web UI provides:
- **Auth Status** — check authentication, view config
- **Channels** — browse accessible channels with filtering
- **Parse** — parse channels with date pickers, progress bar, results table, download buttons
- **Search** — full-text search with filters (media type, views, reactions, date range)
- **Analytics** — interactive charts: messages per day, hourly activity, top posts by views/reactions, media distribution, reaction breakdown

## Output Format

### JSON

Full structured data with all fields:

```json
{
  "channel": {
    "id": 1234567890,
    "title": "Channel Name",
    "username": "channel_name",
    "members_count": 15000
  },
  "messages": [
    {
      "id": 1,
      "date": "2024-01-15T12:00:00+00:00",
      "text": "Message text",
      "views": 5432,
      "forwards": 12,
      "reactions": {
        "total": 150,
        "reactions": [
          {"emoji": "\ud83d\udc4d", "count": 100},
          {"emoji": "\u2764\ufe0f", "count": 50}
        ]
      }
    }
  ],
  "total_messages": 1,
  "parsed_at": "2024-06-01T10:00:00+00:00"
}
```

### CSV

Flattened table format with key fields, opens in Excel/Google Sheets.

## Project Structure

```
src/tg_harvest/
  config/       Settings, constants
  models/       Pydantic data models
  client/       Telegram session, rate limiter
  parsers/      Message/media/channel parsing
  exporters/    JSON, CSV, Excel export (with field selection)
  storage/      Incremental parsing state
  search/       Search engine
  analytics/    Statistics and analytics
  cli/          Click CLI commands
  web/          Streamlit web UI
  utils/        Logging, date helpers
```

## Optional Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `TG_SESSION_NAME` | `tg_harvest` | Session file name |
| `TG_FLOOD_SLEEP_THRESHOLD` | `60` | Auto-sleep for FloodWait errors (seconds) |
| `TG_REQUEST_DELAY` | `1.0` | Delay between API requests (seconds) |
| `TG_OUTPUT_DIR` | `./output` | Default output directory |
| `TG_WEB_PORT` | `8777` | Streamlit web UI port |

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest -v

# Lint
ruff check src/ tests/

# Format
ruff format src/ tests/

# Setup pre-commit hooks
pre-commit install
```

## License

MIT
