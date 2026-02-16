"""Aggregate parse result model."""

from datetime import datetime

from pydantic import BaseModel, computed_field

from tg_harvest.models.channel import ChannelInfo
from tg_harvest.models.message import ParsedMessage


class ParseResult(BaseModel):
    channel: ChannelInfo
    messages: list[ParsedMessage] = []
    parsed_at: datetime
    from_date: datetime | None = None
    to_date: datetime | None = None

    @computed_field
    @property
    def total_messages(self) -> int:
        return len(self.messages)
