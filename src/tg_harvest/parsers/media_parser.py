"""Extract media metadata from Telethon message objects."""

from telethon.tl import types

from tg_harvest.models.media import MediaInfo, MediaType, PollAnswer


def parse_media(media) -> MediaInfo | None:
    """Convert Telethon media object to MediaInfo model."""
    if media is None:
        return None

    if isinstance(media, types.MessageMediaPhoto):
        return _parse_photo(media)
    if isinstance(media, types.MessageMediaDocument):
        return _parse_document(media)
    if isinstance(media, types.MessageMediaWebPage):
        return _parse_web_page(media)
    if isinstance(media, types.MessageMediaGeoLive):
        geo = media.geo
        if isinstance(geo, types.GeoPoint):
            return MediaInfo(type=MediaType.GEO, latitude=geo.lat, longitude=geo.long)
        return MediaInfo(type=MediaType.GEO)
    if isinstance(media, types.MessageMediaGeo):
        geo = media.geo
        if isinstance(geo, types.GeoPoint):
            return MediaInfo(type=MediaType.GEO, latitude=geo.lat, longitude=geo.long)
        return MediaInfo(type=MediaType.GEO)
    if isinstance(media, types.MessageMediaContact):
        first = media.first_name or ""
        last = media.last_name or ""
        name = f"{first} {last}".strip() or None
        return MediaInfo(
            type=MediaType.CONTACT,
            contact_name=name,
            contact_phone=media.phone_number or None,
        )
    if isinstance(media, types.MessageMediaPoll):
        return _parse_poll(media)

    return MediaInfo(type=MediaType.NONE)


def _parse_photo(media: types.MessageMediaPhoto) -> MediaInfo:
    photo = media.photo
    if not isinstance(photo, types.Photo):
        return MediaInfo(type=MediaType.PHOTO)

    largest = max(
        (s for s in photo.sizes if isinstance(s, (types.PhotoSize, types.PhotoSizeProgressive))),
        key=lambda s: getattr(s, "size", 0) or (s.sizes[-1] if hasattr(s, "sizes") else 0),
        default=None,
    )
    width = getattr(largest, "w", None)
    height = getattr(largest, "h", None)
    file_size = getattr(largest, "size", None)
    if file_size is None and hasattr(largest, "sizes"):
        file_size = largest.sizes[-1] if largest.sizes else None

    return MediaInfo(
        type=MediaType.PHOTO,
        file_size=file_size,
        width=width,
        height=height,
    )


def _parse_document(media: types.MessageMediaDocument) -> MediaInfo:
    doc = media.document
    if not isinstance(doc, types.Document):
        return MediaInfo(type=MediaType.DOCUMENT)

    media_type = MediaType.DOCUMENT
    file_name = None
    duration = None
    width = None
    height = None
    title = None
    performer = None

    for attr in doc.attributes:
        if isinstance(attr, types.DocumentAttributeFilename):
            file_name = attr.file_name
        elif isinstance(attr, types.DocumentAttributeVideo):
            duration = attr.duration
            width = attr.w
            height = attr.h
            if attr.round_message:
                media_type = MediaType.VIDEO_NOTE
            else:
                media_type = MediaType.VIDEO
        elif isinstance(attr, types.DocumentAttributeAudio):
            duration = attr.duration
            title = attr.title
            performer = attr.performer
            if attr.voice:
                media_type = MediaType.VOICE
            else:
                media_type = MediaType.AUDIO
        elif isinstance(attr, types.DocumentAttributeSticker):
            media_type = MediaType.STICKER
        elif isinstance(attr, types.DocumentAttributeAnimated):
            media_type = MediaType.GIF

    return MediaInfo(
        type=media_type,
        file_name=file_name,
        file_size=doc.size,
        mime_type=doc.mime_type,
        duration=duration,
        width=width,
        height=height,
        title=title,
        performer=performer,
    )


def _parse_web_page(media: types.MessageMediaWebPage) -> MediaInfo:
    page = media.webpage
    if not isinstance(page, types.WebPage):
        return MediaInfo(type=MediaType.WEB_PAGE)

    return MediaInfo(
        type=MediaType.WEB_PAGE,
        title=page.title,
        url=page.url,
    )


def _parse_poll(media: types.MessageMediaPoll) -> MediaInfo:
    poll = media.poll
    title = poll.question if hasattr(poll, "question") else None
    # question can be a TextWithEntities in newer TL layers
    if hasattr(title, "text"):
        title = title.text

    answers: list[PollAnswer] = []
    if hasattr(poll, "answers") and poll.answers:
        for answer in poll.answers:
            answer_text = answer.text
            if hasattr(answer_text, "text"):
                answer_text = answer_text.text
            answers.append(PollAnswer(text=str(answer_text), voter_count=0))

    # Merge voter counts from results
    if media.results and hasattr(media.results, "results") and media.results.results:
        for i, result in enumerate(media.results.results):
            if i < len(answers):
                answers[i].voter_count = result.voters

    return MediaInfo(
        type=MediaType.POLL,
        title=title,
        poll_answers=answers if answers else None,
    )
