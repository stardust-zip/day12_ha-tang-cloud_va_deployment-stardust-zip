"""
Cost Guard với Redis — Production Ready

Dùng Redis để:
- Scale được khi có nhiều instances
- Data persist qua restart
- Reset hàng tháng tự động
"""
import os
import redis
from datetime import datetime

r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

MONTHLY_BUDGET_USD = float(os.getenv("MONTHLY_BUDGET_USD", "10.0"))


def get_month_key(user_id: str) -> str:
    """Tạo key cho Redis: budget:user_id:2026-04"""
    month_key = datetime.now().strftime("%Y-%m")
    return f"budget:{user_id}:{month_key}"


def check_budget(user_id: str, estimated_cost: float = 0.001) -> bool:
    """
    Return True nếu còn budget, False nếu vượt.

    Args:
        user_id: User identifier
        estimated_cost: Chi phí ước tính cho request này (default $0.001)
    """
    key = get_month_key(user_id)

    current = float(r.get(key) or 0)
    if current + estimated_cost > MONTHLY_BUDGET_USD:
        return False

    r.incrbyfloat(key, estimated_cost)
    r.expire(key, 32 * 24 * 3600)  # 32 days TTL
    return True


def get_budget_usage(user_id: str) -> dict:
    """Lấy thông tin usage hiện tại"""
    key = get_month_key(user_id)
    current = float(r.get(key) or 0)
    return {
        "user_id": user_id,
        "month": datetime.now().strftime("%Y-%m"),
        "used_usd": round(current, 4),
        "budget_usd": MONTHLY_BUDGET_USD,
        "remaining_usd": round(MONTHLY_BUDGET_USD - current, 4),
        "used_pct": round(current / MONTHLY_BUDGET_USD * 100, 1),
    }


def reset_budget(user_id: str) -> bool:
    """Reset budget cho user (dùng cho admin)"""
    key = get_month_key(user_id)
    return r.delete(key) > 0