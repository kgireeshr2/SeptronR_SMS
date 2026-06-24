"""Razorpay payment gateway integration.

Per-school keys are read from the Settings 'fees' category
(razorpay_key_id / razorpay_key_secret / razorpay_webhook_secret) with a global
.env fallback. All money is in paise (integer), matching the fee ledger.

Security model:
  - Orders are created server-side; the amount is set by the server (from the
    invoice), never trusted from the client.
  - The checkout callback signature is verified (HMAC-SHA256 of "order_id|payment_id").
  - The webhook signature is verified (HMAC-SHA256 of the raw body) — this is the
    authoritative confirmation path.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
from typing import Any, Dict, Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.repositories.settings_repository import SettingsRepository

RAZORPAY_BASE = "https://api.razorpay.com/v1"


async def resolve_config(db: AsyncSession, school_id: Optional[str]) -> Dict[str, str]:
    """Per-school Razorpay credentials (Settings 'fees') over global env fallback."""
    key_id = settings.RAZORPAY_KEY_ID or ""
    key_secret = settings.RAZORPAY_KEY_SECRET or ""
    webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET or ""
    if school_id:
        try:
            kv = await SettingsRepository(db).get_as_dict(school_id, "fees")
            key_id = kv.get("razorpay_key_id") or key_id
            key_secret = kv.get("razorpay_key_secret") or key_secret
            webhook_secret = kv.get("razorpay_webhook_secret") or webhook_secret
        except Exception:
            pass
    return {"key_id": key_id, "key_secret": key_secret, "webhook_secret": webhook_secret}


def _auth_header(key_id: str, key_secret: str) -> Dict[str, str]:
    token = base64.b64encode(f"{key_id}:{key_secret}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


async def create_order(
    key_id: str,
    key_secret: str,
    amount_paise: int,
    receipt: str,
    notes: Optional[Dict[str, str]] = None,
    currency: str = "INR",
) -> Dict[str, Any]:
    """Create a Razorpay order (server-side, amount fixed by server)."""
    payload: Dict[str, Any] = {
        "amount": int(amount_paise),
        "currency": currency,
        "receipt": receipt[:40],
        "payment_capture": 1,
    }
    if notes:
        payload["notes"] = notes
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{RAZORPAY_BASE}/orders", headers=_auth_header(key_id, key_secret), json=payload
        )
    resp.raise_for_status()
    return resp.json()


async def fetch_order(key_id: str, key_secret: str, order_id: str) -> Dict[str, Any]:
    """Fetch an order so the paid amount can be reconciled from the gateway."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{RAZORPAY_BASE}/orders/{order_id}", headers=_auth_header(key_id, key_secret)
        )
    resp.raise_for_status()
    return resp.json()


def verify_payment_signature(order_id: str, payment_id: str, signature: str, key_secret: str) -> bool:
    """Verify the checkout callback signature: HMAC-SHA256("order_id|payment_id")."""
    if not (order_id and payment_id and signature and key_secret):
        return False
    expected = hmac.new(
        key_secret.encode("utf-8"), f"{order_id}|{payment_id}".encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def verify_webhook_signature(raw_body: bytes, signature: Optional[str], webhook_secret: str) -> bool:
    """Verify the Razorpay webhook signature: HMAC-SHA256 of the raw request body."""
    if not (signature and webhook_secret):
        return False
    expected = hmac.new(webhook_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
