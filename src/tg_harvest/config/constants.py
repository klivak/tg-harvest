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
SUPPORTED_FORMATS = ("json", "csv", "xlsx", "all")

# Exportable fields (user can select subset)
ALL_EXPORT_FIELDS = (
    "id",
    "date",
    "text",
    "sender_id",
    "post_author",
    "views",
    "forwards",
    "replies_count",
    "reactions_total",
    "reactions_detail",
    "media_type",
    "media_file_name",
    "media_url",
    "forward_from_id",
    "forward_from_name",
    "reply_to_msg_id",
    "grouped_id",
    "is_pinned",
    "is_edited",
    "edit_date",
)

# Analytics defaults
DEFAULT_TOP_N = 10

# Web UI
DEFAULT_WEB_PORT = 8777
