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
