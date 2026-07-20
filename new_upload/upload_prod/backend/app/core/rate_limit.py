"""Anti-abuse helpers for public, unauthenticated endpoints.

- rate_limit(): per-IP fixed-window limiter backed by Redis. No-ops gracefully when
  Redis is disabled (so dev/local still works) and never blocks a request because the
  limiter itself errored.
- verify_captcha(): optional hCaptcha/reCAPTCHA verification — a no-op (returns True)
  unless CAPTCHA_SECRET is configured.
"""
from __future__ import annotations

from typing import Optional

import httpx
from fastapi import HTTPException, Request, status

from app.core.config import settings
from app.core.dependencies import redis_client


def _client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for", "")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit(prefix: str, limit: int, window_seconds: int):
    """FastAPI dependency factory: allow at most `limit` requests per IP per window."""
    async def _dep(request: Request):
        if redis_client is None:
            return  # limiter disabled (Redis off) — degrade gracefully
        key = f"rl:{prefix}:{_client_ip(request)}"
        try:
            current = await redis_client.incr(key)
            if current == 1:
                await redis_client.expire(key, window_seconds)
            if current > limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests. Please try again later.",
                )
        except HTTPException:
            raise
        except Exception:
            return  # never fail a request because the limiter broke
    return _dep


_CAPTCHA_URLS = {
    "hcaptcha": "https://hcaptcha.com/siteverify",
    "recaptcha": "https://www.google.com/recaptcha/api/siteverify",
}


async def verify_captcha(token: Optional[str]) -> bool:
    """Verify a CAPTCHA token. Returns True when CAPTCHA is not configured."""
    if not settings.CAPTCHA_SECRET:
        return True
    if not token:
        return False
    url = _CAPTCHA_URLS.get(settings.CAPTCHA_PROVIDER, _CAPTCHA_URLS["hcaptcha"])
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, data={"secret": settings.CAPTCHA_SECRET, "response": token})
        return bool(resp.json().get("success"))
    except Exception:
        return False
