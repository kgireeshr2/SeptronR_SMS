"""
Celery tasks — Phase 9: Exam Management
Background jobs for result notifications.
"""
from __future__ import annotations

try:
    from app.core.celery_app import celery_app

    @celery_app.task(queue="notifications", bind=True, max_retries=3)
    def send_result_notification_bulk(
        self,
        exam_type_id: str,
        class_id: str,
        year_id: str,
        school_id: str,
    ) -> dict:
        """
        Send SMS/notification to parents for published results.
        Called after results are published for a class + exam type.
        """
        # Placeholder: implement with actual notification channels
        return {
            "exam_type_id": exam_type_id,
            "class_id": class_id,
            "year_id": year_id,
            "school_id": school_id,
            "status": "queued",
        }

except Exception:
    # Celery not configured — define no-op for graceful degradation
    def send_result_notification_bulk(*args, **kwargs):  # type: ignore[misc]
        pass

    send_result_notification_bulk.delay = send_result_notification_bulk  # type: ignore[attr-defined]
