"""
API Key Authentication Module

Simple authentication using X-API-Key header.
"""
import os
from fastapi import Header, HTTPException, Security
from fastapi.security import APIKeyHeader

API_KEY = os.getenv("AGENT_API_KEY", "change-me-in-production")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(x_api_key: str = Security(api_key_header)) -> str:
    """
    Verify API key from header.
    Returns user_id if valid, raises HTTPException if not.
    """
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Include header: X-API-Key: <your-key>",
        )
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key.",
        )
    return "user-001"  # Map to user_id for rate limiting


def get_api_key() -> str:
    """Get current API key (for admin purposes)."""
    return API_KEY