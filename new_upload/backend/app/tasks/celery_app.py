from celery import Celery
from app.core.config import settings

celery = Celery(
    "sms_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.notifications",
        "app.tasks.reports",
        "app.tasks.emails",
        "app.tasks.scheduled",
        "app.tasks.delivery",
        "app.tasks.exam_tasks",
    ],
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "app.tasks.notifications.*": {"queue": "notifications"},
        "app.tasks.reports.*": {"queue": "reports"},
        "app.tasks.emails.*": {"queue": "emails"},
        "app.tasks.scheduled.*": {"queue": "scheduled"},
        "app.tasks.delivery.*": {"queue": "notifications"},
    },
)
