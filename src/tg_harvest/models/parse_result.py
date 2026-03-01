"""Aggregate parse result model."""

from datetime import datetime

from pydantic import BaseModel, computed_field

from tg_harvest.models.channel import ChannelInfo
from tg_harvest.models.message import ParsedMessage


class DownloadStats(BaseModel):
    total_files: int = 0
    total_bytes: int = 0
    skipped_size_limit: int = 0
    skipped_existing: int = 0
    failed: int = 0


class ParseResult(BaseModel):
    channel: ChannelInfo
    messages: list[ParsedMessage] = []
    parsed_at: datetime
    from_date: datetime | None = None
    to_date: datetime | None = None
    download_stats: DownloadStats | None = None

    @computed_field
    @property
    def total_messages(self) -> int:
        return len(self.messages)
