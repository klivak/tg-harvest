"""Application constants and defaults."""

# Telegram API limits
MAX_MESSAGES_PER_REQUEST = 100
DEFAULT_ITER_WAIT_TIME = 0

# Export defaults
DEFAULT_JSON_INDENT = 2
DEFAULT_CSV_DELIMITER = ","
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# CLI defaults
DEFAULT_MESSAGE_LIMIT = 0  # 0 = no limit
DEFAULT_EXPORT_FORMAT = "json"
SUPPORTED_FORMATS = ("json", "csv", "xlsx", "html", "all")

# Media download defaults
DEFAULT_MAX_MEDIA_SIZE_MB = 50
MEDIA_SUBDIRS = {
    "photo": "photos",
    "video": "videos",
    "document": "docs",
    "audio": "audio",
    "voice": "voice",
    "video_note": "video_notes",
    "sticker": "stickers",
    "gif": "gifs",
}

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
    "reply_to_top_id",
    "grouped_id",
    "is_pinned",
    "is_edited",
    "edit_date",
    "url",
    "sender_username",
    "sender_name",
    "sender_is_bot",
    "media_local_path",
)

# Analytics defaults
DEFAULT_TOP_N = 10
MIN_WORD_LENGTH = 4
TOP_WORDS_COUNT = 20
TOP_REACTIONS_DISPLAY = 15

# Text display
DEFAULT_TRUNCATE_LENGTH = 100
PREVIEW_TRUNCATE_LENGTH = 200

# Web UI
DEFAULT_WEB_PORT = 8777
DEFAULT_DIALOG_LIMIT = 100
