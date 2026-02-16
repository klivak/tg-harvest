"""Tests for reaction models."""

from tg_harvest.models.reaction import ReactionCount, ReactionsInfo


class TestReactionCount:
    def test_emoji_reaction(self):
        r = ReactionCount(emoji="\U0001f44d", count=100)
        assert r.emoji == "\U0001f44d"
        assert r.count == 100
        assert r.custom_emoji_id is None

    def test_custom_emoji_reaction(self):
        r = ReactionCount(custom_emoji_id=12345, count=50)
        assert r.custom_emoji_id == 12345
        assert r.emoji is None

    def test_count_required(self):
        import pytest

        with pytest.raises(Exception):
            ReactionCount(emoji="\U0001f44d")


class TestReactionsInfo:
    def test_empty_reactions(self):
        info = ReactionsInfo()
        assert info.total == 0
        assert info.reactions == []

    def test_with_reactions(self, sample_reactions):
        assert sample_reactions.total == 250
        assert len(sample_reactions.reactions) == 3
        assert sample_reactions.reactions[0].emoji == "\U0001f44d"
        assert sample_reactions.reactions[2].custom_emoji_id == 12345

    def test_json_serialization(self):
        info = ReactionsInfo(
            total=10,
            reactions=[ReactionCount(emoji="\u2764\ufe0f", count=10)],
        )
        data = info.model_dump(mode="json")
        assert data["total"] == 10
        assert len(data["reactions"]) == 1
        assert data["reactions"][0]["count"] == 10
