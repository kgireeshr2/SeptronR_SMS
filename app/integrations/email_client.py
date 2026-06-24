"""Email outbound client — SMTP. Synchronous."""
from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


def resolve_config(overrides: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """SMTP config — prefer MAIL_*, fall back to SMTP_*; overlaid with per-school overrides."""
    cfg: Dict[str, Any] = {
        "host": settings.MAIL_HOST or settings.SMTP_HOST,
        "port": int(settings.MAIL_PORT or settings.SMTP_PORT or 587),
        "username": settings.MAIL_USERNAME or settings.SMTP_USER,
        "password": settings.MAIL_PASSWORD or settings.SMTP_PASSWORD,
        "from_email": settings.MAIL_FROM or settings.SMTP_FROM_EMAIL,
        "from_name": settings.MAIL_FROM_NAME or settings.SMTP_FROM_NAME,
        "use_tls": bool(settings.MAIL_TLS),
    }
    if overrides:
        for k, v in overrides.items():
            if v not in (None, ""):
                cfg[k] = v
    return cfg


def send(config: Dict[str, Any], to: str, subject: str, html_body: str) -> Dict[str, Any]:
    host = config.get("host")
    if not host:
        logger.info("[Email stub] To: %s | %s", to, subject)
        return {"ok": False, "provider_message_id": None, "raw": "stub", "error": "no_smtp_host"}
    from_email = config.get("from_email") or config.get("username") or "noreply@school.com"
    from_name = config.get("from_name") or "School"
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{from_name} <{from_email}>"
    msg["To"] = to
    msg.attach(MIMEText(html_body, "html"))
    try:
        with smtplib.SMTP(host, int(config.get("port", 587)), timeout=20) as server:
            if config.get("use_tls", True):
                server.starttls()
            if config.get("username"):
                server.login(config["username"], config.get("password", ""))
            server.sendmail(from_email, [to], msg.as_string())
        return {"ok": True, "provider_message_id": None, "raw": "sent", "error": None}
    except Exception as exc:
        logger.exception("Email send error: %s", exc)
        return {"ok": False, "provider_message_id": None, "raw": "", "error": str(exc)}
