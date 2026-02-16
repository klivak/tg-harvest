"""Tests for date utilities."""

from datetime import datetime, timezone

import pytest

from tg_harvest.utils.date_utils import ensure_utc, parse_date


class TestParseDate:
    def test_date_only(self):
        result = parse_date("2024-01-15")
        assert result == datetime(2024, 1, 15, tzinfo=timezone.utc)

    def test_datetime_full(self):
        result = parse_date("2024-06-15 14:30:00")
        assert result == datetime(2024, 6, 15, 14, 30, 0, tzinfo=timezone.utc)

    def test_result_has_utc_timezone(self):
        result = parse_date("2024-01-01")
        assert result.tzinfo == timezone.utc

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_date("15/01/2024")

    def test_invalid_format_message(self):
        with pytest.raises(ValueError, match="YYYY-MM-DD"):
            parse_date("not-a-date")

    def test_empty_string_raises(self):
        with pytest.raises(ValueError):
            parse_date("")


class TestEnsureUtc:
    def test_naive_datetime(self):
        dt = datetime(2024, 1, 1, 12, 0, 0)
        result = ensure_utc(dt)
        assert result.tzinfo == timezone.utc
        assert result.hour == 12

    def test_already_utc(self):
        dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        result = ensure_utc(dt)
        assert result.tzinfo == timezone.utc
        assert result == dt

    def test_different_timezone(self):
        from datetime import timedelta

        tz_plus3 = timezone(timedelta(hours=3))
        dt = datetime(2024, 1, 1, 15, 0, 0, tzinfo=tz_plus3)
        result = ensure_utc(dt)
        assert result.tzinfo == timezone.utc
        assert result.hour == 12  # 15:00+03 = 12:00 UTC
