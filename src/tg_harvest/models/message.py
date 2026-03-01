"""Message data models."""

from datetime import datetime

from pydantic import BaseModel, computed_field

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


class SenderInfo(BaseModel):
    id: int
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    is_bot: bool = False

    @computed_field  # type: ignore[prop-decorator]
    @property
    def display_name(self) -> str:
        parts = [self.first_name or "", self.last_name or ""]
        name = " ".join(p for p in parts if p).strip()
        return name or self.username or str(self.id)


class EntityInfo(BaseModel):
    type: str
    offset: int
    length: int
    url: str | None = None
    user_id: int | None = None


class ParsedMessage(BaseModel):
    id: int
    channel_id: int
    channel_username: str | None = None
    date: datetime
    text: str = ""
    sender_id: int | None = None
    post_author: str | None = None
    sender: SenderInfo | None = None
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

    @computed_field  # type: ignore[prop-decorator]
    @property
    def url(self) -> str:
        if self.channel_username:
            return f"https://t.me/{self.channel_username}/{self.id}"
        return f"https://t.me/c/{self.channel_id}/{self.id}"
