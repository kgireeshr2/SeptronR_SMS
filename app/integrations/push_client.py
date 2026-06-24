"""Push outbound client — routes by provider: Expo, Web Push (VAPID), FCM. Synchronous.

Push credentials (VAPID keys, Firebase, Expo) are platform-level (global settings),
not per-school. Returns a per-token result; callers persist token state on failure.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


def _send_expo(token: str, title: str, body: str, data: Optional[dict]) -> Dict[str, Any]:
    headers = {"Content-Type": "application/json"}
    if settings.EXPO_ACCESS_TOKEN:
        headers["Authorization"] = f"Bearer {settings.EXPO_ACCESS_TOKEN}"
    payload = {"to": token, "title": title, "body": body, "data": data or {}, "sound": "default"}
    with httpx.Client(timeout=15) as client:
        resp = client.post(settings.EXPO_PUSH_URL, headers=headers, json=payload)
    ok = resp.status_code < 400
    # Expo reports per-message errors (e.g. DeviceNotRegistered) in the body even on 200.
    dead = "DeviceNotRegistered" in resp.text
    return {"ok": ok and not dead, "provider_message_id": None, "raw": resp.text[:1000],
            "error": None if (ok and not dead) else "expo_error", "dead_token": dead}


def _send_webpush(subscription_json: str, title: str, body: str, data: Optional[dict]) -> Dict[str, Any]:
    if not settings.VAPID_PRIVATE_KEY:
        return {"ok": False, "provider_message_id": None, "raw": "", "error": "no_vapid", "dead_token": False}
    try:
        from pywebpush import webpush, WebPushException
    except Exception:
        return {"ok": False, "provider_message_id": None, "raw": "", "error": "pywebpush_missing", "dead_token": False}
    try:
        sub = json.loads(subscription_json)
        webpush(
            subscription_info=sub,
            data=json.dumps({"title": title, "body": body, "data": data or {}}),
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims={"sub": settings.VAPID_SUBJECT},
        )
        return {"ok": True, "provider_message_id": None, "raw": "sent", "error": None, "dead_token": False}
    except WebPushException as exc:  # type: ignore
        status = getattr(getattr(exc, "response", None), "status_code", None)
        dead = status in (404, 410)
        return {"ok": False, "provider_message_id": None, "raw": str(exc)[:500],
                "error": f"webpush_{status}", "dead_token": dead}
    except Exception as exc:
        return {"ok": False, "provider_message_id": None, "raw": str(exc)[:500], "error": str(exc), "dead_token": False}


def _send_fcm(token: str, title: str, body: str, data: Optional[dict]) -> Dict[str, Any]:
    if not settings.FIREBASE_PROJECT_ID:
        return {"ok": False, "provider_message_id": None, "raw": "", "error": "no_firebase", "dead_token": False}
    try:
        import firebase_admin
        from firebase_admin import messaging
        if not firebase_admin._apps:
            firebase_admin.initialize_app()
        msg = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data={k: str(v) for k, v in (data or {}).items()},
            token=token,
        )
        mid = messaging.send(msg)
        return {"ok": True, "provider_message_id": mid, "raw": "sent", "error": None, "dead_token": False}
    except Exception as exc:
        return {"ok": False, "provider_message_id": None, "raw": str(exc)[:500], "error": str(exc), "dead_token": False}


def send(provider: str, token: str, title: str, body: str, data: Optional[dict] = None) -> Dict[str, Any]:
    """Dispatch one push to one device token by provider."""
    try:
        if provider == "expo":
            return _send_expo(token, title, body, data)
        if provider == "webpush":
            return _send_webpush(token, title, body, data)
        if provider == "fcm":
            return _send_fcm(token, title, body, data)
        return {"ok": False, "provider_message_id": None, "raw": "", "error": "unknown_provider", "dead_token": False}
    except Exception as exc:
        logger.exception("Push send error: %s", exc)
        return {"ok": False, "provider_message_id": None, "raw": "", "error": str(exc), "dead_token": False}
