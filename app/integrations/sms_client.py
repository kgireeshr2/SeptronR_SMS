"""SMS outbound client — MSG91 (flow/template) and Twilio. Synchronous."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


def resolve_config(overrides: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """SMS config from global settings (canonical names with legacy fallback), overlaid per-school."""
    cfg = {
        "provider": (settings.SMS_PROVIDER or "msg91").lower(),
        "msg91_key": settings.MSG91_API_KEY or settings.MSG91_AUTH_KEY,
        "msg91_sender": settings.MSG91_SENDER or settings.MSG91_SENDER_ID,
        "msg91_template_id": settings.MSG91_TEMPLATE_ID,
        "twilio_sid": settings.TWILIO_ACCOUNT_SID,
        "twilio_token": settings.TWILIO_AUTH_TOKEN,
        "twilio_from": settings.TWILIO_FROM_NUMBER,
    }
    if overrides:
        cfg.update({k: v for k, v in overrides.items() if v})
    return cfg


def send(config: Dict[str, str], phone: str, message: str) -> Dict[str, Any]:
    provider = (config.get("provider") or "msg91").lower()
    try:
        if provider == "msg91" and config.get("msg91_key"):
            with httpx.Client(timeout=15) as client:
                resp = client.post(
                    "https://api.msg91.com/api/v5/flow/",
                    json={
                        "template_id": config.get("msg91_template_id", ""),
                        "sender": config.get("msg91_sender", "SCHOOL"),
                        "mobiles": phone,
                        "message": message,
                    },
                    headers={"authkey": config.get("msg91_key", ""), "content-type": "application/json"},
                )
            ok = resp.status_code < 400
            return {"ok": ok, "provider_message_id": None, "raw": resp.text[:1000],
                    "error": None if ok else f"http_{resp.status_code}"}

        if provider == "twilio" and config.get("twilio_sid"):
            from twilio.rest import Client
            client = Client(config["twilio_sid"], config["twilio_token"])
            msg = client.messages.create(body=message, from_=config.get("twilio_from"), to=phone)
            return {"ok": True, "provider_message_id": msg.sid, "raw": str(msg.status), "error": None}

        # No provider configured — stub (still logged + MessageLog row recorded by caller).
        logger.info("[SMS stub] To: %s | %s", phone, message)
        return {"ok": False, "provider_message_id": None, "raw": "stub", "error": "no_provider"}
    except Exception as exc:
        logger.exception("SMS send error: %s", exc)
        return {"ok": False, "provider_message_id": None, "raw": "", "error": str(exc)}
