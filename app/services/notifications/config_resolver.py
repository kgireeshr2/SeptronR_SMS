"""Resolve per-school channel credentials (Settings KV) with global .env fallback."""
from __future__ import annotations

from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations import email_client, sms_client, whatsapp_client
from app.repositories.settings_repository import SettingsRepository

_TRUE = {"1", "true", "yes", "on"}


async def _comm_kv(db: AsyncSession, school_id: Optional[str]) -> Dict[str, str]:
    if not school_id:
        return {}
    try:
        return await SettingsRepository(db).get_as_dict(school_id, "communication")
    except Exception:
        return {}


async def resolve_channel_config(db: AsyncSession, school_id: Optional[str], channel: str) -> Dict[str, Any]:
    """Return a ready-to-send config dict for one channel, merging school KV over env."""
    kv = await _comm_kv(db, school_id)

    if channel == "sms":
        return sms_client.resolve_config({
            "provider": kv.get("sms_gateway"),
            "msg91_key": kv.get("sms_api_key"),
            "msg91_sender": kv.get("sms_sender_id"),
            "msg91_template_id": kv.get("sms_template_id"),
            "twilio_sid": kv.get("twilio_sid"),
            "twilio_token": kv.get("twilio_token"),
            "twilio_from": kv.get("twilio_from"),
        })

    if channel == "whatsapp":
        cfg = whatsapp_client.resolve_config({
            "token": kv.get("whatsapp_token") or kv.get("whatsapp_api_key"),
            "phone_id": kv.get("whatsapp_phone_id"),
        })
        # Treat an explicit per-school disable as "no credentials".
        if "whatsapp_enabled" in kv and str(kv.get("whatsapp_enabled", "")).lower() not in _TRUE:
            cfg["token"] = ""
        return cfg

    if channel == "email":
        return email_client.resolve_config({
            "host": kv.get("smtp_host"),
            "port": kv.get("smtp_port"),
            "username": kv.get("smtp_username"),
            "password": kv.get("smtp_password"),
            "from_email": kv.get("smtp_from_email"),
            "from_name": kv.get("smtp_from_name"),
            "use_tls": (str(kv["smtp_use_tls"]).lower() in _TRUE) if "smtp_use_tls" in kv else None,
        })

    return {}
