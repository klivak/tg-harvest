"""Tests for media models."""

from tg_harvest.models.media import MediaInfo, MediaType


class TestMediaType:
    def test_all_types_are_strings(self):
        for mt in MediaType:
            assert isinstance(mt, str)
            assert mt == mt.value

    def test_photo_type(self):
        assert MediaType.PHOTO == "photo"

    def test_video_type(self):
        assert MediaType.VIDEO == "video"

    def test_sticker_type(self):
        assert MediaType.STICKER == "sticker"


class TestMediaInfo:
    def test_photo_minimal(self):
        info = MediaInfo(type=MediaType.PHOTO)
        assert info.type == MediaType.PHOTO
        assert info.file_name is None
        assert info.file_size is None

    def test_video_full(self):
        info = MediaInfo(
            type=MediaType.VIDEO,
            file_name="video.mp4",
            file_size=5242880,
            mime_type="video/mp4",
            duration=120,
            width=1280,
            height=720,
        )
        assert info.file_name == "video.mp4"
        assert info.duration == 120
        assert info.width == 1280

    def test_audio_with_metadata(self):
        info = MediaInfo(
            type=MediaType.AUDIO,
            title="Song Title",
            performer="Artist",
            duration=240,
            mime_type="audio/mpeg",
        )
        assert info.title == "Song Title"
        assert info.performer == "Artist"

    def test_web_page(self):
        info = MediaInfo(
            type=MediaType.WEB_PAGE,
            title="Example Page",
            url="https://example.com",
        )
        assert info.url == "https://example.com"

    def test_json_serialization(self):
        info = MediaInfo(type=MediaType.PHOTO, file_size=1024, width=800, height=600)
        data = info.model_dump(mode="json")
        assert data["type"] == "photo"
        assert data["file_size"] == 1024
        assert data["file_name"] is None

    def test_from_dict(self):
        data = {"type": "document", "file_name": "file.pdf", "file_size": 2048}
        info = MediaInfo.model_validate(data)
        assert info.type == MediaType.DOCUMENT
        assert info.file_name == "file.pdf"
