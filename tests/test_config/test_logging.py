"""Tests for logging configuration."""

import logging
from unittest.mock import patch

from rich.logging import RichHandler

from tg_harvest.utils.logging import setup_logging


class TestSetupLogging:
    def test_setup_creates_rich_handler(self):
        """Verify setup_logging calls basicConfig with RichHandler."""
        with patch("logging.basicConfig") as mock_basic:
            setup_logging(verbose=False)
            mock_basic.assert_called_once()
            kwargs = mock_basic.call_args[1]
            assert kwargs["level"] == logging.INFO
            assert len(kwargs["handlers"]) == 1
            assert isinstance(kwargs["handlers"][0], RichHandler)

    def test_setup_verbose_uses_debug(self):
        with patch("logging.basicConfig") as mock_basic:
            setup_logging(verbose=True)
            kwargs = mock_basic.call_args[1]
            assert kwargs["level"] == logging.DEBUG

    def test_setup_format(self):
        with patch("logging.basicConfig") as mock_basic:
            setup_logging()
            kwargs = mock_basic.call_args[1]
            assert kwargs["format"] == "%(message)s"
            assert kwargs["datefmt"] == "[%X]"

    def test_rich_handler_has_tracebacks(self):
        with patch("logging.basicConfig") as mock_basic:
            setup_logging()
            handler = mock_basic.call_args[1]["handlers"][0]
            assert handler.rich_tracebacks is True

    def test_verbose_and_non_verbose_both_create_handler(self):
        for verbose in (True, False):
            with patch("logging.basicConfig") as mock_basic:
                setup_logging(verbose=verbose)
                handler = mock_basic.call_args[1]["handlers"][0]
                assert isinstance(handler, RichHandler)
