"""Main parse command."""

import asyncio
from pathlib import Path

import click
from rich.console import Console
from rich.progress import BarColumn, MofNCompleteColumn, Progress, TextColumn, TimeElapsedColumn

from tg_harvest.cli.formatters import print_parse_summary
from tg_harvest.client.rate_limiter import RateLimiter
from tg_harvest.client.session import TelegramSession
from tg_harvest.config import Settings
from tg_harvest.config.constants import (
    ALL_EXPORT_FIELDS,
    DEFAULT_EXPORT_FORMAT,
    SUPPORTED_FORMATS,
)
from tg_harvest.exporters.csv_exporter import CsvExporter
from tg_harvest.exporters.json_exporter import JsonExporter
from tg_harvest.exporters.xlsx_exporter import XlsxExporter
from tg_harvest.parsers.channel_parser import ChannelParser
from tg_harvest.storage.state import StateManager
from tg_harvest.utils.date_utils import parse_date

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
@click.option(
    "-i",
    "--incremental",
    is_flag=True,
    default=False,
    help="Only fetch new messages since last parse.",
)
@click.option(
    "--fields",
    default=None,
    help=(
        "Comma-separated list of fields to export. "
        f"Available: {', '.join(ALL_EXPORT_FIELDS)}. "
        "Default: all fields."
    ),
)
def parse(
    channel: str,
    from_date: str | None,
    to_date: str | None,
    limit: int,
    export_format: str,
    output_dir: str | None,
    incremental: bool,
    fields: str | None,
):
    """Parse messages from a Telegram channel or group.

    CHANNEL can be a username (@channel), invite link, or numeric ID.
    """
    # Parse fields option
    field_list = None
    if fields:
        field_list = [f.strip() for f in fields.split(",")]
        invalid = [f for f in field_list if f not in ALL_EXPORT_FIELDS]
        if invalid:
            raise click.BadParameter(
                f"Unknown fields: {', '.join(invalid)}. Available: {', '.join(ALL_EXPORT_FIELDS)}",
                param_hint="--fields",
            )

    asyncio.run(
        _parse_async(
            channel, from_date, to_date, limit, export_format, output_dir, incremental, field_list
        )
    )


async def _parse_async(
    channel: str,
    from_date_str: str | None,
    to_date_str: str | None,
    limit: int,
    export_format: str,
    output_dir: str | None,
    incremental: bool,
    fields: list[str] | None,
):
    settings = Settings()
    out_path = Path(output_dir) if output_dir else settings.output_dir

    from_date = parse_date(from_date_str) if from_date_str else None
    to_date = parse_date(to_date_str) if to_date_str else None

    # Resolve channel identifier
    channel_id: str | int = channel
    if channel.lstrip("-").isdigit():
        channel_id = int(channel)

    # Incremental parsing: load last known message ID
    state = StateManager(settings.state_path)
    min_id = 0

    async with TelegramSession(settings) as session:
        rate_limiter = RateLimiter(delay=settings.request_delay)
        parser = ChannelParser(session.client, rate_limiter)

        # For incremental mode, resolve channel first to get numeric ID
        if incremental:
            info = await parser.get_channel_info(channel_id)
            last_id = state.get_last_id(info.id)
            if last_id:
                min_id = last_id
                console.print(f"[dim]Incremental mode: fetching messages after ID {last_id}[/dim]")

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
                min_id=min_id,
                on_progress=on_progress,
            )

        # Update incremental state
        if result.messages:
            max_msg_id = max(m.id for m in result.messages)
            state.set_last_id(result.channel.id, max_msg_id)

        if not result.messages:
            console.print("[yellow]No messages found for the given criteria.[/yellow]")
            return

        # Export
        output_files: list[str] = []

        if export_format in ("json", "all"):
            path = await JsonExporter(fields).export(result, out_path)
            output_files.append(str(path))

        if export_format in ("csv", "all"):
            path = await CsvExporter(fields).export(result, out_path)
            output_files.append(str(path))

        if export_format in ("xlsx", "all"):
            path = await XlsxExporter(fields).export(result, out_path)
            output_files.append(str(path))

        print_parse_summary(result, output_files)
