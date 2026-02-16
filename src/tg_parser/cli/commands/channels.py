"""Channel listing commands."""

import asyncio

import click
from telethon.tl import types

from tg_parser.cli.formatters import print_channel_table
from tg_parser.client.session import TelegramSession
from tg_parser.config import Settings
from tg_parser.models.channel import ChannelInfo


@click.group()
def channels():
    """Browse accessible channels and groups."""


@channels.command(name="list")
@click.option(
    "-l", "--limit", default=100, help="Max number of dialogs to scan.", show_default=True
)
def list_channels(limit: int):
    """List all channels and groups you have access to."""

    async def _list():
        settings = Settings()
        async with TelegramSession(settings) as session:
            result: list[ChannelInfo] = []
            async for dialog in session.client.iter_dialogs(limit=limit):
                entity = dialog.entity
                if not isinstance(entity, (types.Channel, types.Chat)):
                    continue

                is_channel = isinstance(entity, types.Channel)
                is_group = is_channel and entity.megagroup

                result.append(
                    ChannelInfo(
                        id=entity.id,
                        title=entity.title,
                        username=getattr(entity, "username", None),
                        is_channel=is_channel and not is_group,
                        is_group=is_group or isinstance(entity, types.Chat),
                        is_private=not getattr(entity, "username", None),
                        members_count=getattr(entity, "participants_count", None),
                        restricted=getattr(entity, "restricted", False),
                        scam=getattr(entity, "scam", False),
                        verified=getattr(entity, "verified", False),
                    )
                )

            if result:
                print_channel_table(result)
            else:
                click.echo("No channels or groups found.")

    asyncio.run(_list())
