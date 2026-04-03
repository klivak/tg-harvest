"""Main parse command."""

import asyncio
from datetime import datetime
from pathlib import Path

import click
from rich.console import Console
from rich.progress import BarColumn, MofNCompleteColumn, Progress, TextColumn, TimeElapsedColumn

from tg_harvest.cli.formatters import print_parse_summary, print_queue_summary
from tg_harvest.client.rate_limiter import RateLimiter
from tg_harvest.client.session import TelegramSession
from tg_harvest.config import Settings
from tg_harvest.config.constants import (
    ALL_EXPORT_FIELDS,
    DEFAULT_EXPORT_FORMAT,
    DEFAULT_MAX_MEDIA_SIZE_MB,
    SUPPORTED_FORMATS,
)
from tg_harvest.exporters.csv_exporter import CsvExporter
from tg_harvest.exporters.html_exporter import HtmlExporter
from tg_harvest.exporters.json_exporter import JsonExporter
from tg_harvest.exporters.xlsx_exporter import XlsxExporter
from tg_harvest.parsers.channel_parser import ChannelParser
from tg_harvest.parsers.parse_options import ParseOptions
from tg_harvest.storage.state import StateManager
from tg_harvest.utils.date_utils import parse_date

console = Console()


@click.command()
@click.argument("channels", nargs=-1, required=True)
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
@click.option(
    "--download-media",
    is_flag=True,
    default=False,
    help="Download media files (photos, videos, documents) during parsing.",
)
@click.option(
    "--max-media-size",
    default=DEFAULT_MAX_MEDIA_SIZE_MB,
    type=int,
    help="Max media file size in MB (0 = no limit).",
    show_default=True,
)
@click.option(
    "--media-dir",
    default=None,
    type=click.Path(),
    help="Directory for downloaded media (default: output/media/<channel>).",
)
@click.option(
    "--fetch-replies",
    is_flag=True,
    default=False,
    help="Fetch full reply thread messages (extra API calls).",
)
@click.option(
    "--enrich-senders",
    is_flag=True,
    default=False,
    help="Resolve sender IDs to usernames and names.",
)
@click.option(
    "--split-parts",
    default=1,
    type=click.IntRange(1, 20),
    help="Split output into N parts (1-20).",
    show_default=True,
)
def parse(
    channels: tuple[str, ...],
    from_date: str | None,
    to_date: str | None,
    limit: int,
    export_format: str,
    output_dir: str | None,
    incremental: bool,
    fields: str | None,
    download_media: bool,
    max_media_size: int,
    media_dir: str | None,
    fetch_replies: bool,
    enrich_senders: bool,
    split_parts: int,
):
    """Parse messages from Telegram channels, groups, bots, or private chats.

    CHANNELS can be one or more usernames (@channel), invite links, or numeric IDs.
    When multiple channels are given, they are parsed sequentially (queue mode)
    and each channel's output is saved to a separate subfolder.
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

    options = ParseOptions(
        download_media=download_media,
        max_media_size_mb=max_media_size,
        media_output_dir=Path(media_dir) if media_dir else None,
        fetch_replies=fetch_replies,
        enrich_senders=enrich_senders,
    )

    asyncio.run(
        _parse_async(
            channels,
            from_date,
            to_date,
            limit,
            export_format,
            output_dir,
            incremental,
            field_list,
            options,
            split_parts,
        )
    )


async def _parse_async(
    channels: tuple[str, ...],
    from_date_str: str | None,
    to_date_str: str | None,
    limit: int,
    export_format: str,
    output_dir: str | None,
    incremental: bool,
    fields: list[str] | None,
    options: ParseOptions,
    split_parts: int = 1,
):
    settings = Settings()
    # Reject path traversal
    if output_dir and ".." in Path(output_dir).parts:
        raise click.BadParameter(
            "Output directory must not contain '..' path components.",
            param_hint="-o/--output",
        )
    out_path = Path(output_dir).resolve() if output_dir else settings.output_dir.resolve()

    # Create date-stamped session folder
    session_dir = out_path / datetime.now().strftime("%Y-%m-%d_%H%M%S")
    session_dir.mkdir(parents=True, exist_ok=True)

    from_date = parse_date(from_date_str) if from_date_str else None
    to_date = parse_date(to_date_str) if to_date_str else None

    multi = len(channels) > 1
    state = StateManager(settings.state_path)

    # Queue header
    if multi:
        console.print(f"\n[bold]Queue: {len(channels)} channels[/bold]")
        for i, ch in enumerate(channels, 1):
            console.print(f"  {i}. {ch}")
        console.print()

    results: list[tuple[str, object, list[str]]] = []  # (channel, result, files)
    errors: list[tuple[str, str]] = []  # (channel, error)

    async with TelegramSession(settings) as session:
        rate_limiter = RateLimiter(delay=settings.request_delay)
        parser = ChannelParser(session.client, rate_limiter)

        for ch_idx, channel in enumerate(channels, 1):
            if multi:
                console.print(
                    f"\n[bold cyan]━━━ [{ch_idx}/{len(channels)}] {channel} ━━━[/bold cyan]"
                )

            try:
                channel_result, channel_files = await _parse_single(
                    parser=parser,
                    channel=channel,
                    from_date=from_date,
                    to_date=to_date,
                    limit=limit,
                    export_format=export_format,
                    out_path=session_dir,
                    incremental=incremental,
                    fields=fields,
                    options=options,
                    split_parts=split_parts,
                    state=state,
                    use_subfolder=multi,
                )
                if channel_result:
                    results.append((channel, channel_result, channel_files))
            except Exception as e:
                errors.append((channel, str(e)))
                console.print(f"[red]Error parsing {channel}: {e}[/red]")
                if not multi:
                    raise

    # Queue summary
    if multi:
        print_queue_summary(results, errors)


async def _parse_single(
    parser: ChannelParser,
    channel: str,
    from_date,
    to_date,
    limit: int,
    export_format: str,
    out_path: Path,
    incremental: bool,
    fields: list[str] | None,
    options: ParseOptions,
    split_parts: int,
    state: StateManager,
    use_subfolder: bool,
):
    """Parse a single channel and export results."""
    # Resolve channel identifier
    channel_id: str | int = channel
    if channel.lstrip("-").isdigit():
        channel_id = int(channel)

    min_id = 0

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
            options=options,
        )

    # Update incremental state
    if result.messages:
        max_msg_id = max(m.id for m in result.messages)
        state.set_last_id(result.channel.id, max_msg_id)

    if not result.messages:
        console.print("[yellow]No messages found for the given criteria.[/yellow]")
        return None, []

    # Show download stats
    if result.download_stats and result.download_stats.total_files > 0:
        ds = result.download_stats
        size_mb = ds.total_bytes / 1024 / 1024
        console.print(f"[green]Downloaded {ds.total_files} media files ({size_mb:.1f} MB)[/green]")
        if ds.skipped_size_limit:
            console.print(f"[dim]Skipped {ds.skipped_size_limit} files (size limit)[/dim]")
        if ds.skipped_existing:
            console.print(f"[dim]Skipped {ds.skipped_existing} files (already exist)[/dim]")
        if ds.failed:
            console.print(f"[yellow]Failed to download {ds.failed} files[/yellow]")

    # Per-channel subfolder when multiple channels
    channel_out = out_path
    if use_subfolder:
        folder_name = result.channel.username or str(result.channel.id)
        # Sanitize folder name
        folder_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in folder_name)
        channel_out = out_path / folder_name
        channel_out.mkdir(parents=True, exist_ok=True)

    # Export (with optional split)
    from tg_harvest.exporters.splitter import (
        make_part_result,
        make_part_suffix,
        split_messages,
    )

    chunks = split_messages(result.messages, split_parts)
    total_parts = len(chunks)
    output_files: list[str] = []

    for part_idx, chunk in enumerate(chunks, 1):
        suffix = make_part_suffix(part_idx, total_parts)
        part = make_part_result(result, chunk) if total_parts > 1 else result

        if export_format in ("json", "all"):
            path = await JsonExporter(fields).export(part, channel_out, suffix)
            output_files.append(str(path))
        if export_format in ("csv", "all"):
            path = await CsvExporter(fields).export(part, channel_out, suffix)
            output_files.append(str(path))
        if export_format in ("xlsx", "all"):
            path = await XlsxExporter(fields).export(part, channel_out, suffix)
            output_files.append(str(path))
        if export_format in ("html", "all"):
            path = await HtmlExporter(fields).export(part, channel_out, suffix)
            output_files.append(str(path))

    print_parse_summary(result, output_files)
    return result, output_files
