"""L5 Economic Guard: In-memory sliding window rate limiter.

Limits requests per user within a configurable time window.
Designed for single-process deployments (Cloud Run instances).
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class RateLimitConfig:
    """Rate limit configuration."""

    max_requests: int = 30
    window_seconds: int = 60


class InMemoryRateLimiter:
    """Async-safe in-memory sliding window rate limiter."""

    def __init__(self, config: RateLimitConfig | None = None) -> None:
        self._config = config or RateLimitConfig()
        self._requests: dict[str, list[float]] = {}
        self._lock = asyncio.Lock()

    async def check(self, user_id: str) -> bool:
        """Check if a request is allowed and record it.

        Returns True if the request is within the rate limit, False otherwise.
        """
        async with self._lock:
            now = time.monotonic()
            self._cleanup_expired(user_id, now)

            timestamps = self._requests.setdefault(user_id, [])
            if len(timestamps) >= self._config.max_requests:
                return False

            timestamps.append(now)
            return True

    async def remaining(self, user_id: str) -> int:
        """Return the number of remaining requests for a user in the current window."""
        async with self._lock:
            now = time.monotonic()
            self._cleanup_expired(user_id, now)
            current = len(self._requests.get(user_id, []))
            return max(0, self._config.max_requests - current)

    def _cleanup_expired(self, user_id: str, now: float) -> None:
        """Remove timestamps outside the current window."""
        if user_id not in self._requests:
            return
        cutoff = now - self._config.window_seconds
        self._requests[user_id] = [t for t in self._requests[user_id] if t > cutoff]
