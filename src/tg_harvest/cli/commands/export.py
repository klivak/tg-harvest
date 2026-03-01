"""Re-export parsed JSON files to other formats."""

import asyncio
import json
from pathlib import Path

import click
from rich.console import Console

from tg_harvest.config.constants import ALL_EXPORT_FIELDS

console = Console()

EXPORT_FORMATS = ("csv", "xlsx", "html", "all")


@click.command()
@click.argument("input_path", type=click.Path(exists=True))
@click.option(
    "--format",
    "export_format",
    type=click.Choice(EXPORT_FORMATS, case_sensitive=False),
    default="csv",
    help="Target export format.",
    show_default=True,
)
@click.option(
    "-o",
    "--output",
    "output_dir",
    type=click.Path(),
    default=None,
    help="Output directory (default: same as input file).",
)
@click.option(
    "--fields",
    default=None,
    help=f"Comma-separated fields. Available: {', '.join(ALL_EXPORT_FIELDS)}.",
)
def export(input_path: str, export_format: str, output_dir: str | None, fields: str | None):
    """Re-export parsed JSON to CSV, XLSX, or HTML.

    INPUT_PATH is a JSON file or directory of JSON files produced by 'tg-harvest parse'.
    """
    field_list = None
    if fields:
        field_list = [f.strip() for f in fields.split(",")]
        invalid = [f for f in field_list if f not in ALL_EXPORT_FIELDS]
        if invalid:
            raise click.BadParameter(f"Unknown fields: {', '.join(invalid)}", param_hint="--fields")

    asyncio.run(_export_async(input_path, export_format, output_dir, field_list))


async def _export_async(
    input_path: str,
    export_format: str,
    output_dir: str | None,
    fields: list[str] | None,
):
    from tg_harvest.exporters.csv_exporter import CsvExporter
    from tg_harvest.exporters.html_exporter import HtmlExporter
    from tg_harvest.exporters.xlsx_exporter import XlsxExporter
    from tg_harvest.models.parse_result import ParseResult

    path = Path(input_path)
    json_files: list[Path] = []

    if path.is_file() and path.suffix == ".json":
        json_files.append(path)
    elif path.is_dir():
        json_files = sorted(path.glob("*.json"))
    else:
        console.print("[red]Input must be a JSON file or directory containing JSON files.[/red]")
        return

    if not json_files:
        console.print("[yellow]No JSON files found.[/yellow]")
        return

    for json_file in json_files:
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
            result = ParseResult.model_validate(data)
        except Exception as e:
            console.print(f"[red]Failed to load {json_file.name}: {e}[/red]")
            continue

        out_path = Path(output_dir).resolve() if output_dir else json_file.parent

        output_files: list[str] = []
        if export_format in ("csv", "all"):
            p = await CsvExporter(fields).export(result, out_path)
            output_files.append(str(p))
        if export_format in ("xlsx", "all"):
            p = await XlsxExporter(fields).export(result, out_path)
            output_files.append(str(p))
        if export_format in ("html", "all"):
            p = await HtmlExporter(fields).export(result, out_path)
            output_files.append(str(p))

        for f in output_files:
            console.print(f"[green]Exported:[/green] {f}")
