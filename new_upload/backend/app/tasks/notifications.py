"""Celery notification tasks."""
import logging

from app.tasks.celery_app import celery

logger = logging.getLogger(__name__)


@celery.task(name="tasks.send_sms", queue="notifications", bind=True, max_retries=3)
def send_sms(self, phone: str, message: str):
    """Send SMS via configured provider (MSG91 / Twilio)."""
    try:
        from app.core.config import settings
        provider = getattr(settings, "SMS_PROVIDER", "").lower()
        if provider == "msg91":
            import requests
            resp = requests.post(
                "https://api.msg91.com/api/v5/flow/",
                json={
                    "template_id": getattr(settings, "MSG91_TEMPLATE_ID", ""),
                    "sender": getattr(settings, "MSG91_SENDER", "SCHOOL"),
                    "mobiles": phone,
                    "message": message,
                },
                headers={"authkey": getattr(settings, "MSG91_API_KEY", ""), "content-type": "application/json"},
                timeout=10,
            )
            resp.raise_for_status()
        elif provider == "twilio":
            from twilio.rest import Client
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            client.messages.create(
                body=message,
                from_=settings.TWILIO_FROM_NUMBER,
                to=phone,
            )
        else:
            logger.info(f"[SMS stub] To: {phone} | Message: {message}")
    except Exception as exc:
        raise self.retry(exc=exc, countdown=30)


@celery.task(name="tasks.send_sms_otp", queue="notifications", bind=True, max_retries=3)
def send_sms_otp(self, phone: str, otp: str):
    """Send OTP via SMS provider (MSG91 or Twilio)."""
    message = f"Your verification code is {otp}. Valid for 5 minutes. Do not share this with anyone."
    send_sms.apply(args=[phone, message])


@celery.task(name="tasks.send_whatsapp", queue="notifications")
def send_whatsapp(phone: str, template_name: str, parameters: list):
    """Send WhatsApp message via Meta Cloud API — fully implemented in Phase 14."""
    logger.info(f"[WhatsApp stub] To: {phone} | Template: {template_name}")


@celery.task(name="tasks.notify_absent_parents", queue="notifications")
def notify_absent_parents(absent_student_ids: list, school_id: str):
    """Notify parents of absent students — fully implemented in Phase 7."""
    logger.info(f"[notify_absent_parents stub] {len(absent_student_ids)} students, school={school_id}")

