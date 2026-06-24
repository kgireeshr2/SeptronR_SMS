"""Fire-and-forget trigger API for domain services.

Call `notify_event(...)` from anywhere (attendance save, fee payment, etc.). It enqueues
the async pipeline and NEVER raises — if the broker is down the core operation still
succeeds, the notification is simply skipped (and logged).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def notify_event(
    school_id: str,
    event: str,
    audience: str = "all",
    *,
    context: Optional[Dict[str, Any]] = None,
    channels: Optional[List[str]] = None,
    default_channels: Optional[List[str]] = None,
    class_id: Optional[str] = None,
    section_id: Optional[str] = None,
    user_ids: Optional[list] = None,
    student_ids: Optional[list] = None,
    direct_contacts: Optional[list] = None,
    title: Optional[str] = None,
    subject: Optional[str] = None,
    body: Optional[str] = None,
    link: Optional[str] = None,
    bulk_id: Optional[str] = None,
) -> None:
    try:
        from app.tasks.delivery import dispatch_event
        dispatch_event.delay(
            str(school_id), event, audience,
            context=context, channels=channels, default_channels=default_channels,
            class_id=str(class_id) if class_id else None,
            section_id=str(section_id) if section_id else None,
            user_ids=[str(u) for u in user_ids] if user_ids else None,
            student_ids=[str(s) for s in student_ids] if student_ids else None,
            direct_contacts=direct_contacts,
            title=title, subject=subject, body=body, link=link, bulk_id=bulk_id,
        )
    except Exception as exc:
        logger.warning("notify_event(%s) skipped: %s", event, exc)
