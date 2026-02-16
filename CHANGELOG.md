# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
