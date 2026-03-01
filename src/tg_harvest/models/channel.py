"""Channel/chat info model."""

from datetime import datetime

from pydantic import BaseModel


class ChannelInfo(BaseModel):
    id: int
    title: str
    username: str | None = None
    is_channel: bool = True
    is_group: bool = False
    is_bot: bool = False
    is_private: bool = False
    members_count: int | None = None
    description: str | None = None
    created_at: datetime | None = None
    restricted: bool = False
    scam: bool = False
    verified: bool = False
