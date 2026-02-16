"""Async rate limiter for Telegram API requests."""

import asyncio
import time


class RateLimiter:
    """Simple async rate limiter with configurable delay between requests."""

    def __init__(self, delay: float = 1.0):
        self._delay = delay
        self._last_request = 0.0
        self._lock = asyncio.Lock()

    async def wait(self) -> None:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_request
            if elapsed < self._delay:
                await asyncio.sleep(self._delay - elapsed)
            self._last_request = time.monotonic()
