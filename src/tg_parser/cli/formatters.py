"""Rich formatting helpers for CLI output."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from tg_parser.models.channel import ChannelInfo
from tg_parser.models.parse_result import ParseResult

console = Console()


def print_channel_table(channels: list[ChannelInfo]) -> None:
    table = Table(title="Accessible Channels & Groups")
    table.add_column("ID", style="dim")
    table.add_column("Title", style="bold")
    table.add_column("Username")
    table.add_column("Type")
    table.add_column("Members", justify="right")
    table.add_column("Restricted", justify="center")

    for ch in channels:
        ch_type = "Group" if ch.is_group else "Channel"
        username = f"@{ch.username}" if ch.username else "private"
        members = str(ch.members_count) if ch.members_count else "-"
        restricted = "Yes" if ch.restricted else ""

        table.add_row(
            str(ch.id),
            ch.title,
            username,
            ch_type,
            members,
            restricted,
        )

    console.print(table)


def print_parse_summary(result: ParseResult, output_files: list[str]) -> None:
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="bold")
    table.add_column("Value")

    table.add_row("Channel", result.channel.title)
    table.add_row("Messages parsed", str(result.total_messages))

    if result.from_date:
        table.add_row("From", result.from_date.strftime("%Y-%m-%d %H:%M"))
    if result.to_date:
        table.add_row("To", result.to_date.strftime("%Y-%m-%d %H:%M"))

    if result.messages:
        oldest = min(m.date for m in result.messages)
        newest = max(m.date for m in result.messages)
        table.add_row("Oldest message", oldest.strftime("%Y-%m-%d %H:%M"))
        table.add_row("Newest message", newest.strftime("%Y-%m-%d %H:%M"))

    for path in output_files:
        table.add_row("Saved to", path)

    panel = Panel(table, title="Parse Complete", border_style="green")
    console.print(panel)
