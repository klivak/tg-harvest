"""Parse options for controlling extended parsing behavior."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ParseOptions:
    """Options that control extended parsing behavior (media download, etc.)."""

    # Media download
    download_media: bool = False
    max_media_size_mb: int = 50
    media_output_dir: Path | None = None

    # Reply threads
    fetch_replies: bool = False

    # Sender enrichment
    enrich_senders: bool = False
