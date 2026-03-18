"""Tests for the rate limiter."""

from __future__ import annotations

import time
from unittest.mock import patch

import pytest

from app.guardrails.system.rate_limiter import InMemoryRateLimiter, RateLimitConfig


class TestRateLimitConfig:
    def test_default_values(self) -> None:
        config = RateLimitConfig()
        assert config.max_requests == 30
        assert config.window_seconds == 60

    def test_custom_values(self) -> None:
        config = RateLimitConfig(max_requests=5, window_seconds=10)
        assert config.max_requests == 5
        assert config.window_seconds == 10


class TestInMemoryRateLimiter:
    @pytest.mark.asyncio
    async def test_allows_under_limit(self) -> None:
        limiter = InMemoryRateLimiter(RateLimitConfig(max_requests=5, window_seconds=60))
        for _ in range(5):
            assert await limiter.check("user-1") is True

    @pytest.mark.asyncio
    async def test_blocks_over_limit(self) -> None:
        limiter = InMemoryRateLimiter(RateLimitConfig(max_requests=3, window_seconds=60))
        for _ in range(3):
            await limiter.check("user-1")
        assert await limiter.check("user-1") is False

    @pytest.mark.asyncio
    async def test_independent_users(self) -> None:
        limiter = InMemoryRateLimiter(RateLimitConfig(max_requests=2, window_seconds=60))
        assert await limiter.check("user-1") is True
        assert await limiter.check("user-1") is True
        assert await limiter.check("user-1") is False
        # Different user still has budget
        assert await limiter.check("user-2") is True

    @pytest.mark.asyncio
    async def test_window_expiry(self) -> None:
        limiter = InMemoryRateLimiter(RateLimitConfig(max_requests=2, window_seconds=1))
        assert await limiter.check("user-1") is True
        assert await limiter.check("user-1") is True
        assert await limiter.check("user-1") is False

        # Simulate time passing beyond the window
        future = time.monotonic() + 2
        with patch(
            "app.guardrails.system.rate_limiter.time.monotonic",
            return_value=future,
        ):
            assert await limiter.check("user-1") is True

    @pytest.mark.asyncio
    async def test_remaining_returns_correct_count(self) -> None:
        limiter = InMemoryRateLimiter(RateLimitConfig(max_requests=5, window_seconds=60))
        assert await limiter.remaining("user-1") == 5
        await limiter.check("user-1")
        assert await limiter.remaining("user-1") == 4
