"""Base exporter interface."""

from abc import ABC, abstractmethod
from pathlib import Path

from tg_parser.models.parse_result import ParseResult


class BaseExporter(ABC):
    """Abstract base class for all exporters."""

    @abstractmethod
    async def export(self, result: ParseResult, output_path: Path) -> Path:
        """Export parse result to a file.

        Args:
            result: The parse result to export.
            output_path: Directory where the file will be saved.

        Returns:
            Path to the created file.
        """
