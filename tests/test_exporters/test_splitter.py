"""Tests for message splitting utilities."""

from datetime import datetime, timezone

from tg_harvest.exporters.splitter import make_part_result, make_part_suffix, split_messages
from tg_harvest.models.message import ParsedMessage


def _msg(msg_id: int) -> ParsedMessage:
    return ParsedMessage(
        id=msg_id,
        channel_id=123,
        date=datetime(2024, 6, 15, tzinfo=timezone.utc),
        text=f"Message {msg_id}",
    )


class TestSplitMessages:
    def test_single_part_returns_original(self):
        msgs = [_msg(1), _msg(2), _msg(3)]
        result = split_messages(msgs, 1)
        assert len(result) == 1
        assert result[0] is msgs

    def test_zero_parts_returns_original(self):
        msgs = [_msg(1), _msg(2)]
        result = split_messages(msgs, 0)
        assert len(result) == 1
        assert result[0] is msgs

    def test_empty_list(self):
        result = split_messages([], 3)
        assert len(result) == 1
        assert result[0] == []

    def test_even_split(self):
        msgs = [_msg(i) for i in range(6)]
        result = split_messages(msgs, 3)
        assert len(result) == 3
        assert [len(c) for c in result] == [2, 2, 2]

    def test_uneven_split_distributes_remainder(self):
        msgs = [_msg(i) for i in range(10)]
        result = split_messages(msgs, 3)
        assert len(result) == 3
        assert [len(c) for c in result] == [4, 3, 3]

    def test_preserves_order(self):
        msgs = [_msg(i) for i in range(6)]
        result = split_messages(msgs, 2)
        ids_0 = [m.id for m in result[0]]
        ids_1 = [m.id for m in result[1]]
        assert ids_0 == [0, 1, 2]
        assert ids_1 == [3, 4, 5]

    def test_more_parts_than_messages(self):
        msgs = [_msg(1), _msg(2)]
        result = split_messages(msgs, 5)
        assert len(result) == 2
        assert all(len(c) == 1 for c in result)

    def test_single_message_multiple_parts(self):
        msgs = [_msg(1)]
        result = split_messages(msgs, 3)
        assert len(result) == 1
        assert len(result[0]) == 1


class TestMakePartSuffix:
    def test_no_split(self):
        assert make_part_suffix(1, 1) == ""

    def test_zero_total(self):
        assert make_part_suffix(1, 0) == ""

    def test_split_format(self):
        assert make_part_suffix(1, 3) == "_part1of3"
        assert make_part_suffix(2, 3) == "_part2of3"
        assert make_part_suffix(3, 3) == "_part3of3"

    def test_ten_parts(self):
        assert make_part_suffix(5, 10) == "_part5of10"


class TestMakePartResult:
    def test_preserves_channel(self, sample_parse_result):
        msgs = sample_parse_result.messages[:1]
        part = make_part_result(sample_parse_result, msgs)
        assert part.channel == sample_parse_result.channel

    def test_uses_provided_messages(self, sample_parse_result):
        msgs = sample_parse_result.messages[:1]
        part = make_part_result(sample_parse_result, msgs)
        assert len(part.messages) == 1
        assert part.messages[0].id == msgs[0].id

    def test_preserves_metadata(self, sample_parse_result):
        msgs = sample_parse_result.messages[:1]
        part = make_part_result(sample_parse_result, msgs)
        assert part.parsed_at == sample_parse_result.parsed_at
        assert part.from_date == sample_parse_result.from_date
        assert part.to_date == sample_parse_result.to_date

    def test_total_messages_reflects_subset(self, sample_parse_result):
        msgs = sample_parse_result.messages[:1]
        part = make_part_result(sample_parse_result, msgs)
        assert part.total_messages == 1
