"""Search command."""

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from tg_harvest.config import Settings
from tg_harvest.models.media import MediaType
from tg_harvest.search.engine import SearchEngine, SearchFilters

console = Console()


@click.command()
@click.argument("query")
@click.option("--channel", default=None, help="Filter by channel username or ID.")
@click.option("--media-type", default=None, help="Filter by media type (photo, video, etc.).")
@click.option("--min-views", default=None, type=int, help="Minimum views count.")
@click.option("--from-date", default=None, help="Start date (YYYY-MM-DD).")
@click.option("--to-date", default=None, help="End date (YYYY-MM-DD).")
@click.option("--has-reactions", is_flag=True, default=False, help="Only messages with reactions.")
@click.option("-n", "--max-results", default=50, help="Max results to show.", show_default=True)
@click.option(
    "-o",
    "--output-dir",
    type=click.Path(),
    default=None,
    help="Output directory to search in.",
)
def search(
    query: str,
    channel: str | None,
    media_type: str | None,
    min_views: int | None,
    from_date: str | None,
    to_date: str | None,
    has_reactions: bool,
    max_results: int,
    output_dir: str | None,
):
    """Search across parsed messages.

    QUERY is the text to search for in message content.
    """
    settings = Settings()
    out_path = Path(output_dir) if output_dir else settings.output_dir

    engine = SearchEngine()
    results = engine.load_results(out_path)

    if not results:
        console.print("[yellow]No parsed data found. Run 'tg-harvest parse' first.[/yellow]")
        return

    channel_id = None
    if channel:
        if channel.lstrip("-").isdigit():
            channel_id = int(channel)

    media = None
    if media_type:
        try:
            media = MediaType(media_type)
        except ValueError:
            console.print(f"[red]Invalid media type: {media_type}[/red]")
            return

    filters = SearchFilters(
        keyword=query,
        media_type=media,
        has_reactions=True if has_reactions else None,
        min_views=min_views,
        date_from=from_date,
        date_to=to_date,
        channel_id=channel_id,
    )

    matches = engine.search(results, filters)

    if not matches:
        console.print("[yellow]No messages found matching your query.[/yellow]")
        return

    console.print(f"[green]Found {len(matches)} matching messages[/green]\n")

    table = Table(title=f"Search: '{query}'")
    table.add_column("Channel", style="bold", max_width=20)
    table.add_column("Date", style="dim")
    table.add_column("ID", style="dim", justify="right")
    table.add_column("Text", max_width=60)
    table.add_column("Views", justify="right")
    table.add_column("Reactions", justify="right")

    for match in matches[:max_results]:
        msg = match.message
        text = msg.text[:80] + "..." if len(msg.text) > 80 else msg.text
        text = text.replace("\n", " ")
        views = str(msg.views) if msg.views else "-"
        reactions = str(msg.reactions.total) if msg.reactions else "-"
        ch_name = match.channel_username or match.channel_title[:15]

        table.add_row(
            ch_name,
            msg.date.strftime("%Y-%m-%d %H:%M"),
            str(msg.id),
            text,
            views,
            reactions,
        )

    console.print(table)

    if len(matches) > max_results:
        console.print(
            f"\n[dim]Showing {max_results} of {len(matches)} results. Use -n to see more.[/dim]"
        )
