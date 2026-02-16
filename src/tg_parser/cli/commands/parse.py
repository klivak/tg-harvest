"""Main parse command."""

import asyncio
from pathlib import Path

import click
from rich.console import Console
from rich.progress import BarColumn, MofNCompleteColumn, Progress, TextColumn, TimeElapsedColumn

from tg_parser.cli.formatters import print_parse_summary
from tg_parser.client.rate_limiter import RateLimiter
from tg_parser.client.session import TelegramSession
from tg_parser.config import Settings
from tg_parser.config.constants import DEFAULT_EXPORT_FORMAT, SUPPORTED_FORMATS
from tg_parser.exporters.csv_exporter import CsvExporter
from tg_parser.exporters.json_exporter import JsonExporter
from tg_parser.parsers.channel_parser import ChannelParser
from tg_parser.utils.date_utils import parse_date

console = Console()


@click.command()
@click.argument("channel")
@click.option(
    "-f",
    "--from-date",
    default=None,
    help="Start date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS).",
)
@click.option(
    "-t",
    "--to-date",
    default=None,
    help="End date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS).",
)
@click.option(
    "-l",
    "--limit",
    default=0,
    help="Max messages to fetch (0 = no limit).",
    show_default=True,
)
@click.option(
    "--format",
    "export_format",
    type=click.Choice(SUPPORTED_FORMATS, case_sensitive=False),
    default=DEFAULT_EXPORT_FORMAT,
    help="Export format.",
    show_default=True,
)
@click.option(
    "-o",
    "--output",
    "output_dir",
    type=click.Path(),
    default=None,
    help="Output directory (default: from settings or ./output).",
)
def parse(
    channel: str,
    from_date: str | None,
    to_date: str | None,
    limit: int,
    export_format: str,
    output_dir: str | None,
):
    """Parse messages from a Telegram channel or group.

    CHANNEL can be a username (@channel), invite link, or numeric ID.
    """
    asyncio.run(_parse_async(channel, from_date, to_date, limit, export_format, output_dir))


async def _parse_async(
    channel: str,
    from_date_str: str | None,
    to_date_str: str | None,
    limit: int,
    export_format: str,
    output_dir: str | None,
):
    settings = Settings()
    out_path = Path(output_dir) if output_dir else settings.output_dir

    from_date = parse_date(from_date_str) if from_date_str else None
    to_date = parse_date(to_date_str) if to_date_str else None

    # Resolve channel identifier
    channel_id: str | int = channel
    if channel.lstrip("-").isdigit():
        channel_id = int(channel)

    async with TelegramSession(settings) as session:
        rate_limiter = RateLimiter(delay=settings.request_delay)
        parser = ChannelParser(session.client, rate_limiter)

        # Parse with progress bar
        with Progress(
            TextColumn("[bold blue]Parsing"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("messages", total=None)

            def on_progress(count: int):
                progress.update(task, completed=count)

            result = await parser.parse(
                channel=channel_id,
                from_date=from_date,
                to_date=to_date,
                limit=limit,
                on_progress=on_progress,
            )

        if not result.messages:
            console.print("[yellow]No messages found for the given criteria.[/yellow]")
            return

        # Export
        output_files: list[str] = []

        if export_format in ("json", "both"):
            exporter = JsonExporter()
            path = await exporter.export(result, out_path)
            output_files.append(str(path))

        if export_format in ("csv", "both"):
            exporter = CsvExporter()
            path = await exporter.export(result, out_path)
            output_files.append(str(path))

        print_parse_summary(result, output_files)
