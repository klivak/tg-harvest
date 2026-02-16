"""Application constants and defaults."""

# Telegram API limits
MAX_MESSAGES_PER_REQUEST = 100
DEFAULT_ITER_WAIT_TIME = 2.0

# Export defaults
DEFAULT_JSON_INDENT = 2
DEFAULT_CSV_DELIMITER = ","
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# CLI defaults
DEFAULT_MESSAGE_LIMIT = 0  # 0 = no limit
DEFAULT_EXPORT_FORMAT = "json"
SUPPORTED_FORMATS = ("json", "csv", "both")

# Analytics defaults
DEFAULT_TOP_N = 10

# Web UI
DEFAULT_WEB_PORT = 8777
