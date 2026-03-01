"""Tests for media parser."""

from unittest.mock import MagicMock

from telethon.tl import types

from tg_harvest.models.media import MediaType
from tg_harvest.parsers.media_parser import parse_media


class TestParseMedia:
    def test_none_media(self):
        assert parse_media(None) is None

    def test_photo(self):
        photo_size = MagicMock(spec=types.PhotoSize)
        photo_size.w = 1920
        photo_size.h = 1080
        photo_size.size = 102400

        photo = MagicMock(spec=types.Photo)
        photo.sizes = [photo_size]

        media = MagicMock(spec=types.MessageMediaPhoto)
        media.photo = photo

        result = parse_media(media)
        assert result is not None
        assert result.type == MediaType.PHOTO
        assert result.width == 1920
        assert result.height == 1080
        assert result.file_size == 102400

    def test_video_document(self):
        video_attr = MagicMock(spec=types.DocumentAttributeVideo)
        video_attr.duration = 120
        video_attr.w = 1280
        video_attr.h = 720
        video_attr.round_message = False

        filename_attr = MagicMock(spec=types.DocumentAttributeFilename)
        filename_attr.file_name = "video.mp4"

        doc = MagicMock(spec=types.Document)
        doc.attributes = [video_attr, filename_attr]
        doc.size = 5242880
        doc.mime_type = "video/mp4"

        media = MagicMock(spec=types.MessageMediaDocument)
        media.document = doc

        result = parse_media(media)
        assert result is not None
        assert result.type == MediaType.VIDEO
        assert result.duration == 120
        assert result.file_name == "video.mp4"
        assert result.file_size == 5242880

    def test_video_note(self):
        video_attr = MagicMock(spec=types.DocumentAttributeVideo)
        video_attr.duration = 30
        video_attr.w = 360
        video_attr.h = 360
        video_attr.round_message = True

        doc = MagicMock(spec=types.Document)
        doc.attributes = [video_attr]
        doc.size = 1000
        doc.mime_type = "video/mp4"

        media = MagicMock(spec=types.MessageMediaDocument)
        media.document = doc

        result = parse_media(media)
        assert result.type == MediaType.VIDEO_NOTE

    def test_audio_document(self):
        audio_attr = MagicMock(spec=types.DocumentAttributeAudio)
        audio_attr.duration = 240
        audio_attr.title = "Song"
        audio_attr.performer = "Artist"
        audio_attr.voice = False

        doc = MagicMock(spec=types.Document)
        doc.attributes = [audio_attr]
        doc.size = 3000000
        doc.mime_type = "audio/mpeg"

        media = MagicMock(spec=types.MessageMediaDocument)
        media.document = doc

        result = parse_media(media)
        assert result.type == MediaType.AUDIO
        assert result.title == "Song"
        assert result.performer == "Artist"
        assert result.duration == 240

    def test_voice_message(self):
        audio_attr = MagicMock(spec=types.DocumentAttributeAudio)
        audio_attr.duration = 15
        audio_attr.title = None
        audio_attr.performer = None
        audio_attr.voice = True

        doc = MagicMock(spec=types.Document)
        doc.attributes = [audio_attr]
        doc.size = 50000
        doc.mime_type = "audio/ogg"

        media = MagicMock(spec=types.MessageMediaDocument)
        media.document = doc

        result = parse_media(media)
        assert result.type == MediaType.VOICE
        assert result.duration == 15

    def test_sticker(self):
        sticker_attr = MagicMock(spec=types.DocumentAttributeSticker)

        doc = MagicMock(spec=types.Document)
        doc.attributes = [sticker_attr]
        doc.size = 30000
        doc.mime_type = "image/webp"

        media = MagicMock(spec=types.MessageMediaDocument)
        media.document = doc

        result = parse_media(media)
        assert result.type == MediaType.STICKER

    def test_gif(self):
        animated_attr = MagicMock(spec=types.DocumentAttributeAnimated)

        doc = MagicMock(spec=types.Document)
        doc.attributes = [animated_attr]
        doc.size = 200000
        doc.mime_type = "video/mp4"

        media = MagicMock(spec=types.MessageMediaDocument)
        media.document = doc

        result = parse_media(media)
        assert result.type == MediaType.GIF

    def test_web_page(self):
        webpage = MagicMock(spec=types.WebPage)
        webpage.title = "Example"
        webpage.url = "https://example.com"

        media = MagicMock(spec=types.MessageMediaWebPage)
        media.webpage = webpage

        result = parse_media(media)
        assert result.type == MediaType.WEB_PAGE
        assert result.title == "Example"
        assert result.url == "https://example.com"

    def test_geo(self):
        geo_point = MagicMock(spec=types.GeoPoint)
        geo_point.lat = 50.45
        geo_point.long = 30.52
        media = MagicMock(spec=types.MessageMediaGeo)
        media.geo = geo_point
        result = parse_media(media)
        assert result.type == MediaType.GEO
        assert result.latitude == 50.45
        assert result.longitude == 30.52

    def test_contact(self):
        media = MagicMock(spec=types.MessageMediaContact)
        media.first_name = "John"
        media.last_name = "Doe"
        media.phone_number = "+380501234567"
        result = parse_media(media)
        assert result.type == MediaType.CONTACT
        assert result.contact_name == "John Doe"
        assert result.contact_phone == "+380501234567"

    def test_poll_with_plain_question(self):
        poll = MagicMock()
        poll.question = "What color?"
        poll.answers = None

        media = MagicMock(spec=types.MessageMediaPoll)
        media.poll = poll
        media.results = None

        result = parse_media(media)
        assert result.type == MediaType.POLL

    def test_poll_with_text_entity_question(self):
        question = MagicMock()
        question.text = "Favorite language?"

        poll = MagicMock()
        poll.question = question
        poll.answers = None

        media = MagicMock(spec=types.MessageMediaPoll)
        media.poll = poll
        media.results = None

        result = parse_media(media)
        assert result.type == MediaType.POLL
        assert result.title == "Favorite language?"

    def test_plain_document(self):
        filename_attr = MagicMock(spec=types.DocumentAttributeFilename)
        filename_attr.file_name = "report.pdf"

        doc = MagicMock(spec=types.Document)
        doc.attributes = [filename_attr]
        doc.size = 500000
        doc.mime_type = "application/pdf"

        media = MagicMock(spec=types.MessageMediaDocument)
        media.document = doc

        result = parse_media(media)
        assert result.type == MediaType.DOCUMENT
        assert result.file_name == "report.pdf"
        assert result.mime_type == "application/pdf"
