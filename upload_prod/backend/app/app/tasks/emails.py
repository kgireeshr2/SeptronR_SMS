"""Celery email tasks."""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.tasks.celery_app import celery


@celery.task(name="tasks.send_email", queue="emails", bind=True, max_retries=3)
def send_email(self, to: str, subject: str, html_body: str, from_name: str = ""):
    """Send transactional email via SMTP."""
    try:
        from app.core.config import settings
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{from_name or settings.MAIL_FROM_NAME} <{settings.MAIL_FROM}>" \
            if hasattr(settings, "MAIL_FROM") else subject
        msg["To"] = to
        msg.attach(MIMEText(html_body, "html"))

        if hasattr(settings, "MAIL_HOST") and settings.MAIL_HOST:
            with smtplib.SMTP(settings.MAIL_HOST, getattr(settings, "MAIL_PORT", 587)) as server:
                if getattr(settings, "MAIL_TLS", True):
                    server.starttls()
                if getattr(settings, "MAIL_USERNAME", None):
                    server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
                server.sendmail(msg["From"], [to], msg.as_string())
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@celery.task(name="tasks.send_bulk_email", queue="emails")
def send_bulk_email(recipients: list, subject: str, html_body: str):
    """Send bulk email to a list of recipients."""
    for recipient in recipients:
        send_email.delay(recipient, subject, html_body)


@celery.task(name="tasks.send_password_reset_email", queue="emails", bind=True, max_retries=3)
def send_password_reset_email(self, email: str, token: str, school_name: str):
    """Send password reset email via SMTP."""
    try:
        from app.core.config import settings
        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:5173")
        reset_link = f"{frontend_url}/reset-password?token={token}"
        subject = f"Reset your password — {school_name}"
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: auto;">
            <h2 style="color: #1e3a8a;">Password Reset Request</h2>
            <p>You requested a password reset for your <strong>{school_name}</strong> account.</p>
            <p>Click the button below to reset your password. This link expires in <strong>1 hour</strong>.</p>
            <p style="text-align: center; margin: 30px 0;">
                <a href="{reset_link}"
                   style="background-color: #1e3a8a; color: white; padding: 12px 30px;
                          text-decoration: none; border-radius: 6px; font-size: 16px;">
                    Reset Password
                </a>
            </p>
            <p style="color: #666; font-size: 12px;">
                If you didn't request this, please ignore this email. Your password will remain unchanged.
                <br>Link: {reset_link}
            </p>
        </body>
        </html>
        """
        send_email(email, subject, html_body, school_name)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@celery.task(name="tasks.send_admission_acknowledgement", queue="emails")
def send_admission_acknowledgement(parent_email: str, reference_number: str, school_name: str, applicant_name: str):
        subject = f"Application Received — {school_name}"
        html_body = f"""
        <html><body style='font-family: Arial, sans-serif;'>
            <h3>Application Submitted</h3>
            <p>Dear Parent,</p>
            <p>We received the admission application for <strong>{applicant_name}</strong>.</p>
            <p>Reference Number: <strong>{reference_number}</strong></p>
            <p>Please keep this reference for status tracking.</p>
        </body></html>
        """
        send_email(parent_email, subject, html_body, school_name)


@celery.task(name="tasks.send_admission_approved", queue="emails")
def send_admission_approved(parent_email: str, student_name: str, admission_number: str, school_name: str):
        subject = f"Admission Approved — {school_name}"
        html_body = f"""
        <html><body style='font-family: Arial, sans-serif;'>
            <h3>Congratulations!</h3>
            <p>Admission approved for <strong>{student_name}</strong>.</p>
            <p>Admission Number: <strong>{admission_number}</strong></p>
        </body></html>
        """
        send_email(parent_email, subject, html_body, school_name)


@celery.task(name="tasks.send_admission_rejected", queue="emails")
def send_admission_rejected(parent_email: str, student_name: str, remarks: str, school_name: str):
        subject = f"Admission Update — {school_name}"
        html_body = f"""
        <html><body style='font-family: Arial, sans-serif;'>
            <h3>Admission Update</h3>
            <p>Admission for <strong>{student_name}</strong> was not approved at this time.</p>
            <p>Remarks: {remarks or 'N/A'}</p>
        </body></html>
        """
        send_email(parent_email, subject, html_body, school_name)

