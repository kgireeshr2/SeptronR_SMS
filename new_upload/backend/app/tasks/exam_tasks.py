"""Celery tasks — Phase 9: Exam result notifications.

Delegates to the central notification pipeline (notify_event). Kept for backward
compatibility with any caller that still imports send_result_notification_bulk.
"""
from __future__ import annotations

import logging

from app.tasks.celery_app import celery

logger = logging.getLogger(__name__)


@celery.task(name="tasks.send_result_notification_bulk", queue="notifications")
def send_result_notification_bulk(exam_type_id: str, class_id: str, year_id: str, school_id: str) -> dict:
    """Notify parents of a class that results were published."""
    from app.services.notifications.notify import notify_event
    notify_event(
        school_id, "result_published", audience="parents", class_id=class_id,
        default_channels=["in_app", "sms", "whatsapp"],
        title="Results Published",
        body="Dear Parent, exam results have been published. Please check the parent portal.",
        link="/exams",
    )
    return {"status": "dispatched", "class_id": class_id, "school_id": school_id}
