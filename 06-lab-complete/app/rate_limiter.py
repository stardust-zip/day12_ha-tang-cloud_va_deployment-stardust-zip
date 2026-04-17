"""
Rate Limiter using Redis

Sliding window algorithm for rate limiting.
"""
import os
import time
from fastapi import HTTPException

try:
    import redis
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    r = redis.from_url(REDIS_URL, decode_responses=True)
    r.ping()
    USE_REDIS = True
except Exception:
    USE_REDIS = False


RATE_LIMIT = int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))
WINDOW_SECONDS = 60


def check_rate_limit(user_id: str) -> dict:
    """
    Check if user has exceeded rate limit.
    Raises HTTPException(429) if exceeded.
    Returns rate limit info.
    """
    if not USE_REDIS:
        return {
            "limit": RATE_LIMIT,
            "remaining": RATE_LIMIT,
            "reset_at": int(time.time()) + WINDOW_SECONDS,
        }

    key = f"rate:{user_id}"
    now = time.time()
    window_start = now - WINDOW_SECONDS

    # Remove old timestamps
    r.zremrangebyscore(key, 0, window_start)

    # Count requests in window
    request_count = r.zcard(key)

    if request_count >= RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "limit": RATE_LIMIT,
                "window_seconds": WINDOW_SECONDS,
            },
            headers={
                "X-RateLimit-Limit": str(RATE_LIMIT),
                "X-RateLimit-Remaining": "0",
                "Retry-After": str(WINDOW_SECONDS),
            },
        )

    # Add current request
    r.zadd(key, {str(now): now})
    r.expire(key, WINDOW_SECONDS)

    return {
        "limit": RATE_LIMIT,
        "remaining": RATE_LIMIT - request_count - 1,
        "reset_at": int(now) + WINDOW_SECONDS,
    }