"""Web UI command."""

import subprocess
import sys
from pathlib import Path

import click
from rich.console import Console

from tg_harvest.config import Settings
from tg_harvest.config.constants import DEFAULT_WEB_PORT

console = Console()


@click.command()
@click.option(
    "-p",
    "--port",
    default=None,
    type=int,
    help=f"Port to run on (default: {DEFAULT_WEB_PORT}).",
)
def web(port: int | None):
    """Start the Streamlit web interface."""
    settings = Settings()
    actual_port = port or settings.web_port

    app_path = Path(__file__).resolve().parent.parent.parent / "web" / "app.py"

    console.print(f"[bold green]Starting web UI on port {actual_port}[/bold green]")
    console.print(f"[dim]Open http://localhost:{actual_port} in your browser[/dim]")

    subprocess.run(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(app_path),
            "--server.port",
            str(actual_port),
            "--server.headless",
            "true",
            "--browser.gatherUsageStats",
            "false",
        ],
        check=False,
    )
