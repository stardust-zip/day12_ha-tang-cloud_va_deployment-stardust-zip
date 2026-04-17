"""
Production AI Agent — Full Security Stack

Features:
- API Key authentication
- JWT authentication  
- Rate limiting (Redis)
- Cost guard (Redis)

Test:
    # Test auth
    curl http://localhost:8000/ask -X POST \
        -H "X-API-Key: secret-key-123" \
        -d '{"question": "Hello"}'

    # Test rate limit
    for i in {1..15}; do
        curl http://localhost:8000/ask -X POST \
            -H "X-API-Key: secret-key-123" \
            -d '{"question": "Test '$i'"}'
    done
"""
import os
from fastapi import FastAPI, HTTPException, Header, Depends
from contextlib import asynccontextmanager
import uvicorn

from auth import verify_token, authenticate_user, create_token
from rate_limiter_redis import check_rate_limit as check_redis_rate_limit
from cost_guard_redis import check_budget as check_redis_budget

from utils.mock_llm import ask


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting AI Agent with full security stack...")
    print(f"Rate limit: {os.getenv('RATE_LIMIT_PER_MINUTE', '10')}/min")
    print(f"Monthly budget: ${os.getenv('MONTHLY_BUDGET_USD', '10')}")
    yield
    print("Shutting down...")


app = FastAPI(title="Secure AI Agent", lifespan=lifespan)

API_KEY = os.getenv("AGENT_API_KEY", "secret-key-123")


def verify_api_key(x_api_key: str = Header(...)) -> str:
    """Simple API key verification - returns user_id"""
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return "user-001"  # Map API key to user_id for rate limiting


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/token")
def get_token(username: str, password: str):
    """Get JWT token"""
    user = authenticate_user(username, password)
    token = create_token(user["username"], user["role"])
    return {"access_token": token, "token_type": "bearer"}


@app.post("/ask")
def ask_agent(
    question: str,
    user_id: str = Depends(verify_api_key),
):
    """
    Protected endpoint with:
    1. API Key auth
    2. Rate limiting
    3. Cost guard
    """
    try:
        rate_info = check_redis_rate_limit(user_id)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Rate limit check failed: {e}")

    if not check_redis_budget(user_id, estimated_cost=0.001):
        raise HTTPException(
            status_code=402,
            detail={
                "error": "Monthly budget exceeded",
                "budget_usd": float(os.getenv("MONTHLY_BUDGET_USD", "10")),
            },
        )

    answer = ask(question)
    return {"question": question, "answer": answer, "user_id": user_id}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)