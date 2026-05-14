import pytest

from app.services.rate_limiter import RateLimiter


def test_rate_limiter_allows_under_limit():
    limiter = RateLimiter(max_requests=3, window_seconds=60)
    # Should not raise
    limiter.check("user1")
    limiter.check("user1")
    limiter.check("user1")


def test_rate_limiter_blocks_over_limit():
    from fastapi import HTTPException

    limiter = RateLimiter(max_requests=3, window_seconds=60)
    limiter.check("user1")
    limiter.check("user1")
    limiter.check("user1")
    with pytest.raises(HTTPException) as exc_info:
        limiter.check("user1")
    assert exc_info.value.status_code == 429


def test_rate_limiter_different_users():
    limiter = RateLimiter(max_requests=2, window_seconds=60)
    limiter.check("user1")
    limiter.check("user1")
    # user2 should still be fine
    limiter.check("user2")


def test_rate_limiter_window_reset():
    import time

    limiter = RateLimiter(max_requests=2, window_seconds=1)
    limiter.check("user1")
    limiter.check("user1")
    # Wait for window to expire
    time.sleep(1.1)
    # Should be allowed again
    limiter.check("user1")
