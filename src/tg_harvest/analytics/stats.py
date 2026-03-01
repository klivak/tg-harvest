"""Channel statistics and analytics."""

from collections import Counter

from tg_harvest.config.constants import DEFAULT_TOP_N
from tg_harvest.models.message import ParsedMessage
from tg_harvest.models.parse_result import ParseResult


class ChannelStats:
    """Compute statistics from a ParseResult."""

    def __init__(self, result: ParseResult):
        self._result = result
        self._messages = result.messages

    @property
    def total(self) -> int:
        return len(self._messages)

    def messages_per_day(self) -> dict[str, int]:
        counter: Counter[str] = Counter()
        for msg in self._messages:
            day = msg.date.strftime("%Y-%m-%d")
            counter[day] += 1
        return dict(sorted(counter.items()))

    def activity_by_hour(self) -> dict[int, int]:
        counter: Counter[int] = Counter()
        for msg in self._messages:
            counter[msg.date.hour] += 1
        return {h: counter.get(h, 0) for h in range(24)}

    def top_by_views(self, n: int = DEFAULT_TOP_N) -> list[ParsedMessage]:
        with_views = [m for m in self._messages if m.views is not None]
        return sorted(with_views, key=lambda m: m.views or 0, reverse=True)[:n]

    def top_by_reactions(self, n: int = DEFAULT_TOP_N) -> list[ParsedMessage]:
        with_reactions = [m for m in self._messages if m.reactions and m.reactions.total > 0]
        return sorted(with_reactions, key=lambda m: m.reactions.total, reverse=True)[:n]

    def media_distribution(self) -> dict[str, int]:
        counter: Counter[str] = Counter()
        for msg in self._messages:
            if msg.media:
                counter[msg.media.type] += 1
            else:
                counter["text_only"] += 1
        return dict(counter.most_common())

    def reactions_summary(self) -> dict[str, int]:
        counter: Counter[str] = Counter()
        for msg in self._messages:
            if msg.reactions:
                for r in msg.reactions.reactions:
                    label = r.emoji or f"custom:{r.custom_emoji_id}"
                    counter[label] += r.count
        return dict(counter.most_common())

    def forwarded_count(self) -> int:
        return sum(1 for m in self._messages if m.forward_info is not None)

    def edited_count(self) -> int:
        return sum(1 for m in self._messages if m.is_edited)

    def avg_views(self) -> float:
        with_views = [m.views for m in self._messages if m.views is not None]
        return sum(with_views) / len(with_views) if with_views else 0.0

    def avg_reactions(self) -> float:
        totals = [
            m.reactions.total for m in self._messages if m.reactions and m.reactions.total > 0
        ]
        return sum(totals) / len(totals) if totals else 0.0

    def messages_per_week(self) -> dict[str, int]:
        counter: Counter[str] = Counter()
        for msg in self._messages:
            week = msg.date.strftime("%G-W%V")
            counter[week] += 1
        return dict(sorted(counter.items()))

    def messages_per_month(self) -> dict[str, int]:
        counter: Counter[str] = Counter()
        for msg in self._messages:
            month = msg.date.strftime("%Y-%m")
            counter[month] += 1
        return dict(sorted(counter.items()))

    def top_by_forwards(self, n: int = DEFAULT_TOP_N) -> list[ParsedMessage]:
        with_forwards = [m for m in self._messages if m.forwards is not None and m.forwards > 0]
        return sorted(with_forwards, key=lambda m: m.forwards or 0, reverse=True)[:n]

    def engagement_rate(self) -> float:
        rates = []
        for m in self._messages:
            if m.views and m.views > 0 and m.reactions and m.reactions.total > 0:
                rates.append(m.reactions.total / m.views)
        return sum(rates) / len(rates) if rates else 0.0

    def avg_message_length(self) -> float:
        if not self._messages:
            return 0.0
        lengths = [len(m.text) for m in self._messages]
        return sum(lengths) / len(lengths)

    def thread_stats(self) -> dict:
        """Compute reply thread statistics from reply_to_top_id data."""
        threads: dict[int, int] = {}
        for msg in self._messages:
            if msg.reply_info and msg.reply_info.reply_to_top_id:
                top_id = msg.reply_info.reply_to_top_id
                threads[top_id] = threads.get(top_id, 0) + 1

        if not threads:
            return {"total_threads": 0, "avg_replies": 0.0, "max_replies": 0}

        return {
            "total_threads": len(threads),
            "avg_replies": sum(threads.values()) / len(threads),
            "max_replies": max(threads.values()),
        }

    def top_threads(self, n: int = DEFAULT_TOP_N) -> list[tuple[int, int]]:
        """Return top N threads by reply count as (top_msg_id, count) pairs."""
        threads: dict[int, int] = {}
        for msg in self._messages:
            if msg.reply_info and msg.reply_info.reply_to_top_id:
                top_id = msg.reply_info.reply_to_top_id
                threads[top_id] = threads.get(top_id, 0) + 1
        return sorted(threads.items(), key=lambda x: x[1], reverse=True)[:n]
