"""Download media files from Telethon message objects."""

import logging
from pathlib import Path

from telethon import TelegramClient

from tg_harvest.config.constants import MEDIA_SUBDIRS
from tg_harvest.models.media import MediaInfo, MediaType
from tg_harvest.models.parse_result import DownloadStats

logger = logging.getLogger(__name__)

NON_DOWNLOADABLE = {
    MediaType.POLL,
    MediaType.GEO,
    MediaType.CONTACT,
    MediaType.WEB_PAGE,
    MediaType.NONE,
}


class MediaDownloader:
    """Downloads media files during parsing."""

    def __init__(
        self,
        client: TelegramClient,
        base_dir: Path,
        max_size_mb: int = 50,
    ):
        self._client = client
        self._base_dir = base_dir
        self._max_size_bytes = max_size_mb * 1024 * 1024
        self._stats = DownloadStats()

    @property
    def stats(self) -> DownloadStats:
        return self._stats

    async def download(self, telethon_msg, media_info: MediaInfo) -> str | None:
        """Download media from a Telethon message, return local path or None."""
        if media_info.type in NON_DOWNLOADABLE:
            return None

        # Size check before downloading (0 = no limit)
        if (
            self._max_size_bytes > 0
            and media_info.file_size
            and media_info.file_size > self._max_size_bytes
        ):
            self._stats.skipped_size_limit += 1
            logger.debug(
                "Skipping msg %d: size %d exceeds limit %d",
                telethon_msg.id,
                media_info.file_size,
                self._max_size_bytes,
            )
            return None

        # Determine target directory by media type
        subdir = MEDIA_SUBDIRS.get(media_info.type.value, "other")
        target_dir = self._base_dir / subdir
        target_dir.mkdir(parents=True, exist_ok=True)

        # Generate deterministic filename
        file_name = self._resolve_filename(telethon_msg.id, media_info)
        target_path = target_dir / file_name

        # Resume: skip existing files
        if target_path.exists():
            self._stats.skipped_existing += 1
            return str(target_path)

        try:
            result = await self._client.download_media(telethon_msg, file=str(target_path))
            if result:
                self._stats.total_files += 1
                self._stats.total_bytes += target_path.stat().st_size
                return str(target_path)
            else:
                self._stats.failed += 1
                return None
        except Exception:
            self._stats.failed += 1
            logger.warning(
                "Failed to download media for msg %d",
                telethon_msg.id,
                exc_info=True,
            )
            return None

    @staticmethod
    def _resolve_filename(msg_id: int, media_info: MediaInfo) -> str:
        """Build a deterministic filename: {msg_id}_{original_name_or_type.ext}."""
        if media_info.file_name:
            # Sanitize: strip directory components and null bytes to prevent path traversal
            safe_name = Path(media_info.file_name).name.replace("\0", "")
            if safe_name:
                return f"{msg_id}_{safe_name}"
        ext = MediaDownloader._guess_extension(media_info)
        return f"{msg_id}_{media_info.type.value}{ext}"

    @staticmethod
    def _guess_extension(media_info: MediaInfo) -> str:
        if media_info.mime_type:
            parts = media_info.mime_type.split("/")
            if len(parts) == 2:
                return f".{parts[1].split('+')[0]}"
        type_ext = {
            "photo": ".jpg",
            "video": ".mp4",
            "audio": ".mp3",
            "voice": ".ogg",
            "video_note": ".mp4",
            "gif": ".mp4",
            "sticker": ".webp",
        }
        return type_ext.get(media_info.type.value, "")
