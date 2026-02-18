"""Authentication commands."""

import asyncio

import click
from rich.console import Console

from tg_harvest.client.session import TelegramSession
from tg_harvest.config import Settings

console = Console()


@click.group()
def auth():
    """Manage Telegram authentication."""


@auth.command()
def login():
    """Log in to Telegram (interactive)."""

    async def _login():
        settings = Settings()
        session = TelegramSession(settings)
        try:
            await session.login()
            console.print("[green]Successfully logged in![/green]")
        finally:
            await session.disconnect()

    asyncio.run(_login())


@auth.command()
def status():
    """Check current authentication status."""

    async def _status():
        settings = Settings()
        session = TelegramSession(settings)
        try:
            await session.connect()
            if await session.ensure_authorized():
                me = await session.client.get_me()
                console.print(f"[green]Authenticated as:[/green] {me.first_name} (id={me.id})")
                if me.username:
                    console.print(f"[dim]Username:[/dim] @{me.username}")
                if me.phone:
                    phone = me.phone
                    masked = f"+{phone[:3]}***{phone[-4:]}" if len(phone) >= 7 else "+***"
                    console.print(f"[dim]Phone:[/dim] {masked}")
            else:
                console.print("[yellow]Not authenticated. Run:[/yellow] tg-harvest auth login")
        finally:
            await session.disconnect()

    asyncio.run(_status())


@auth.command()
def logout():
    """Log out and delete session."""

    async def _logout():
        settings = Settings()
        session = TelegramSession(settings)
        try:
            await session.logout()
            console.print("[green]Logged out successfully.[/green]")
        except Exception as e:
            console.print(f"[red]Logout error: {e}[/red]")
        finally:
            await session.disconnect()

    asyncio.run(_logout())
