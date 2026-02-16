"""Tests for rate limiter."""

import asyncio
import time

import pytest

from tg_harvest.client.rate_limiter import RateLimiter


class TestRateLimiter:
    @pytest.mark.asyncio
    async def test_first_call_no_delay(self):
        limiter = RateLimiter(delay=1.0)
        start = time.monotonic()
        await limiter.wait()
        elapsed = time.monotonic() - start
        assert elapsed < 0.1

    @pytest.mark.asyncio
    async def test_second_call_has_delay(self):
        limiter = RateLimiter(delay=0.2)
        await limiter.wait()
        start = time.monotonic()
        await limiter.wait()
        elapsed = time.monotonic() - start
        assert elapsed >= 0.15  # allow small tolerance

    @pytest.mark.asyncio
    async def test_delay_respects_setting(self):
        limiter = RateLimiter(delay=0.3)
        await limiter.wait()
        start = time.monotonic()
        await limiter.wait()
        elapsed = time.monotonic() - start
        assert 0.25 <= elapsed <= 0.5

    @pytest.mark.asyncio
    async def test_no_delay_after_enough_time(self):
        limiter = RateLimiter(delay=0.1)
        await limiter.wait()
        await asyncio.sleep(0.15)
        start = time.monotonic()
        await limiter.wait()
        elapsed = time.monotonic() - start
        assert elapsed < 0.05

    @pytest.mark.asyncio
    async def test_zero_delay(self):
        limiter = RateLimiter(delay=0.0)
        start = time.monotonic()
        for _ in range(10):
            await limiter.wait()
        elapsed = time.monotonic() - start
        assert elapsed < 0.1
