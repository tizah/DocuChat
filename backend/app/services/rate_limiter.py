import time

from app.config import settings
from app.exceptions import RateLimitError


class RateLimiter:
    """In-memory sliding window rate limiter."""

    def __init__(self, max_requests: int, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = {}

    def check(self, user_id: str) -> None:
        now = time.time()
        cutoff = now - self.window_seconds

        timestamps = self._requests.get(user_id, [])
        # Prune old timestamps
        timestamps = [t for t in timestamps if t > cutoff]

        if len(timestamps) >= self.max_requests:
            raise RateLimitError()

        timestamps.append(now)
        self._requests[user_id] = timestamps


chat_rate_limiter = RateLimiter(max_requests=settings.chat_rate_limit)
