"""Telegram client session management."""

import logging

from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

from tg_harvest.config.settings import Settings

logger = logging.getLogger(__name__)


class TelegramSession:
    """Wraps TelegramClient with authentication and lifecycle management."""

    def __init__(self, settings: Settings):
        if not settings.api_id or not settings.api_hash:
            raise ValueError(
                "TG_API_ID and TG_API_HASH are required. Set them in .env or environment variables."
            )
        self._settings = settings
        self._client = TelegramClient(
            str(settings.session_path),
            settings.api_id,
            settings.api_hash,
            flood_sleep_threshold=settings.flood_sleep_threshold,
        )

    @property
    def client(self) -> TelegramClient:
        return self._client

    async def connect(self) -> None:
        await self._client.connect()
        logger.debug("Connected to Telegram")

    async def ensure_authorized(self) -> bool:
        """Check if already authorized, return True if yes."""
        if await self._client.is_user_authorized():
            me = await self._client.get_me()
            logger.info("Authorized as %s (id=%d)", me.first_name, me.id)
            return True
        return False

    async def login(self) -> None:
        """Interactive login flow: phone -> code -> optional 2FA."""
        await self.connect()

        if await self.ensure_authorized():
            return

        await self._client.send_code_request(self._settings.phone)
        code = input("Enter the code you received: ")

        try:
            await self._client.sign_in(self._settings.phone, code)
        except SessionPasswordNeededError:
            import getpass

            password = getpass.getpass("Two-factor authentication enabled. Enter your password: ")
            await self._client.sign_in(password=password)

        me = await self._client.get_me()
        logger.info("Logged in as %s (id=%d)", me.first_name, me.id)

    async def logout(self) -> None:
        await self.connect()
        await self._client.log_out()
        logger.info("Logged out successfully")

    async def disconnect(self) -> None:
        if self._client.is_connected():
            await self._client.disconnect()

    async def __aenter__(self) -> "TelegramSession":
        await self.connect()
        if not await self.ensure_authorized():
            await self.login()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.disconnect()
