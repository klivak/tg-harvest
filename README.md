# TG Harvest

[![CI](https://github.com/klivak/telegram-api-parser/actions/workflows/ci.yml/badge.svg)](https://github.com/klivak/telegram-api-parser/actions/workflows/ci.yml)

Telegram channel/chat data harvester via MTProto API. Extracts messages, media metadata, reactions, views, forwards from any channel you have access to — including restricted channels where copying is disabled.

**Use cases:** Telegram channel analytics, content archiving, social media monitoring, OSINT research, marketing analysis, competitor tracking, audience engagement metrics, message backup, data journalism, community management.

## Quick Start

```bash
git clone https://github.com/klivak/telegram-api-parser.git
cd telegram-api-parser
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
cp .env.example .env          # fill in TG_API_ID, TG_API_HASH, TG_PHONE
tg-harvest auth login         # one-time login: enter the code sent to your Telegram app
```

After login the session is saved locally. Everything else can be done via the **web UI** or CLI:

```bash
# Web UI — recommended (all features in one place)
tg-harvest web                # opens at http://localhost:8777

# Or use the CLI directly
tg-harvest channels list      # list your channels and get their IDs
tg-harvest parse @channel     # parse a public channel
tg-harvest parse -1001234567890  # parse a private channel by numeric ID
tg-harvest search "keyword"   # search parsed data
```

> **Note:** `tg-harvest auth login` must be run once in the terminal — it requires entering a confirmation code sent to your Telegram app. After that, the session is saved and the web UI works without any further terminal interaction.

---

**Keywords:** telegram parser, telegram scraper, telegram channel export, telegram messages download, telegram analytics, telegram data extraction, telethon, telegram api, telegram backup, telegram archive, telegram channel statistics, telegram reactions, telegram views counter, restricted channel parser, private channel export, telegram to excel, telegram to csv, telegram to json, telegram content analysis, telegram monitoring tool

---

## Features

- **Full MTProto access** — works at the protocol level, bypasses UI restrictions (copy-disabled channels)
- **Private & restricted channels** — parse any channel or group you are a member of, regardless of copy restrictions
- **Rich data extraction** — messages, media, reactions, views, forwards, replies, entities
- **Web UI** — Streamlit interface with EN/UK language switcher, per-page help guides, parsing, search, and analytics
- **Message search** — full-text search across parsed data with filters
- **Incremental parsing** — only fetch new messages since last parse
- **Analytics** — message activity charts, top posts, reaction breakdown
- **Flexible filtering** — by date range, message limit
- **Multiple export formats** — JSON, CSV, Excel (.xlsx), or all at once
- **Field selection** — choose which columns to export (id, text, date, views, etc.)
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

## Requirements

- Python 3.11+
- Telegram API credentials (get from [my.telegram.org/apps](https://my.telegram.org/apps))

---

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

---

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
3. Click **API development tools**
4. Fill in any app title and short name (e.g. `tg-harvest`)
5. Copy **App api_id** and **App api_hash**

---

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
# Parse public channel by username
tg-harvest parse @channel_name

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

# Export to all formats at once (JSON + CSV + XLSX)
tg-harvest parse @channel --format all

# Export only selected fields
tg-harvest parse @channel --fields id,text,date,views

# Custom output directory
tg-harvest parse @channel -o ./my_data

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
- **Auth Status** — step-by-step guide to get API credentials, check session, view config
- **Channels** — browse all accessible channels; private channels show numeric IDs for copying
- **Parse** — parse by username or numeric ID, date pickers, incremental mode, progress bar, download buttons
- **Search** — full-text search with filters (media type, views, reactions, date range, channel)
- **Analytics** — interactive charts: messages per day, hourly activity, top posts by views/reactions, media distribution, reaction breakdown
- **Language switcher** — English / Українська (sidebar)

Each page has a collapsible **Tips / Підказки** section with usage hints.

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
  exporters/    JSON, CSV, Excel export (with field selection)
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

[![CI](https://github.com/klivak/telegram-api-parser/actions/workflows/ci.yml/badge.svg)](https://github.com/klivak/telegram-api-parser/actions/workflows/ci.yml)

Інструмент для збору даних з Telegram-каналів і чатів через MTProto API.

## Швидкий старт

```bash
git clone https://github.com/klivak/telegram-api-parser.git
cd telegram-api-parser
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
cp .env.example .env          # вписати TG_API_ID, TG_API_HASH, TG_PHONE
tg-harvest auth login         # одноразовий вхід: введіть код з вашого Telegram
```

Після входу сесія зберігається локально. Все інше можна робити через **веб-інтерфейс** або CLI:

```bash
# Веб-інтерфейс — рекомендовано (всі функції в одному місці)
tg-harvest web                # відкривається на http://localhost:8777

# Або через CLI напряму
tg-harvest channels list      # список каналів та їхні ID
tg-harvest parse @channel     # парсити публічний канал
tg-harvest parse -1001234567890  # парсити приватний канал за числовим ID
tg-harvest search "ключове слово"  # пошук по розпарсених даних
```

> **Важливо:** `tg-harvest auth login` потрібно запустити один раз у терміналі — програма надішле код підтвердження у ваш Telegram-додаток, який треба ввести. Після цього сесія зберігається і веб-інтерфейс працює без будь-яких додаткових дій у терміналі.

Витягує повідомлення, метадані медіа, реакції, перегляди, репости з будь-якого каналу, учасником якого ви є — включно з каналами з вимкненим копіюванням.

---

## Можливості

- **Повний доступ через MTProto** — працює на рівні протоколу, обходить UI-обмеження (канали із забороною копіювання)
- **Приватні та обмежені канали** — парсить будь-який канал або групу, учасником якої ви є
- **Повна витяжка даних** — повідомлення, медіа, реакції, перегляди, репости, відповіді
- **Веб-інтерфейс** — Streamlit з перемикачем мов EN/UK, покроковими підказками, парсингом, пошуком та аналітикою
- **Пошук по повідомленнях** — повнотекстовий пошук із фільтрами
- **Інкрементальний парсинг** — завантажує лише нові повідомлення з моменту останнього запуску
- **Аналітика** — графіки активності, топ-пости, розбивка реакцій
- **Гнучка фільтрація** — за датою, лімітом повідомлень
- **Формати експорту** — JSON, CSV, Excel (.xlsx) або всі одразу
- **Вибір полів** — оберіть колонки для експорту (id, text, date, views тощо)
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

## Вимоги

- Python 3.11+
- API-ключі Telegram (отримати на [my.telegram.org/apps](https://my.telegram.org/apps))

---

## Встановлення

```bash
git clone https://github.com/klivak/telegram-api-parser.git
cd telegram-api-parser

# Створити віртуальне середовище
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Встановити
pip install -e .

# Встановити dev-залежності (для тестів і лінтингу)
pip install -e ".[dev]"
```

---

## Налаштування

Скопіюйте `.env.example` у `.env` і заповніть ключі:

```bash
cp .env.example .env
```

```env
TG_API_ID=12345678
TG_API_HASH=ваш_api_hash
TG_PHONE=+380501234567
```

### Як отримати API-ключі

1. Перейдіть на [my.telegram.org/apps](https://my.telegram.org/apps)
2. Увійдіть за номером телефону
3. Натисніть **API development tools**
4. Вкажіть будь-яку назву додатку (наприклад `tg-harvest`)
5. Скопіюйте **App api_id** та **App api_hash**

---

## Використання

### Авторизація

```bash
# Увійти (інтерактивно: код з Telegram + опційно 2FA)
tg-harvest auth login

# Перевірити статус авторизації
tg-harvest auth status

# Вийти
tg-harvest auth logout
```

### Список каналів

```bash
# Показати всі доступні канали та групи
tg-harvest channels list

# Обмежити кількість діалогів для сканування
tg-harvest channels list -l 200
```

### Парсинг повідомлень

```bash
# Парсинг публічного каналу за юзернеймом
tg-harvest parse @channel_name

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

# Експорт у всі формати одразу (JSON + CSV + XLSX)
tg-harvest parse @channel --format all

# Тільки вибрані поля
tg-harvest parse @channel --fields id,text,date,views

# Своя директорія виводу
tg-harvest parse @channel -o ./my_data
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

### Веб-інтерфейс

```bash
# Запустити веб-інтерфейс (порт 8777)
tg-harvest web

# На іншому порту
tg-harvest web -p 9000
```

Веб-інтерфейс містить:
- **Авторизація** — покрокова інструкція з отримання API-ключів, перевірка сесії
- **Канали** — перегляд усіх доступних каналів; приватні канали показують числовий ID для копіювання
- **Парсинг** — парсинг за юзернеймом або числовим ID, вибір дат, інкрементальний режим, прогрес-бар, кнопки завантаження
- **Пошук** — повнотекстовий пошук із фільтрами (тип медіа, перегляди, реакції, дата, канал)
- **Аналітика** — інтерактивні графіки: повідомлень на день, активність по годинах, топ-пости, розподіл медіа, реакції
- **Перемикач мови** — English / Українська (бічна панель)

На кожній сторінці є розділ **Підказки** з поясненнями.

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
  exporters/    Експорт JSON, CSV, Excel
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
