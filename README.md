# TG Harvest

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/klivak)

[![CI](https://github.com/klivak/tg-harvest/actions/workflows/ci.yml/badge.svg)](https://github.com/klivak/tg-harvest/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GitHub release](https://img.shields.io/github/v/release/klivak/tg-harvest)](https://github.com/klivak/tg-harvest/releases)

Telegram data harvester via MTProto API. Extracts messages, media metadata, reactions, views, forwards from any channel, group, bot, or private chat you have access to — including restricted channels where copying is disabled.

### What is TG Harvest?

TG Harvest is an open-source Python tool for **downloading and exporting Telegram channel data**. It connects directly to Telegram's MTProto API (the same protocol used by the official app), giving you access to data that web scrapers and bots cannot reach — including channels with copy restrictions, private groups, and bot conversations.

Unlike Telegram's built-in export (which only works for personal chats), TG Harvest can **export any channel or group you're a member of** — with full message text, reactions, view counts, forwards, media metadata, and more.

### Who is this for?

- **Marketers & SMM managers** — export channel posts for content analysis, track engagement metrics, compare competitor channels
- **Researchers & data journalists** — collect Telegram data for analysis, monitor public discourse, archive news channels
- **OSINT analysts** — extract data from public and private channels for investigations
- **Community managers** — backup group conversations, analyze member activity, track discussion trends
- **Developers & data scientists** — structured JSON/CSV export for building datasets, training models, or feeding into analytics pipelines
- **Anyone who needs a Telegram backup** — export your own channels, groups, or bot conversations to JSON, CSV, Excel, or HTML

### Key capabilities

- Export Telegram channels, groups, bots, and private chats to **JSON, CSV, Excel (.xlsx), or HTML**
- Access **restricted channels** where Telegram disables copying — TG Harvest works at the protocol level
- **Multi-channel queue** — parse multiple channels in one session, each saved to a separate folder
- **Incremental parsing** — only fetch new messages since the last run (no duplicates)
- **Web UI** with interactive charts, search, and analytics — no coding required
- **CLI** for automation and scripting

## Quick Start

> **No programming knowledge needed!** Follow these steps one by one. You only need to type the commands into your terminal (Command Prompt on Windows, Terminal on Mac/Linux).

### Step 0 — Install Python

You need Python 3.11 or newer. Check if you have it:

```bash
python --version
```

If this shows `Python 3.11` or higher, you're good. If not, download Python from [python.org/downloads](https://www.python.org/downloads/) and install it. **On Windows, check "Add Python to PATH" during installation.**

### Step 1 — Download and install TG Harvest

Open a terminal and run these commands one by one:

```bash
git clone https://github.com/klivak/tg-harvest.git
cd tg-harvest
python -m venv .venv
```

Activate the virtual environment:
- **Windows:** `.venv\Scripts\activate`
- **Mac/Linux:** `source .venv/bin/activate`

Then install:

```bash
pip install -e .
```

### Step 2 — Get Telegram API keys

1. Go to [my.telegram.org/apps](https://my.telegram.org/apps) in your browser
2. Log in with your phone number (the one linked to your Telegram account)
3. Click **API development tools**
4. Fill in any app title (e.g. `tg-harvest`) and short name (e.g. `harvest`)
5. You'll see **App api_id** (a number) and **App api_hash** (a long string) — copy them

### Step 3 — Configure

```bash
cp .env.example .env
```

Open the `.env` file in any text editor and fill in your values:

```env
TG_API_ID=12345678
TG_API_HASH=your_api_hash_here
TG_PHONE=+380123456789
```

### Step 4 — Log in to Telegram

```bash
tg-harvest auth login
```

Telegram will send a code to your Telegram app. Enter it when prompted. If you have 2FA enabled, enter your password too. **This only needs to be done once** — the session is saved locally.

### Step 5 — Start using!

```bash
# Web UI — recommended (all features in one place)
tg-harvest web                # opens at http://localhost:8777

# Or use the CLI directly
tg-harvest channels list      # list your channels, groups, bots
tg-harvest parse @channel     # parse a public channel
tg-harvest parse @some_bot    # parse a bot conversation
tg-harvest parse -1001234567890  # parse a private channel by numeric ID
tg-harvest search "keyword"   # search parsed data
```

> **Note:** `tg-harvest auth login` must be run once in the terminal — it requires entering a confirmation code sent to your Telegram app. After that, the session is saved and the web UI works without any further terminal interaction.

---

## Features

- **Full MTProto access** — works at the protocol level, bypasses UI restrictions (copy-disabled channels)
- **Channels, groups, bots & private chats** — parse any dialog you have access to, including bot conversations and 1-to-1 chats
- **Private & restricted channels** — parse even channels with copy restrictions disabled
- **Rich data extraction** — messages, media, reactions, views, forwards, replies, entities
- **Web UI** — Streamlit interface with EN/UK language switcher, per-page help guides, parsing, search, and analytics
- **Message search** — full-text search across parsed data with filters
- **Incremental parsing** — only fetch new messages since last parse
- **Analytics** — message activity charts, top posts, reaction breakdown
- **Multi-channel queue** — parse multiple channels in one session (`tg-harvest parse @ch1 @ch2 @ch3`), each saved to a separate date-stamped folder
- **Flexible filtering** — by date range, message limit
- **Multiple export formats** — JSON, CSV, Excel (.xlsx), HTML report, or all at once
- **File splitting** — split large exports into multiple parts (2–20 files)
- **HTML report** — self-contained single-file HTML with dark/light theme, sortable table, clickable message URLs
- **Re-export** — convert already parsed JSON to CSV/XLSX/HTML without re-connecting to Telegram (`tg-harvest export`)
- **File Manager** — browse, delete, and re-export parsed files from the web UI
- **Field selection** — choose which columns to export (id, text, date, views, url, etc.)
- **Direct message links** — each message includes a Telegram URL for quick navigation
- **Beautiful CLI** — progress bars, colored output, summary tables
- **Rate limiting** — respects Telegram API limits, auto-handles FloodWait errors
- **CI/CD** — GitHub Actions, ruff linting, pre-commit hooks

---

## Private & Restricted Channels

TG Harvest can extract data from channels and groups where Telegram's UI disables copying. This works because the app communicates directly via the **MTProto protocol** — the same protocol used by the official Telegram app. Copy restrictions only affect the UI, not the underlying API.

**Requirements:**
- Your Telegram account must be a **member** of the channel or group
- You must be authenticated via `tg-harvest auth login`

**How to access a private channel:**
1. Run `tg-harvest channels list` or open the **Channels** page in the web UI
2. Find the channel — private channels show no username, only a numeric ID
3. Copy the numeric ID (e.g. `-1001234567890`)
4. Use it to parse: `tg-harvest parse -1001234567890`

**What TG Harvest can extract from restricted channels:**
- Full message text
- Media metadata (file names, types, sizes — not the files themselves)
- Reactions, views, forwards
- Post author, sender info
- Edit history, pinned status

**What it cannot do:**
- Access channels you are not a member of
- Retrieve deleted messages
- Download self-destructing messages

---

## Usage

> For installation and configuration, see [Quick Start](#quick-start) above.

### Authentication

```bash
# Log in (interactive: phone code + optional 2FA)
tg-harvest auth login

# Check auth status
tg-harvest auth status

# Log out
tg-harvest auth logout
```

### List Channels, Groups & Bots

```bash
# Show all accessible channels, groups, bots, and private chats
tg-harvest channels list

# Limit number of dialogs to scan
tg-harvest channels list -l 200
```

### Parse Messages

```bash
# Parse public channel by username
tg-harvest parse @channel_name

# Parse a bot conversation
tg-harvest parse @bot_username

# Parse private channel by numeric ID
tg-harvest parse -1001234567890

# Parse with date range
tg-harvest parse @channel -f 2024-01-01 -t 2024-12-31

# Limit number of messages
tg-harvest parse @channel --limit 5000

# Incremental mode — only new messages since last parse
tg-harvest parse @channel -i

# Export to CSV
tg-harvest parse @channel --format csv

# Export to Excel (.xlsx)
tg-harvest parse @channel --format xlsx

# Export to HTML report
tg-harvest parse @channel --format html

# Export to all formats at once (JSON + CSV + XLSX + HTML)
tg-harvest parse @channel --format all

# Export only selected fields
tg-harvest parse @channel --fields id,text,date,views

# Custom output directory
tg-harvest parse @channel -o ./my_data

# Download media files (photos, videos, documents)
tg-harvest parse @channel --download-media

# Download media with size limit (MB)
tg-harvest parse @channel --download-media --max-media-size 100

# Resolve sender IDs to usernames and names
tg-harvest parse @channel --enrich-senders

# Fetch full reply threads (extra API calls)
tg-harvest parse @channel --fetch-replies

# Multi-channel queue — parse several channels in one session
tg-harvest parse @channel1 @channel2 @channel3

# Multi-channel with options
tg-harvest parse @news @politics @tech --format all --limit 1000

# Split output into parts (useful for large exports)
tg-harvest parse @channel --split-parts 5

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

### Re-export

```bash
# Re-export parsed JSON to CSV (no Telegram connection needed)
tg-harvest export output/channel_20240615.json --format csv

# Re-export to HTML report
tg-harvest export output/channel_20240615.json --format html

# Re-export all JSON files in a directory
tg-harvest export output/ --format all

# With field selection
tg-harvest export output/ --format xlsx --fields id,text,date,views,url
```

### Web UI

```bash
# Start Streamlit web interface (port 8777)
tg-harvest web

# Custom port
tg-harvest web -p 9000
```

The web UI provides:
- **Auth Status** — step-by-step guide to get API credentials, check session, view config
- **Channels** — browse all accessible channels, groups, bots, and private chats; shows types and numeric IDs for copying
- **Parse** — parse any dialog by username or numeric ID, date pickers, incremental mode, progress bar, download buttons
- **Search** — full-text search with filters (media type, views, reactions, date range, channel)
- **Analytics** — interactive charts: messages per day/week/month, hourly activity, top posts by views/reactions/forwards, media distribution, reaction breakdown, engagement rate, word frequency
- **Files** — file manager to browse, delete, and re-export parsed output files
- **Language switcher** — English / Українська (sidebar)

Each page has a collapsible **Tips / Підказки** section with usage hints.

#### Web UI step-by-step workflow

1. **Auth Status** — verify your Telegram session is active (green indicator in sidebar)
2. **Channels** — click "Load channels" to fetch your dialogs list
3. **Parse** — select a channel from the dropdown (loaded from step 2), choose date range/limit preset, click "Parse"
4. **Search / Analytics / Files** — explore parsed data

> **Note:** Telegram may temporarily throttle requests (FloodWait) approximately every 3000 messages. This is normal — the parser will automatically pause for 30–60 seconds and then continue. Do not close the page during the pause.

---

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
          {"emoji": "👍", "count": 100},
          {"emoji": "❤️", "count": 50}
        ]
      }
    }
  ],
  "total_messages": 1,
  "parsed_at": "2024-06-01T10:00:00+00:00"
}
```

### CSV / Excel

Flattened table format. Opens directly in Excel or Google Sheets.

---

## Project Structure

```
src/tg_harvest/
  config/       Settings, constants
  models/       Pydantic data models
  client/       Telegram session, rate limiter
  parsers/      Message/media/channel parsing
  exporters/    JSON, CSV, Excel, HTML export (with field selection)
  storage/      Incremental parsing state
  search/       Search engine
  analytics/    Statistics and analytics
  cli/          Click CLI commands
  web/          Streamlit web UI
    locales/    Translation files (en.json, uk.json)
  utils/        Logging, date helpers
```

---

## Optional Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `TG_SESSION_NAME` | `tg_harvest` | Session file name |
| `TG_FLOOD_SLEEP_THRESHOLD` | `60` | Auto-sleep for FloodWait errors (seconds) |
| `TG_REQUEST_DELAY` | `1.0` | Delay between API requests (seconds) |
| `TG_OUTPUT_DIR` | `./output` | Default output directory |
| `TG_WEB_PORT` | `8777` | Streamlit web UI port |

---

## Security

### Credential storage
- API keys (`TG_API_ID`, `TG_API_HASH`, `TG_PHONE`) are loaded from `.env` which is **gitignored** — never committed
- Telegram session files (`sessions/*.session`) are **gitignored** — contain auth tokens, protect with filesystem permissions (`chmod 600 sessions/`) on shared systems
- Parsed data (`output/`) is **gitignored**
- Phone numbers are masked in all UI output (`+380***4567`)
- 2FA password input uses `getpass` — not echoed to terminal

### Input handling
- Search queries are regex-escaped before use (`re.escape`)
- Output directory is validated against `..` path traversal
- All data models validated through Pydantic v2 before use

### Web UI
- Message text is displayed via `st.dataframe()` — not rendered as markdown (no XSS)
- Translation strings are static files — never user-controlled
- **Not designed for public internet exposure** — run locally or behind a reverse proxy with authentication if exposed

### Responsible use
TG Harvest accesses only data you can already see as a Telegram member. It does not bypass access controls — only UI copy restrictions. Respect Telegram's Terms of Service and applicable laws when collecting data.

---

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

---

## License

MIT

---
---

# TG Harvest (Українська)

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/klivak)

[![CI](https://github.com/klivak/tg-harvest/actions/workflows/ci.yml/badge.svg)](https://github.com/klivak/tg-harvest/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GitHub release](https://img.shields.io/github/v/release/klivak/tg-harvest)](https://github.com/klivak/tg-harvest/releases)

Інструмент для збору даних з Telegram — каналів, груп, ботів і приватних чатів через MTProto API.

Витягує повідомлення, метадані медіа, реакції, перегляди, репости з будь-якого діалогу, до якого ви маєте доступ — включно з каналами з вимкненим копіюванням.

## Швидкий старт

> **Не потрібно вміти програмувати!** Просто виконуйте команди одну за одною в терміналі (Командний рядок на Windows, Термінал на Mac/Linux).

### Крок 0 — Встановіть Python

Потрібен Python 3.11 або новіший. Перевірте, чи він у вас є:

```bash
python --version
```

Якщо показує `Python 3.11` або вище — все добре. Якщо ні, завантажте Python з [python.org/downloads](https://www.python.org/downloads/) і встановіть. **На Windows обов'язково поставте галочку "Add Python to PATH" під час встановлення.**

### Крок 1 — Завантажте і встановіть TG Harvest

Відкрийте термінал і виконайте ці команди по черзі:

```bash
git clone https://github.com/klivak/tg-harvest.git
cd tg-harvest
python -m venv .venv
```

Активуйте віртуальне середовище:
- **Windows:** `.venv\Scripts\activate`
- **Mac/Linux:** `source .venv/bin/activate`

Потім встановіть:

```bash
pip install -e .
```

### Крок 2 — Отримайте API-ключі Telegram

1. Перейдіть на [my.telegram.org/apps](https://my.telegram.org/apps) у браузері
2. Увійдіть за номером телефону (тим, що прив'язаний до вашого Telegram)
3. Натисніть **API development tools**
4. Вкажіть будь-яку назву додатку (наприклад `tg-harvest`) і коротку назву (наприклад `harvest`)
5. З'являться **App api_id** (число) і **App api_hash** (довгий рядок) — скопіюйте їх

### Крок 3 — Налаштуйте

```bash
cp .env.example .env
```

Відкрийте файл `.env` у будь-якому текстовому редакторі і впишіть ваші значення:

```env
TG_API_ID=12345678
TG_API_HASH=ваш_api_hash
TG_PHONE=+380501234567
```

### Крок 4 — Увійдіть у Telegram

```bash
tg-harvest auth login
```

Telegram надішле код підтвердження у ваш додаток Telegram. Введіть його, коли програма попросить. Якщо у вас увімкнена 2FA, введіть також пароль. **Це потрібно зробити лише один раз** — сесія зберігається локально.

### Крок 5 — Користуйтеся!

```bash
# Веб-інтерфейс — рекомендовано (всі функції в одному місці)
tg-harvest web                # відкривається на http://localhost:8777

# Або через CLI напряму
tg-harvest channels list      # список каналів, груп, ботів
tg-harvest parse @channel     # парсити публічний канал
tg-harvest parse @some_bot    # парсити бота
tg-harvest parse -1001234567890  # парсити приватний канал за числовим ID
tg-harvest search "ключове слово"  # пошук по розпарсених даних
```

> **Важливо:** `tg-harvest auth login` потрібно запустити один раз у терміналі — програма надішле код підтвердження у ваш Telegram-додаток, який треба ввести. Після цього сесія зберігається і веб-інтерфейс працює без будь-яких додаткових дій у терміналі.

---

## Можливості

- **Повний доступ через MTProto** — працює на рівні протоколу, обходить UI-обмеження (канали із забороною копіювання)
- **Канали, групи, боти та приватні чати** — парсить будь-який діалог, до якого ви маєте доступ, включно з ботами та особистими чатами
- **Приватні та обмежені канали** — парсить навіть канали з вимкненим копіюванням
- **Повна витяжка даних** — повідомлення, медіа, реакції, перегляди, репости, відповіді
- **Веб-інтерфейс** — Streamlit з перемикачем мов EN/UK, покроковими підказками, парсингом, пошуком та аналітикою
- **Пошук по повідомленнях** — повнотекстовий пошук із фільтрами
- **Інкрементальний парсинг** — завантажує лише нові повідомлення з моменту останнього запуску
- **Аналітика** — графіки активності, топ-пости, розбивка реакцій
- **Гнучка фільтрація** — за датою, лімітом повідомлень
- **Формати експорту** — JSON, CSV, Excel (.xlsx), HTML-звіт або всі одразу
- **HTML-звіт** — самодостатній HTML-файл з темною/світлою темою, сортувальною таблицею, посиланнями на повідомлення
- **Переекспорт** — конвертація вже розпарсеного JSON у CSV/XLSX/HTML без підключення до Telegram (`tg-harvest export`)
- **Менеджер файлів** — перегляд, видалення та переекспорт файлів прямо з веб-інтерфейсу
- **Вибір полів** — оберіть колонки для експорту (id, text, date, views, url тощо)
- **Прямі посилання** — кожне повідомлення містить URL для швидкого переходу в Telegram
- **Зручний CLI** — прогрес-бари, кольоровий вивід, зведені таблиці
- **Rate limiting** — дотримується лімітів API, автоматично обробляє FloodWait

---

## Приватні та обмежені канали

TG Harvest може витягувати дані з каналів і груп, де Telegram вимикає копіювання в UI. Це можливо тому, що програма працює напряму через **MTProto-протокол** — той самий, що використовує офіційний додаток Telegram. Заборона копіювання — це обмеження інтерфейсу, а не API.

**Умови:**
- Ваш акаунт має бути **учасником** каналу або групи
- Потрібна авторизація через `tg-harvest auth login`

**Як знайти ID приватного каналу:**
1. Запустіть `tg-harvest channels list` або відкрийте сторінку **Канали** у веб-інтерфейсі
2. Знайдіть канал — приватні канали не мають юзернейму, лише числовий ID
3. Скопіюйте числовий ID (наприклад `-1001234567890`)
4. Використайте для парсингу: `tg-harvest parse -1001234567890`

**Що витягує з обмежених каналів:**
- Повний текст повідомлень
- Метадані медіа (назви файлів, типи, розміри — але не самі файли)
- Реакції, перегляди, репости
- Автор поста, інформація про відправника
- Статус редагування, закріплені повідомлення

**Що НЕ може:**
- Отримати доступ до каналів, де ви не є учасником
- Відновити видалені повідомлення
- Завантажити повідомлення з таймером самознищення

---

## Використання

> Встановлення та налаштування — див. [Швидкий старт](#швидкий-старт) вище.

### Авторизація

```bash
# Увійти (інтерактивно: код з Telegram + опційно 2FA)
tg-harvest auth login

# Перевірити статус авторизації
tg-harvest auth status

# Вийти
tg-harvest auth logout
```

### Список каналів, груп і ботів

```bash
# Показати всі доступні канали, групи, ботів та приватні чати
tg-harvest channels list

# Обмежити кількість діалогів для сканування
tg-harvest channels list -l 200
```

### Парсинг повідомлень

```bash
# Парсинг публічного каналу за юзернеймом
tg-harvest parse @channel_name

# Парсинг бота
tg-harvest parse @bot_username

# Парсинг приватного каналу за числовим ID
tg-harvest parse -1001234567890

# З фільтром за датою
tg-harvest parse @channel -f 2024-01-01 -t 2024-12-31

# Обмежити кількість повідомлень
tg-harvest parse @channel --limit 5000

# Інкрементальний режим — тільки нові повідомлення з моменту останнього парсингу
tg-harvest parse @channel -i

# Експорт у CSV
tg-harvest parse @channel --format csv

# Експорт у Excel (.xlsx)
tg-harvest parse @channel --format xlsx

# Експорт у HTML-звіт
tg-harvest parse @channel --format html

# Експорт у всі формати одразу (JSON + CSV + XLSX + HTML)
tg-harvest parse @channel --format all

# Тільки вибрані поля
tg-harvest parse @channel --fields id,text,date,views

# Своя директорія виводу
tg-harvest parse @channel -o ./my_data

# Завантажити медіа (фото, відео, документи)
tg-harvest parse @channel --download-media

# Завантажити медіа з лімітом розміру (МБ)
tg-harvest parse @channel --download-media --max-media-size 100

# Розшифрувати ID відправників у юзернейми та імена
tg-harvest parse @channel --enrich-senders

# Завантажити повні гілки відповідей (додаткові API-запити)
tg-harvest parse @channel --fetch-replies
```

### Пошук

```bash
# Пошук по всіх розпарсених даних
tg-harvest search "ключове слово"

# Фільтр за типом медіа
tg-harvest search "фото" --media-type photo

# Фільтр за мінімальною кількістю переглядів
tg-harvest search "новини" --min-views 1000

# Тільки повідомлення з реакціями
tg-harvest search "оголошення" --has-reactions

# Фільтр за датою
tg-harvest search "оновлення" --from-date 2024-01-01 --to-date 2024-06-30
```

### Переекспорт

```bash
# Переекспорт розпарсеного JSON у CSV (без підключення до Telegram)
tg-harvest export output/channel_20240615.json --format csv

# Переекспорт у HTML-звіт
tg-harvest export output/channel_20240615.json --format html

# Переекспорт усіх JSON-файлів у директорії
tg-harvest export output/ --format all

# З вибором полів
tg-harvest export output/ --format xlsx --fields id,text,date,views,url
```

### Веб-інтерфейс

```bash
# Запустити веб-інтерфейс (порт 8777)
tg-harvest web

# На іншому порту
tg-harvest web -p 9000
```

Веб-інтерфейс містить:
- **Авторизація** — покрокова інструкція з отримання API-ключів, перевірка сесії
- **Канали** — перегляд усіх доступних каналів, груп, ботів та приватних чатів; показує типи та числові ID для копіювання
- **Парсинг** — парсинг будь-якого діалогу за юзернеймом або числовим ID, вибір дат, інкрементальний режим, прогрес-бар, кнопки завантаження
- **Пошук** — повнотекстовий пошук із фільтрами (тип медіа, перегляди, реакції, дата, канал)
- **Аналітика** — інтерактивні графіки: повідомлень на день/тиждень/місяць, активність по годинах, топ-пости за переглядами/реакціями/репостами, розподіл медіа, реакції, залученість, частотність слів
- **Файли** — менеджер файлів для перегляду, видалення та переекспорту розпарсених даних
- **Перемикач мови** — English / Українська (бічна панель)

На кожній сторінці є розділ **Підказки** з поясненнями.

#### Покроковий воркфлоу веб-інтерфейсу

1. **Авторизація** — переконайтеся, що сесія активна (зелений індикатор у бічній панелі)
2. **Канали** — натисніть "Завантажити канали", щоб отримати список діалогів
3. **Парсинг** — оберіть канал зі списку (завантажений у кроці 2), виберіть діапазон дат / пресет, натисніть "Парсити"
4. **Пошук / Аналітика / Файли** — досліджуйте розпарсені дані

> **Зверніть увагу:** Telegram може тимчасово обмежити запити (FloodWait) приблизно кожні 3000 повідомлень. Це нормально — парсер автоматично зупиниться на 30–60 секунд і продовжить. Не закривайте сторінку під час паузи.

---

## Формат виводу

### JSON

Повні структуровані дані з усіма полями:

```json
{
  "channel": {
    "id": 1234567890,
    "title": "Назва каналу",
    "username": "channel_name",
    "members_count": 15000
  },
  "messages": [
    {
      "id": 1,
      "date": "2024-01-15T12:00:00+00:00",
      "text": "Текст повідомлення",
      "views": 5432,
      "forwards": 12,
      "reactions": {
        "total": 150,
        "reactions": [
          {"emoji": "👍", "count": 100},
          {"emoji": "❤️", "count": 50}
        ]
      }
    }
  ],
  "total_messages": 1,
  "parsed_at": "2024-06-01T10:00:00+00:00"
}
```

### CSV / Excel

Зведена таблиця. Відкривається в Excel або Google Sheets.

---

## Структура проекту

```
src/tg_harvest/
  config/       Налаштування, константи
  models/       Pydantic-моделі даних
  client/       Telegram-сесія, rate limiter
  parsers/      Парсинг повідомлень, медіа, каналів
  exporters/    Експорт JSON, CSV, Excel, HTML
  storage/      Стан інкрементального парсингу
  search/       Пошуковий рушій
  analytics/    Статистика та аналітика
  cli/          CLI-команди (Click)
  web/          Веб-інтерфейс (Streamlit)
    locales/    Файли перекладів (en.json, uk.json)
  utils/        Логування, допоміжні функції
```

---

## Додаткові налаштування

| Змінна | За замовчуванням | Опис |
|--------|-----------------|------|
| `TG_SESSION_NAME` | `tg_harvest` | Назва файлу сесії |
| `TG_FLOOD_SLEEP_THRESHOLD` | `60` | Авто-пауза при FloodWait (секунди) |
| `TG_REQUEST_DELAY` | `1.0` | Затримка між запитами до API (секунди) |
| `TG_OUTPUT_DIR` | `./output` | Директорія виводу за замовчуванням |
| `TG_WEB_PORT` | `8777` | Порт веб-інтерфейсу |

---

## Безпека

### Зберігання ключів
- API-ключі (`TG_API_ID`, `TG_API_HASH`, `TG_PHONE`) завантажуються з `.env`, який **виключено з git** — ніколи не комітяться
- Файли сесій Telegram (`sessions/*.session`) **виключено з git** — містять токени авторизації; захистіть правами файлової системи (`chmod 600 sessions/`) на спільних серверах
- Розпарсені дані (`output/`) **виключено з git**
- Номери телефонів маскуються у всіх виводах (`+380***4567`)
- Введення пароля 2FA використовує `getpass` — пароль не відображається в терміналі

### Обробка введення
- Пошукові запити екрануються через `re.escape` перед використанням
- Директорія виводу перевіряється на path traversal (`..`)
- Усі дані валідуються через Pydantic v2 перед використанням

### Веб-інтерфейс
- Текст повідомлень відображається через `st.dataframe()` — не рендериться як markdown (немає XSS)
- Рядки перекладів — статичні файли, не залежать від введення користувача
- **Не призначений для публічного доступу** — запускайте локально або за reverse proxy з автентифікацією

### Відповідальне використання
TG Harvest отримує доступ лише до даних, які ви вже можете бачити як учасник Telegram. Програма не обходить контроль доступу — лише UI-обмеження копіювання. Дотримуйтеся Умов використання Telegram і чинного законодавства при збиранні даних.

---

## Розробка

```bash
# Встановити dev-залежності
pip install -e ".[dev]"

# Запустити тести
pytest -v

# Лінтинг
ruff check src/ tests/

# Форматування
ruff format src/ tests/

# Налаштувати pre-commit хуки
pre-commit install
```

---

## Ліцензія

MIT

---

☕ [Buy me a coffee](https://ko-fi.com/klivak) if this project helped you
