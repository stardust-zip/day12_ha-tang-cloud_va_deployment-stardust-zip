"""
Cost Guard using Redis

Track usage and prevent exceeding budget.
"""
import os
import time
from datetime import datetime
from fastapi import HTTPException

try:
    import redis
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    r = redis.from_url(REDIS_URL, decode_responses=True)
    r.ping()
    USE_REDIS = True
except Exception:
    USE_REDIS = False

MONTHLY_BUDGET_USD = float(os.getenv("MONTHLY_BUDGET_USD", "10.0"))


def get_month_key(user_id: str) -> str:
    """Generate Redis key for user's monthly budget."""
    month_key = datetime.now().strftime("%Y-%m")
    return f"budget:{user_id}:{month_key}"


def check_budget(user_id: str, estimated_cost: float = 0.001) -> dict:
    """
    Check if user has remaining budget.
    Raises HTTPException(402) if exceeded.
    Returns budget info.
    """
    if not USE_REDIS:
        return {
            "used_usd": 0.0,
            "budget_usd": MONTHLY_BUDGET_USD,
            "remaining_usd": MONTHLY_BUDGET_USD,
        }

    key = get_month_key(user_id)
    current = float(r.get(key) or 0)

    if current + estimated_cost > MONTHLY_BUDGET_USD:
        raise HTTPException(
            status_code=402,
            detail={
                "error": "Monthly budget exceeded",
                "used_usd": round(current, 4),
                "budget_usd": MONTHLY_BUDGET_USD,
            },
        )

    # Increment budget
    r.incrbyfloat(key, estimated_cost)
    r.expire(key, 32 * 24 * 3600)  # 32 days TTL

    remaining = MONTHLY_BUDGET_USD - current - estimated_cost
    return {
        "used_usd": round(current + estimated_cost, 4),
        "budget_usd": MONTHLY_BUDGET_USD,
        "remaining_usd": round(remaining, 4),
    }


def get_usage(user_id: str) -> dict:
    """Get current usage for user."""
    if not USE_REDIS:
        return {
            "user_id": user_id,
            "month": datetime.now().strftime("%Y-%m"),
            "used_usd": 0.0,
            "budget_usd": MONTHLY_BUDGET_USD,
            "remaining_usd": MONTHLY_BUDGET_USD,
        }

    key = get_month_key(user_id)
    current = float(r.get(key) or 0)

    return {
        "user_id": user_id,
        "month": datetime.now().strftime("%Y-%m"),
        "used_usd": round(current, 4),
        "budget_usd": MONTHLY_BUDGET_USD,
        "remaining_usd": round(MONTHLY_BUDGET_USD - current, 4),
    }