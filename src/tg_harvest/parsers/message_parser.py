"""Convert raw Telethon Message objects to ParsedMessage models."""

import logging

from telethon.tl import types

from tg_harvest.models.media import MediaInfo
from tg_harvest.models.message import EntityInfo, ForwardInfo, ParsedMessage, ReplyInfo
from tg_harvest.models.reaction import ReactionCount, ReactionsInfo
from tg_harvest.parsers.media_parser import parse_media

logger = logging.getLogger(__name__)


def parse_message(msg, channel_id: int) -> ParsedMessage | None:
    """Convert a Telethon Message to a ParsedMessage.

    Returns None if the message is a service message or cannot be parsed.
    """
    if isinstance(msg, types.MessageService):
        return None

    if not isinstance(msg, types.Message):
        return None

    try:
        return ParsedMessage(
            id=msg.id,
            channel_id=channel_id,
            date=msg.date,
            text=msg.message or "",
            sender_id=_extract_peer_id(msg.from_id),
            post_author=msg.post_author,
            media=_extract_media(msg.media),
            views=msg.views,
            forwards=msg.forwards,
            replies_count=_extract_replies_count(msg.replies),
            reactions=_extract_reactions(msg.reactions),
            forward_info=_extract_forward(msg.fwd_from),
            reply_info=_extract_reply(msg.reply_to),
            grouped_id=msg.grouped_id,
            is_pinned=msg.pinned or False,
            is_edited=msg.edit_date is not None,
            edit_date=msg.edit_date,
            entities=_extract_entities(msg.entities),
        )
    except Exception:
        logger.warning("Failed to parse message id=%d, skipping", msg.id, exc_info=True)
        return None


def _extract_peer_id(peer) -> int | None:
    if peer is None:
        return None
    if isinstance(peer, types.PeerUser):
        return peer.user_id
    if isinstance(peer, types.PeerChannel):
        return peer.channel_id
    if isinstance(peer, types.PeerChat):
        return peer.chat_id
    return None


def _extract_media(media) -> MediaInfo | None:
    return parse_media(media)


def _extract_replies_count(replies) -> int | None:
    if replies is None:
        return None
    return getattr(replies, "replies", None)


def _extract_reactions(reactions) -> ReactionsInfo | None:
    if reactions is None:
        return None
    results = getattr(reactions, "results", None)
    if not results:
        return None

    counts = []
    total = 0
    for r in results:
        count = r.count
        total += count
        reaction = r.reaction
        if isinstance(reaction, types.ReactionEmoji):
            counts.append(ReactionCount(emoji=reaction.emoticon, count=count))
        elif isinstance(reaction, types.ReactionCustomEmoji):
            counts.append(ReactionCount(custom_emoji_id=reaction.document_id, count=count))
        else:
            counts.append(ReactionCount(emoji=str(reaction), count=count))

    return ReactionsInfo(total=total, reactions=counts)


def _extract_forward(fwd) -> ForwardInfo | None:
    if fwd is None:
        return None
    return ForwardInfo(
        from_id=_extract_peer_id(fwd.from_id),
        from_name=fwd.from_name,
        channel_post=fwd.channel_post,
        date=fwd.date,
    )


def _extract_reply(reply_to) -> ReplyInfo | None:
    if reply_to is None:
        return None
    if not isinstance(reply_to, types.MessageReplyHeader):
        return None
    return ReplyInfo(
        reply_to_msg_id=reply_to.reply_to_msg_id,
        reply_to_top_id=reply_to.reply_to_top_id,
    )


def _extract_entities(entities) -> list[EntityInfo]:
    if not entities:
        return []

    result = []
    for e in entities:
        entity_type = type(e).__name__.replace("MessageEntity", "").lower()
        url = getattr(e, "url", None)
        user_id = getattr(e, "user_id", None)
        result.append(
            EntityInfo(
                type=entity_type,
                offset=e.offset,
                length=e.length,
                url=url,
                user_id=user_id,
            )
        )
    return result
