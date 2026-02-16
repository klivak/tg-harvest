"""Search engine for parsed messages."""

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path

from tg_harvest.models.media import MediaType
from tg_harvest.models.message import ParsedMessage
from tg_harvest.models.parse_result import ParseResult
from tg_harvest.utils.date_utils import parse_date

logger = logging.getLogger(__name__)


@dataclass
class SearchFilters:
    keyword: str = ""
    media_type: MediaType | None = None
    has_reactions: bool | None = None
    min_views: int | None = None
    date_from: str | None = None
    date_to: str | None = None
    channel_id: int | None = None


@dataclass
class SearchResult:
    message: ParsedMessage
    channel_title: str
    channel_username: str | None


class SearchEngine:
    """Search across parsed results stored as JSON files."""

    def load_results(self, output_dir: Path) -> list[ParseResult]:
        results = []
        if not output_dir.exists():
            return results

        for json_file in sorted(output_dir.glob("*.json"), reverse=True):
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
                results.append(ParseResult.model_validate(data))
            except Exception:
                logger.warning("Failed to load %s, skipping", json_file)
        return results

    def search(
        self,
        results: list[ParseResult],
        filters: SearchFilters,
    ) -> list[SearchResult]:
        matches: list[SearchResult] = []
        pattern = re.compile(re.escape(filters.keyword), re.IGNORECASE) if filters.keyword else None

        for result in results:
            if filters.channel_id and result.channel.id != filters.channel_id:
                continue

            for msg in result.messages:
                if not self._matches(msg, filters, pattern):
                    continue
                matches.append(
                    SearchResult(
                        message=msg,
                        channel_title=result.channel.title,
                        channel_username=result.channel.username,
                    )
                )

        matches.sort(key=lambda r: r.message.date, reverse=True)
        return matches

    def _matches(
        self,
        msg: ParsedMessage,
        filters: SearchFilters,
        pattern: re.Pattern | None,
    ) -> bool:
        if pattern and not pattern.search(msg.text):
            return False

        if filters.media_type is not None:
            if msg.media is None or msg.media.type != filters.media_type:
                return False

        if filters.has_reactions is True:
            if not msg.reactions or msg.reactions.total == 0:
                return False

        if filters.min_views is not None:
            if msg.views is None or msg.views < filters.min_views:
                return False

        if filters.date_from:
            dt = parse_date(filters.date_from)
            if msg.date < dt:
                return False

        if filters.date_to:
            dt = parse_date(filters.date_to)
            if msg.date > dt:
                return False

        return True
