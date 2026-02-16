# Telegram API Parser

Parser for Telegram channels and chats via MTProto API. Extracts messages, media metadata, reactions, views, forwards from any channel you have access to — including restricted channels where copying is disabled.

## Features

- **Full API access** — works at MTProto level, bypasses UI restrictions (copy-disabled channels)
- **Rich data extraction** — messages, media, reactions, views, forwards, replies, entities
- **Flexible filtering** — by date range, message limit
- **Multiple export formats** — JSON, CSV, or both
- **Beautiful CLI** — progress bars, colored output, summary tables
- **Rate limiting** — respects Telegram API limits, auto-handles FloodWait errors
- **Async architecture** — efficient parsing of large channels

## Requirements

- Python 3.11+
- Telegram API credentials (get from [my.telegram.org/apps](https://my.telegram.org/apps))

## Installation

```bash
git clone <repo-url>
cd telegram-api-parser

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Install
pip install -e .
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
tg-parser auth login

# Check auth status
tg-parser auth status

# Log out
tg-parser auth logout
```

### List Channels

```bash
# Show all accessible channels and groups
tg-parser channels list

# Limit number of dialogs to scan
tg-parser channels list -l 200
```

### Parse Messages

```bash
# Parse all messages from a channel
tg-parser parse @channel_name

# Parse with date range
tg-parser parse @channel -f 2024-01-01 -t 2024-12-31

# Limit number of messages
tg-parser parse @channel --limit 5000

# Export to CSV
tg-parser parse @channel --format csv

# Export to both JSON and CSV
tg-parser parse @channel --format both

# Custom output directory
tg-parser parse @channel -o ./my_data

# Parse by numeric ID (for private channels)
tg-parser parse -1001234567890

# Verbose mode (debug logging)
tg-parser -v parse @channel
```

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
src/tg_parser/
  config/       Settings, constants
  models/       Pydantic data models
  client/       Telegram session, rate limiter
  parsers/      Message/media/channel parsing
  exporters/    JSON, CSV export
  cli/          Click CLI commands
  utils/        Logging, date helpers
```

## Optional Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `TG_SESSION_NAME` | `tg_parser` | Session file name |
| `TG_FLOOD_SLEEP_THRESHOLD` | `60` | Auto-sleep for FloodWait errors (seconds) |
| `TG_REQUEST_DELAY` | `1.0` | Delay between API requests (seconds) |
| `TG_OUTPUT_DIR` | `./output` | Default output directory |

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check src/
```

## License

MIT
