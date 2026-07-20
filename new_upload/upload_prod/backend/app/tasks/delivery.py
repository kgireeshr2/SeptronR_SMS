"""Celery tasks for the central notification pipeline.

- dispatch_event: resolve audience → create MessageLog/Notification rows → enqueue deliveries.
- deliver_message: send one MessageLog via the right channel client and record the outcome.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone

from sqlalchemy import select

from app.tasks.celery_app import celery
from app.tasks.async_db import run_async

logger = logging.getLogger(__name__)


# ── dispatch_event ────────────────────────────────────────────────────────────

@celery.task(name="tasks.dispatch_event", queue="notifications", bind=True, max_retries=2)
def dispatch_event(self, school_id, event, audience="all", context=None, channels=None,
                   default_channels=None, class_id=None, section_id=None, user_ids=None,
                   student_ids=None, direct_contacts=None,
                   title=None, subject=None, body=None, link=None, bulk_id=None):
    """Fan an event out to an audience. Safe to call via .delay() from any domain service."""
    from app.services.notifications import dispatcher
    from app.services.notifications.recipients import resolve_recipients

    async def _run(db):
        recipients = await resolve_recipients(
            db, school_id, audience,
            class_id=class_id, section_id=section_id, user_ids=user_ids,
            student_ids=student_ids, direct_contacts=direct_contacts,
        )
        if not recipients:
            return {"message_log_ids": [], "notification_count": 0}
        return await dispatcher.dispatch(
            db, school_id, event, recipients, context or {},
            channels=channels, default_channels=default_channels,
            title=title, subject=subject, body=body, link=link, bulk_id=bulk_id,
        )

    try:
        result = run_async(_run)
    except Exception as exc:
        logger.exception("dispatch_event failed: %s", exc)
        raise self.retry(exc=exc, countdown=30)

    for log_id in result.get("message_log_ids", []):
        try:
            deliver_message.delay(log_id)
        except Exception as exc:  # broker down — leave row 'queued' for a later sweep
            logger.warning("Could not enqueue deliver_message %s: %s", log_id, exc)
    return result


# ── send_bulk_message ─────────────────────────────────────────────────────────

@celery.task(name="tasks.send_bulk_message", queue="notifications", bind=True, max_retries=2)
def send_bulk_message(self, bulk_id: str):
    """Resolve a BulkMessage's audience and fan out across its channels."""
    from app.models.communications import BulkMessage
    from app.services.notifications import dispatcher
    from app.services.notifications.recipients import resolve_recipients

    async def _run(db):
        bm = (await db.execute(select(BulkMessage).where(BulkMessage.id == bulk_id))).scalar_one_or_none()
        if not bm or bm.status in ("sending", "sent"):
            return {"message_log_ids": []}
        bm.status = "sending"
        await db.flush()
        recipients = await resolve_recipients(
            db, str(bm.school_id), bm.target_type or "all",
            class_id=str(bm.target_class_id) if bm.target_class_id else None,
            section_id=str(bm.target_section_id) if bm.target_section_id else None,
        )
        res = await dispatcher.dispatch(
            db, str(bm.school_id), "bulk", recipients, {},
            channels=bm.channels or ["in_app"], title=bm.title, subject=bm.title,
            body=bm.body, bulk_id=str(bm.id),
        )
        bm.total_recipients = len(recipients)
        bm.sent_count = len(res.get("message_log_ids", [])) + res.get("notification_count", 0)
        bm.status = "sent"
        bm.sent_at = datetime.now(timezone.utc)
        return res

    try:
        result = run_async(_run)
    except Exception as exc:
        logger.exception("send_bulk_message failed: %s", exc)
        raise self.retry(exc=exc, countdown=60)

    for log_id in result.get("message_log_ids", []):
        try:
            deliver_message.delay(log_id)
        except Exception as exc:
            logger.warning("Could not enqueue deliver_message %s: %s", log_id, exc)
    return result


# ── deliver_message ───────────────────────────────────────────────────────────

def _wa_to(phone: str) -> str:
    digits = re.sub(r"\D", "", phone or "")
    return digits if len(digits) > 10 else f"91{digits}"  # default India country code


@celery.task(name="tasks.deliver_message", queue="notifications", bind=True, max_retries=3)
def deliver_message(self, message_log_id: str):
    """Send one queued MessageLog row through its channel and update its status."""
    from app.models.communications import MessageLog, DeviceToken
    from app.services.notifications.config_resolver import resolve_channel_config
    from app.integrations import sms_client, email_client, whatsapp_client, push_client

    async def _run(db):
        log = (await db.execute(select(MessageLog).where(MessageLog.id == message_log_id))).scalar_one_or_none()
        if not log or log.status not in ("queued", "failed"):
            return {"ok": True, "skip": True}

        channel = log.channel
        result = {"ok": False, "error": "unhandled", "raw": "", "provider_message_id": None}

        if channel == "sms":
            cfg = await resolve_channel_config(db, str(log.school_id), "sms")
            result = sms_client.send(cfg, log.recipient_phone, log.body or "")
        elif channel == "email":
            cfg = await resolve_channel_config(db, str(log.school_id), "email")
            result = email_client.send(cfg, log.recipient_email, log.subject or "Notification", log.body or "")
        elif channel == "whatsapp":
            cfg = await resolve_channel_config(db, str(log.school_id), "whatsapp")
            payload = whatsapp_client.wa_text(_wa_to(log.recipient_phone), log.body or "")
            result = whatsapp_client.send_message(cfg, _wa_to(log.recipient_phone), payload)
        elif channel == "push":
            tokens = (await db.execute(
                select(DeviceToken).where(
                    DeviceToken.user_id == log.recipient_user_id,
                    DeviceToken.is_active == True,  # noqa: E712
                )
            )).scalars().all()
            any_ok = False
            errors = []
            for t in tokens:
                r = push_client.send(t.provider, t.token, log.subject or "Notification", log.body or "", {})
                any_ok = any_ok or r.get("ok")
                if r.get("dead_token"):
                    t.is_active = False
                if r.get("error"):
                    errors.append(r["error"])
            result = {"ok": any_ok, "error": None if any_ok else (",".join(errors) or "no_devices"),
                      "raw": "", "provider_message_id": None}

        log.status = "sent" if result.get("ok") else "failed"
        log.provider_message_id = result.get("provider_message_id")
        log.gateway_response = (result.get("raw") or "")[:2000]
        log.error_message = result.get("error")
        if result.get("ok"):
            log.sent_at = datetime.now(timezone.utc)
        return {"ok": result.get("ok"), "error": result.get("error")}

    try:
        res = run_async(_run)
    except Exception as exc:
        logger.exception("deliver_message DB error: %s", exc)
        raise self.retry(exc=exc, countdown=60)

    # Retry only on transient transport errors, not on misconfig/no-credential stubs.
    if not res.get("ok") and res.get("error") and res["error"] not in (
        "no_provider", "no_credentials", "no_smtp_host", "no_vapid", "no_firebase", "no_devices", "unknown_provider"
    ) and not res.get("skip"):
        try:
            raise self.retry(countdown=60)
        except self.MaxRetriesExceededError:
            pass
    return res
