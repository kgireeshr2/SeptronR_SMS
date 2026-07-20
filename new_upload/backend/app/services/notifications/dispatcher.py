"""Central dispatcher: turn an (event, recipients, context) into MessageLog + Notification rows.

Does NOT enqueue delivery itself — it returns the created MessageLog ids so the calling
Celery task can commit first, then enqueue `deliver_message` (avoids a read-before-commit race).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.communications import (
    MessageLog,
    Notification,
    NotificationPreference,
    NotificationTemplate,
)
from app.services.notifications import templating
from app.services.notifications.recipients import Recipient

logger = logging.getLogger(__name__)

# Channels that produce an outbound MessageLog + async delivery.
_OUTBOUND = {"sms", "whatsapp", "email", "push"}


async def _load_template(db: AsyncSession, school_id: str, event: str) -> Optional[NotificationTemplate]:
    res = await db.execute(
        select(NotificationTemplate).where(
            NotificationTemplate.school_id == school_id,
            NotificationTemplate.event_trigger == event,
            NotificationTemplate.is_active == True,  # noqa: E712
        ).order_by(NotificationTemplate.is_default.desc())
    )
    return res.scalars().first()


async def _disabled_channels(db: AsyncSession, user_id: str) -> set:
    res = await db.execute(
        select(NotificationPreference).where(
            NotificationPreference.user_id == user_id,
            NotificationPreference.enabled == False,  # noqa: E712
        )
    )
    out = set()
    for p in res.scalars().all():
        out.add(p.channel if p.event_trigger == "all" else f"{p.channel}:{p.event_trigger}")
    return out


def _is_disabled(disabled: set, channel: str, event: str) -> bool:
    return "all" in disabled or channel in disabled or f"{channel}:{event}" in disabled


async def dispatch(
    db: AsyncSession,
    school_id: str,
    event: str,
    recipients: List[Recipient],
    context: Optional[Dict[str, Any]] = None,
    *,
    channels: Optional[List[str]] = None,
    default_channels: Optional[List[str]] = None,
    title: Optional[str] = None,
    subject: Optional[str] = None,
    body: Optional[str] = None,
    link: Optional[str] = None,
    bulk_id: Optional[str] = None,
) -> Dict[str, Any]:
    context = dict(context or {})

    template = None
    if channels is None or body is None or subject is None:
        template = await _load_template(db, school_id, event)
    # Channel selection: explicit > per-school template > caller default > in_app.
    if channels is None:
        channels = template.channels if template else (default_channels or ["in_app"])
    base_subject = subject if subject is not None else (template.subject if template else (title or event))
    base_body = body if body is not None else (template.body if template else "")

    log_ids: List[str] = []
    notif_count = 0

    for r in recipients:
        ctx = {**context, "recipient_name": r.name}
        rendered_body = templating.render(base_body, ctx) or base_body
        rendered_subject = templating.render(base_subject or "", ctx) or (title or event)

        disabled = await _disabled_channels(db, str(r.user_id)) if r.user_id else set()

        for channel in channels:
            if _is_disabled(disabled, channel, event):
                continue

            if channel == "in_app":
                if not r.user_id:
                    continue
                db.add(Notification(
                    school_id=school_id, user_id=r.user_id, type=event, channel="in_app",
                    title=(title or rendered_subject or event)[:300], body=rendered_body,
                    data={"link": link, "event": event} if link else {"event": event},
                ))
                notif_count += 1
                continue

            if channel not in _OUTBOUND:
                continue
            if channel in ("sms", "whatsapp") and not r.phone:
                continue
            if channel == "email" and not r.email:
                continue
            if channel == "push" and not r.user_id:
                continue

            log = MessageLog(
                school_id=school_id, bulk_message_id=bulk_id,
                recipient_user_id=r.user_id, recipient_phone=r.phone, recipient_email=r.email,
                channel=channel, event_trigger=event,
                subject=rendered_subject[:300] if rendered_subject else None,
                body=rendered_body, status="queued",
            )
            db.add(log)
            await db.flush()
            log_ids.append(str(log.id))

    return {"message_log_ids": log_ids, "notification_count": notif_count}
