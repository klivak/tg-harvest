"""Message data models."""

from datetime import datetime

from pydantic import BaseModel

from tg_harvest.models.media import MediaInfo
from tg_harvest.models.reaction import ReactionsInfo


class ForwardInfo(BaseModel):
    from_id: int | None = None
    from_name: str | None = None
    channel_post: int | None = None
    date: datetime | None = None


class ReplyInfo(BaseModel):
    reply_to_msg_id: int | None = None
    reply_to_top_id: int | None = None


class EntityInfo(BaseModel):
    type: str
    offset: int
    length: int
    url: str | None = None
    user_id: int | None = None


class ParsedMessage(BaseModel):
    id: int
    channel_id: int
    date: datetime
    text: str = ""
    sender_id: int | None = None
    post_author: str | None = None
    media: MediaInfo | None = None
    views: int | None = None
    forwards: int | None = None
    replies_count: int | None = None
    reactions: ReactionsInfo | None = None
    forward_info: ForwardInfo | None = None
    reply_info: ReplyInfo | None = None
    grouped_id: int | None = None
    is_pinned: bool = False
    is_edited: bool = False
    edit_date: datetime | None = None
    entities: list[EntityInfo] = []
