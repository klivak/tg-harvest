"""Tests for application constants."""

from tg_harvest.config.constants import (
    ALL_EXPORT_FIELDS,
    DEFAULT_CSV_DELIMITER,
    DEFAULT_DATE_FORMAT,
    DEFAULT_EXPORT_FORMAT,
    DEFAULT_ITER_WAIT_TIME,
    DEFAULT_JSON_INDENT,
    DEFAULT_MESSAGE_LIMIT,
    DEFAULT_TOP_N,
    DEFAULT_WEB_PORT,
    MAX_MESSAGES_PER_REQUEST,
    SUPPORTED_FORMATS,
)


class TestTelegramConstants:
    def test_max_messages_per_request_positive(self):
        assert MAX_MESSAGES_PER_REQUEST > 0

    def test_default_iter_wait_time_non_negative(self):
        assert DEFAULT_ITER_WAIT_TIME >= 0


class TestExportConstants:
    def test_json_indent_reasonable(self):
        assert DEFAULT_JSON_INDENT in (2, 4)

    def test_csv_delimiter_single_char(self):
        assert len(DEFAULT_CSV_DELIMITER) == 1

    def test_date_format_valid(self):
        from datetime import datetime

        # Should not raise
        datetime.now().strftime(DEFAULT_DATE_FORMAT)

    def test_default_export_format_in_supported(self):
        assert DEFAULT_EXPORT_FORMAT in SUPPORTED_FORMATS

    def test_supported_formats_contains_required(self):
        assert "json" in SUPPORTED_FORMATS
        assert "csv" in SUPPORTED_FORMATS
        assert "xlsx" in SUPPORTED_FORMATS
        assert "all" in SUPPORTED_FORMATS

    def test_supported_formats_is_tuple(self):
        assert isinstance(SUPPORTED_FORMATS, tuple)


class TestExportFields:
    def test_all_export_fields_not_empty(self):
        assert len(ALL_EXPORT_FIELDS) > 0

    def test_all_export_fields_is_tuple(self):
        assert isinstance(ALL_EXPORT_FIELDS, tuple)

    def test_required_fields_present(self):
        required = ("id", "date", "text", "views", "forwards", "media_type")
        for field in required:
            assert field in ALL_EXPORT_FIELDS, f"Missing required field: {field}"

    def test_no_duplicate_fields(self):
        assert len(ALL_EXPORT_FIELDS) == len(set(ALL_EXPORT_FIELDS))

    def test_fields_are_strings(self):
        for field in ALL_EXPORT_FIELDS:
            assert isinstance(field, str)

    def test_fields_are_snake_case(self):
        import re

        for field in ALL_EXPORT_FIELDS:
            assert re.match(r"^[a-z][a-z0-9_]*$", field), f"Field not snake_case: {field}"


class TestCliConstants:
    def test_default_message_limit_is_no_limit(self):
        assert DEFAULT_MESSAGE_LIMIT == 0


class TestAnalyticsConstants:
    def test_default_top_n_positive(self):
        assert DEFAULT_TOP_N > 0


class TestWebConstants:
    def test_default_web_port_valid(self):
        assert 1024 < DEFAULT_WEB_PORT < 65535

    def test_default_web_port_is_8777(self):
        assert DEFAULT_WEB_PORT == 8777
