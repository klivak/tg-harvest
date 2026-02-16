"""Channel listing commands."""

import asyncio

import click

from tg_parser.cli.formatters import print_channel_table
from tg_parser.client.rate_limiter import RateLimiter
from tg_parser.client.session import TelegramSession
from tg_parser.config import Settings
from tg_parser.parsers.channel_parser import ChannelParser


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
            rate_limiter = RateLimiter(delay=settings.request_delay)
            parser = ChannelParser(session.client, rate_limiter)
            result = await parser.list_channels(limit=limit)

            if result:
                print_channel_table(result)
            else:
                click.echo("No channels or groups found.")

    asyncio.run(_list())
