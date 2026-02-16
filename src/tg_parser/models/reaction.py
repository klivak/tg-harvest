"""Reaction data models."""

from pydantic import BaseModel


class ReactionCount(BaseModel):
    emoji: str | None = None
    custom_emoji_id: int | None = None
    count: int


class ReactionsInfo(BaseModel):
    total: int = 0
    reactions: list[ReactionCount] = []
