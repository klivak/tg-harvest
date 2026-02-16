"""Root CLI application."""

import click

from tg_parser import __version__
from tg_parser.cli.commands.auth import auth
from tg_parser.cli.commands.channels import channels
from tg_parser.cli.commands.parse import parse
from tg_parser.cli.commands.search import search
from tg_parser.cli.commands.web import web
from tg_parser.utils.logging import setup_logging


@click.group()
@click.version_option(version=__version__, prog_name="tg-parser")
@click.option("-v", "--verbose", is_flag=True, help="Enable debug logging.")
def cli(verbose: bool):
    """Telegram channel/chat parser via MTProto API."""
    setup_logging(verbose=verbose)


cli.add_command(auth)
cli.add_command(channels)
cli.add_command(parse)
cli.add_command(search)
cli.add_command(web)
