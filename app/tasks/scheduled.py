"""Celery beat scheduled tasks — implemented progressively across phases."""
from celery.schedules import crontab
from app.tasks.celery_app import celery


celery.conf.beat_schedule = {
    # Daily 7 AM: Generate monthly fee invoices
    "generate-monthly-invoices": {
        "task": "app.tasks.scheduled.generate_monthly_invoices",
        "schedule": crontab(hour=7, minute=0),
    },
    # Daily 8 AM: Send attendance reminders
    "send-attendance-reminders": {
        "task": "app.tasks.scheduled.send_attendance_reminders",
        "schedule": crontab(hour=8, minute=0),
    },
    # Weekly Sunday midnight: Audit log cleanup
    "cleanup-audit-logs": {
        "task": "app.tasks.scheduled.cleanup_old_audit_logs",
        "schedule": crontab(hour=0, minute=0, day_of_week="sunday"),
    },
    # Monthly: Generate salary slips
    "generate-payslips": {
        "task": "app.tasks.scheduled.generate_monthly_payslips",
        "schedule": crontab(hour=1, minute=0, day_of_month=1),
    },
    # Every 5 minutes: send any due scheduled bulk messages
    "dispatch-scheduled-bulk": {
        "task": "app.tasks.scheduled.dispatch_scheduled_bulk",
        "schedule": crontab(minute="*/5"),
    },
}


@celery.task(name="app.tasks.scheduled.generate_monthly_invoices", queue="scheduled")
def generate_monthly_invoices():
    """Auto-generate fee invoices for the new month."""
    pass


@celery.task(name="app.tasks.scheduled.send_attendance_reminders", queue="scheduled")
def send_attendance_reminders():
    """Send daily attendance reminders to class teachers."""
    pass


@celery.task(name="app.tasks.scheduled.cleanup_old_audit_logs", queue="scheduled")
def cleanup_old_audit_logs():
    """Delete audit logs older than configured retention period."""
    pass


@celery.task(name="app.tasks.scheduled.generate_monthly_payslips", queue="scheduled")
def generate_monthly_payslips():
    """Auto-generate staff payslips at month start."""
    pass


@celery.task(name="app.tasks.scheduled.dispatch_scheduled_bulk", queue="scheduled")
def dispatch_scheduled_bulk():
    """Find bulk messages whose scheduled_at is due and enqueue them."""
    from datetime import datetime, timezone
    from sqlalchemy import select
    from app.tasks.async_db import run_async
    from app.tasks.delivery import send_bulk_message
    from app.models.communications import BulkMessage

    async def _run(db):
        now = datetime.now(timezone.utc)
        rows = (await db.execute(
            select(BulkMessage.id).where(
                BulkMessage.status == "scheduled",
                BulkMessage.scheduled_at != None,  # noqa: E711
                BulkMessage.scheduled_at <= now,
            )
        )).scalars().all()
        return [str(r) for r in rows]

    for bid in run_async(_run):
        try:
            send_bulk_message.delay(bid)
        except Exception:
            pass
