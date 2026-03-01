"""Edge case tests for media parser: missing data, unknown types, progressive photos."""

from unittest.mock import MagicMock

from telethon.tl import types

from tg_harvest.models.media import MediaType
from tg_harvest.parsers.media_parser import parse_media


class TestPhotoEdgeCases:
    def test_photo_not_photo_type(self):
        """photo attribute that's not a types.Photo instance."""
        media = MagicMock(spec=types.MessageMediaPhoto)
        media.photo = MagicMock()  # Not spec=types.Photo
        result = parse_media(media)
        assert result.type == MediaType.PHOTO
        # No dimensions since not a real Photo
        assert result.width is None

    def test_photo_with_no_matching_sizes(self):
        """Photo with sizes that don't match PhotoSize or PhotoSizeProgressive."""
        photo = MagicMock(spec=types.Photo)
        # PhotoStrippedSize or PhotoCachedSize won't match the filter
        stripped = MagicMock()
        photo.sizes = [stripped]

        media = MagicMock(spec=types.MessageMediaPhoto)
        media.photo = photo

        result = parse_media(media)
        assert result.type == MediaType.PHOTO
        assert result.width is None
        assert result.file_size is None

    def test_photo_with_progressive_size(self):
        """PhotoSizeProgressive stores sizes as a list of byte counts."""
        progressive = MagicMock(spec=types.PhotoSizeProgressive)
        progressive.w = 1280
        progressive.h = 720
        progressive.size = None  # Progressive doesn't have .size
        progressive.sizes = [1000, 5000, 20000, 50000]

        photo = MagicMock(spec=types.Photo)
        photo.sizes = [progressive]

        media = MagicMock(spec=types.MessageMediaPhoto)
        media.photo = photo

        result = parse_media(media)
        assert result.type == MediaType.PHOTO
        assert result.width == 1280
        assert result.height == 720
        assert result.file_size == 50000

    def test_photo_multiple_sizes_picks_largest(self):
        small = MagicMock(spec=types.PhotoSize)
        small.w = 320
        small.h = 240
        small.size = 5000

        large = MagicMock(spec=types.PhotoSize)
        large.w = 1920
        large.h = 1080
        large.size = 100000

        photo = MagicMock(spec=types.Photo)
        photo.sizes = [small, large]

        media = MagicMock(spec=types.MessageMediaPhoto)
        media.photo = photo

        result = parse_media(media)
        assert result.file_size == 100000
        assert result.width == 1920


class TestDocumentEdgeCases:
    def test_document_not_document_type(self):
        """document attribute that's not a types.Document."""
        media = MagicMock(spec=types.MessageMediaDocument)
        media.document = MagicMock()  # Not spec=types.Document
        result = parse_media(media)
        assert result.type == MediaType.DOCUMENT

    def test_document_with_no_attributes(self):
        doc = MagicMock(spec=types.Document)
        doc.attributes = []
        doc.size = 1024
        doc.mime_type = "application/octet-stream"

        media = MagicMock(spec=types.MessageMediaDocument)
        media.document = doc

        result = parse_media(media)
        assert result.type == MediaType.DOCUMENT
        assert result.file_name is None
        assert result.file_size == 1024

    def test_sticker_overrides_document(self):
        """Sticker attribute should override default DOCUMENT type."""
        filename_attr = MagicMock(spec=types.DocumentAttributeFilename)
        filename_attr.file_name = "sticker.webp"

        sticker_attr = MagicMock(spec=types.DocumentAttributeSticker)

        doc = MagicMock(spec=types.Document)
        doc.attributes = [filename_attr, sticker_attr]
        doc.size = 10000
        doc.mime_type = "image/webp"

        media = MagicMock(spec=types.MessageMediaDocument)
        media.document = doc

        result = parse_media(media)
        assert result.type == MediaType.STICKER
        assert result.file_name == "sticker.webp"

    def test_gif_overrides_document(self):
        animated_attr = MagicMock(spec=types.DocumentAttributeAnimated)

        doc = MagicMock(spec=types.Document)
        doc.attributes = [animated_attr]
        doc.size = 50000
        doc.mime_type = "video/mp4"

        media = MagicMock(spec=types.MessageMediaDocument)
        media.document = doc

        result = parse_media(media)
        assert result.type == MediaType.GIF


class TestWebPageEdgeCases:
    def test_webpage_not_webpage_type(self):
        """webpage attribute that's not types.WebPage (e.g., WebPageEmpty)."""
        media = MagicMock(spec=types.MessageMediaWebPage)
        media.webpage = MagicMock()  # Not spec=types.WebPage
        result = parse_media(media)
        assert result.type == MediaType.WEB_PAGE
        assert result.title is None
        assert result.url is None


class TestPollEdgeCases:
    def test_poll_with_no_question_attr(self):
        """Poll object that doesn't have a question attribute."""
        poll = MagicMock(spec=[])  # No attributes
        media = MagicMock(spec=types.MessageMediaPoll)
        media.poll = poll
        media.results = None
        result = parse_media(media)
        assert result.type == MediaType.POLL
        assert result.title is None

    def test_poll_with_string_question(self):
        poll = MagicMock()
        poll.question = "Simple question?"
        poll.answers = None
        media = MagicMock(spec=types.MessageMediaPoll)
        media.poll = poll
        media.results = None
        result = parse_media(media)
        assert result.title == "Simple question?"


class TestUnknownMediaType:
    def test_unknown_media_returns_none_type(self):
        """Unknown media type should return MediaInfo with NONE type."""
        media = MagicMock()  # Unknown type
        result = parse_media(media)
        assert result.type == MediaType.NONE
