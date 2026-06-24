"""WhatsApp (Meta Cloud API) outbound client + payload builders.

Extracted from the webhook so both the inbound bot and the notification pipeline
share one implementation. Builders are pure (no I/O); `send_message` performs the POST.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_API_URL = "https://graph.facebook.com/{version}/{phone_id}/messages"


def normalize_phone(phone: str) -> str:
    """Strip non-digits; drop a leading India country code (91) for 12-digit numbers."""
    digits = re.sub(r"\D", "", phone or "")
    if digits.startswith("91") and len(digits) == 12:
        return digits[2:]
    return digits


def _strip_md(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text or "")
    return re.sub(r"_(.+?)_", r"\1", text)


# ── Payload builders (pure) ───────────────────────────────────────────────────

def wa_text(to: str, text: str) -> Dict[str, Any]:
    return {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": _strip_md(text)[:4096]},
    }


def wa_interactive_list(to: str, body_text: str, options: List[Dict]) -> Dict[str, Any]:
    rows = [
        {
            "id": str(o["id"])[:200],
            "title": str(o["label"])[:24],
            "description": (o.get("description") or "")[:72],
        }
        for o in options[:10]
    ]
    return {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": "School Assistant"},
            "body": {"text": _strip_md(body_text)[:1024]},
            "footer": {"text": "Reply with the option ID or type 'menu' to restart"},
            "action": {"button": "Select", "sections": [{"title": "Options", "rows": rows}]},
        },
    }


def wa_buttons(to: str, body_text: str, options: List[Dict]) -> Dict[str, Any]:
    buttons = [
        {"type": "reply", "reply": {"id": str(o["id"])[:256], "title": str(o["label"])[:20]}}
        for o in options[:3]
    ]
    return {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {"type": "button", "body": {"text": _strip_md(body_text)[:1024]}, "action": {"buttons": buttons}},
    }


def wa_template(to: str, name: str, lang: str, params: Optional[List[str]] = None) -> Dict[str, Any]:
    """Business-initiated template message (required outside the 24h session window).

    `params` fill the {{1}}, {{2}} ... body placeholders of the approved template.
    """
    components = []
    if params:
        components.append({
            "type": "body",
            "parameters": [{"type": "text", "text": str(p)} for p in params],
        })
    template: Dict[str, Any] = {"name": name, "language": {"code": lang or settings.WHATSAPP_DEFAULT_LANG}}
    if components:
        template["components"] = components
    return {"messaging_product": "whatsapp", "to": to, "type": "template", "template": template}


# ── Config + send ─────────────────────────────────────────────────────────────

def resolve_config(overrides: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """Build the WhatsApp config from global settings, overlaid with per-school overrides."""
    cfg = {
        "token": settings.META_WHATSAPP_TOKEN,
        "phone_id": settings.META_PHONE_NUMBER_ID,
        "api_version": settings.META_WHATSAPP_API_VERSION,
    }
    if overrides:
        cfg.update({k: v for k, v in overrides.items() if v})
    return cfg


def send_message(config: Dict[str, str], to: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """POST a prepared payload to the Meta Cloud API. Synchronous."""
    token = config.get("token")
    phone_id = config.get("phone_id")
    if not token or not phone_id:
        logger.warning("WhatsApp credentials not configured; skipping send.")
        return {"ok": False, "provider_message_id": None, "raw": "", "error": "no_credentials"}
    url = _API_URL.format(version=config.get("api_version") or "v18.0", phone_id=phone_id)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        with httpx.Client(timeout=15) as client:
            resp = client.post(url, headers=headers, json=payload)
        ok = resp.status_code < 400
        mid = None
        if ok:
            try:
                mid = resp.json().get("messages", [{}])[0].get("id")
            except Exception:
                mid = None
        else:
            logger.error("WA send failed status=%s body=%s", resp.status_code, resp.text[:500])
        return {
            "ok": ok,
            "provider_message_id": mid,
            "raw": resp.text[:1000],
            "error": None if ok else f"http_{resp.status_code}",
        }
    except Exception as exc:
        logger.exception("WhatsApp send error: %s", exc)
        return {"ok": False, "provider_message_id": None, "raw": "", "error": str(exc)}
