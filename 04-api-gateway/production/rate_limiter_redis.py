"""
Rate Limiter với Redis — Production Ready

Dùng Redis để:
- Scale được khi có nhiều instances
- Share state giữa các instances
- Sliding window algorithm
"""
import os
import time
import redis
from fastapi import HTTPException

r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

RATE_LIMIT = int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))
WINDOW_SECONDS = 60


def check_rate_limit(user_id: str) -> dict:
    """
    Kiểm tra rate limit cho user.
    Return info nếu OK, raise 429 nếu vượt limit.
    """
    key = f"rate:{user_id}"
    now = time.time()
    window_start = now - WINDOW_SECONDS

    pipe = r.pipeline()
    
    # Remove old timestamps
    pipe.zremrangebyscore(key, 0, window_start)
    
    # Count requests in window
    pipe.zcard(key)
    
    # Add current request
    pipe.zadd(key, {str(now): now})
    
    # Set expiry
    pipe.expire(key, WINDOW_SECONDS)
    
    results = pipe.execute()
    request_count = results[1]

    if request_count > RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "limit": RATE_LIMIT,
                "window_seconds": WINDOW_SECONDS,
                "retry_after": WINDOW_SECONDS,
            },
            headers={
                "X-RateLimit-Limit": str(RATE_LIMIT),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(now) + WINDOW_SECONDS),
                "Retry-After": str(WINDOW_SECONDS),
            },
        )

    return {
        "limit": RATE_LIMIT,
        "remaining": RATE_LIMIT - request_count,
        "reset_at": int(now) + WINDOW_SECONDS,
    }


def get_rate_limit_stats(user_id: str) -> dict:
    """Lấy stats của user"""
    key = f"rate:{user_id}"
    now = time.time()
    window_start = now - WINDOW_SECONDS
    
    r.zremrangebyscore(key, 0, window_start)
    count = r.zcard(key)
    
    return {
        "requests_in_window": count,
        "limit": RATE_LIMIT,
        "remaining": max(0, RATE_LIMIT - count),
    }


def reset_rate_limit(user_id: str) -> bool:
    """Reset rate limit cho user (dùng cho admin)"""
    key = f"rate:{user_id}"
    return r.delete(key) > 0