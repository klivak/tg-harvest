"""Root CLI application."""

import click

from tg_harvest import __version__
from tg_harvest.cli.commands.auth import auth
from tg_harvest.cli.commands.channels import channels
from tg_harvest.cli.commands.export import export
from tg_harvest.cli.commands.parse import parse
from tg_harvest.cli.commands.search import search
from tg_harvest.cli.commands.web import web
from tg_harvest.utils.logging import setup_logging


@click.group()
@click.version_option(version=__version__, prog_name="tg-harvest")
@click.option("-v", "--verbose", is_flag=True, help="Enable debug logging.")
def cli(verbose: bool):
    """Telegram channel/chat data harvester via MTProto API."""
    setup_logging(verbose=verbose)


cli.add_command(auth)
cli.add_command(channels)
cli.add_command(export)
cli.add_command(parse)
cli.add_command(search)
cli.add_command(web)
