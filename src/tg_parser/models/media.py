"""Media type and metadata models."""

from enum import StrEnum

from pydantic import BaseModel


class MediaType(StrEnum):
    PHOTO = "photo"
    VIDEO = "video"
    DOCUMENT = "document"
    AUDIO = "audio"
    VOICE = "voice"
    VIDEO_NOTE = "video_note"
    STICKER = "sticker"
    GIF = "gif"
    POLL = "poll"
    GEO = "geo"
    CONTACT = "contact"
    WEB_PAGE = "web_page"
    NONE = "none"


class MediaInfo(BaseModel):
    type: MediaType
    file_name: str | None = None
    file_size: int | None = None
    mime_type: str | None = None
    duration: int | None = None
    width: int | None = None
    height: int | None = None
    title: str | None = None
    performer: str | None = None
    url: str | None = None
