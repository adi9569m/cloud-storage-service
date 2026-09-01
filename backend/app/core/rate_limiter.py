"""In-memory sliding-window rate limiter for protecting endpoints against brute-force and abuse."""

from collections import defaultdict
from datetime import datetime, timezone
import time
from typing import Callable, Dict, List
from fastapi import HTTPException, Request, status
from app.core.config import settings


class InMemoryRateLimiter:
    """Sliding-window in-memory rate limiter tracking client IP hit timestamps."""

    def __init__(self) -> None:
        self._records: Dict[str, List[float]] = defaultdict(list)

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """Check if key has made fewer than max_requests in the past window_seconds."""
        now = time.time()
        window_start = now - window_seconds

        # Clean older records
        valid_timestamps = [ts for ts in self._records[key] if ts > window_start]
        self._records[key] = valid_timestamps

        if len(valid_timestamps) >= max_requests:
            return False

        self._records[key].append(now)
        return True

    def reset(self) -> None:
        """Clear all rate limit state (useful in test teardown)."""
        self._records.clear()


limiter = InMemoryRateLimiter()


def check_rate_limit(max_requests: int = 60, window_seconds: int = 60) -> Callable:
    """FastAPI route dependency factory for rate limiting."""

    async def rate_limit_dependency(request: Request) -> None:
        if not settings.RATE_LIMIT_ENABLED:
            return

        client_ip = request.client.host if request.client else "unknown"
        endpoint = request.url.path
        key = f"{client_ip}:{endpoint}"

        if not limiter.is_allowed(key, max_requests=max_requests, window_seconds=window_seconds):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many requests. Limit is {max_requests} requests per {window_seconds}s.",
                headers={"Retry-After": str(window_seconds)},
            )

    return rate_limit_dependency
