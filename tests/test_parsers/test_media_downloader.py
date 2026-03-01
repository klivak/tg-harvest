"""Tests for MediaDownloader."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from tg_harvest.models.media import MediaInfo, MediaType
from tg_harvest.parsers.media_downloader import MediaDownloader


@pytest.fixture
def tmp_media_dir(tmp_path):
    return tmp_path / "media"


@pytest.fixture
def downloader(tmp_media_dir):
    client = AsyncMock()
    return MediaDownloader(client, tmp_media_dir, max_size_mb=10)


def _make_media(
    media_type=MediaType.PHOTO,
    file_name=None,
    file_size=1024,
    mime_type="image/jpeg",
):
    return MediaInfo(
        type=media_type,
        file_name=file_name,
        file_size=file_size,
        mime_type=mime_type,
    )


def _make_telethon_msg(msg_id=1):
    msg = MagicMock()
    msg.id = msg_id
    return msg


class TestSkipNonDownloadable:
    @pytest.mark.asyncio
    async def test_skip_poll(self, downloader):
        media = _make_media(media_type=MediaType.POLL)
        result = await downloader.download(_make_telethon_msg(), media)
        assert result is None

    @pytest.mark.asyncio
    async def test_skip_geo(self, downloader):
        media = _make_media(media_type=MediaType.GEO)
        result = await downloader.download(_make_telethon_msg(), media)
        assert result is None

    @pytest.mark.asyncio
    async def test_skip_contact(self, downloader):
        media = _make_media(media_type=MediaType.CONTACT)
        result = await downloader.download(_make_telethon_msg(), media)
        assert result is None

    @pytest.mark.asyncio
    async def test_skip_web_page(self, downloader):
        media = _make_media(media_type=MediaType.WEB_PAGE)
        result = await downloader.download(_make_telethon_msg(), media)
        assert result is None

    @pytest.mark.asyncio
    async def test_skip_none_type(self, downloader):
        media = _make_media(media_type=MediaType.NONE)
        result = await downloader.download(_make_telethon_msg(), media)
        assert result is None


class TestSizeLimit:
    @pytest.mark.asyncio
    async def test_skip_file_exceeding_size_limit(self, downloader):
        # max_size_mb=10 → 10 * 1024 * 1024 = 10485760 bytes
        media = _make_media(file_size=20_000_000)
        result = await downloader.download(_make_telethon_msg(), media)
        assert result is None
        assert downloader.stats.skipped_size_limit == 1

    @pytest.mark.asyncio
    async def test_allow_file_within_size_limit(self, downloader, tmp_media_dir):
        media = _make_media(file_size=1024)
        msg = _make_telethon_msg(msg_id=42)

        async def fake_download(m, file=None):
            Path(file).parent.mkdir(parents=True, exist_ok=True)
            Path(file).write_bytes(b"fake image data")
            return file

        downloader._client.download_media = fake_download
        result = await downloader.download(msg, media)
        assert result is not None
        assert downloader.stats.total_files == 1

    @pytest.mark.asyncio
    async def test_allow_when_file_size_unknown(self, downloader, tmp_media_dir):
        """file_size=None should not trigger size limit skip."""
        media = _make_media(file_size=None)
        msg = _make_telethon_msg(msg_id=99)

        async def fake_download(m, file=None):
            Path(file).parent.mkdir(parents=True, exist_ok=True)
            Path(file).write_bytes(b"data")
            return file

        downloader._client.download_media = fake_download
        result = await downloader.download(msg, media)
        assert result is not None


class TestResume:
    @pytest.mark.asyncio
    async def test_skip_existing_file(self, downloader, tmp_media_dir):
        media = _make_media(file_name="existing.jpg")
        msg = _make_telethon_msg(msg_id=5)

        # Pre-create the file
        target_dir = tmp_media_dir / "photos"
        target_dir.mkdir(parents=True)
        (target_dir / "5_existing.jpg").write_bytes(b"old data")

        result = await downloader.download(msg, media)
        assert result is not None
        assert "5_existing.jpg" in result
        assert downloader.stats.skipped_existing == 1
        # download_media should NOT have been called
        downloader._client.download_media.assert_not_awaited()


class TestFilename:
    def test_with_original_name(self):
        media = _make_media(file_name="photo.jpg")
        name = MediaDownloader._resolve_filename(1, media)
        assert name == "1_photo.jpg"

    def test_without_original_name_uses_mime(self):
        media = _make_media(file_name=None, mime_type="image/jpeg")
        name = MediaDownloader._resolve_filename(2, media)
        assert name == "2_photo.jpeg"

    def test_without_original_name_no_mime(self):
        media = _make_media(file_name=None, mime_type=None)
        name = MediaDownloader._resolve_filename(3, media)
        assert name == "3_photo.jpg"

    def test_video_type(self):
        media = _make_media(media_type=MediaType.VIDEO, file_name=None, mime_type=None)
        name = MediaDownloader._resolve_filename(4, media)
        assert name == "4_video.mp4"

    def test_document_type(self):
        media = _make_media(media_type=MediaType.DOCUMENT, file_name="report.pdf", mime_type=None)
        name = MediaDownloader._resolve_filename(5, media)
        assert name == "5_report.pdf"


class TestDownloadFailure:
    @pytest.mark.asyncio
    async def test_download_returns_none_on_failure(self, downloader):
        media = _make_media()
        msg = _make_telethon_msg()

        downloader._client.download_media = AsyncMock(return_value=None)
        result = await downloader.download(msg, media)
        assert result is None
        assert downloader.stats.failed == 1

    @pytest.mark.asyncio
    async def test_download_exception_handled(self, downloader):
        media = _make_media()
        msg = _make_telethon_msg()

        downloader._client.download_media = AsyncMock(side_effect=ConnectionError("timeout"))
        result = await downloader.download(msg, media)
        assert result is None
        assert downloader.stats.failed == 1


class TestSubdirectories:
    @pytest.mark.asyncio
    async def test_video_goes_to_videos_dir(self, downloader, tmp_media_dir):
        media = _make_media(media_type=MediaType.VIDEO, file_name="clip.mp4")
        msg = _make_telethon_msg(msg_id=10)

        async def fake_download(m, file=None):
            Path(file).parent.mkdir(parents=True, exist_ok=True)
            Path(file).write_bytes(b"video data")
            return file

        downloader._client.download_media = fake_download
        result = await downloader.download(msg, media)
        assert "videos" in result
        assert "10_clip.mp4" in result

    @pytest.mark.asyncio
    async def test_audio_goes_to_audio_dir(self, downloader, tmp_media_dir):
        media = _make_media(media_type=MediaType.AUDIO, file_name="song.mp3")
        msg = _make_telethon_msg(msg_id=11)

        async def fake_download(m, file=None):
            Path(file).parent.mkdir(parents=True, exist_ok=True)
            Path(file).write_bytes(b"audio data")
            return file

        downloader._client.download_media = fake_download
        result = await downloader.download(msg, media)
        assert "audio" in result
