"""
SQLAlchemy models — Phase 14: Communication & Notifications
Tables: notification_templates, notifications, bulk_messages, message_logs, announcements
"""
from __future__ import annotations

from enum import Enum as PyEnum
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    Boolean, ForeignKey, Integer, String, Text, UniqueConstraint,
)
from app.models.compat import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from sqlalchemy import DateTime
from sqlalchemy import func

if TYPE_CHECKING:
    from app.models.school import School
    from app.models.auth import User
    from app.models.classes import Class, Section


class NotificationChannel(str, PyEnum):
    sms = "sms"
    email = "email"
    whatsapp = "whatsapp"
    push = "push"
    in_app = "in_app"


class NotificationTrigger(str, PyEnum):
    attendance_absent = "attendance_absent"
    fee_due = "fee_due"
    fee_receipt = "fee_receipt"
    result_published = "result_published"
    homework_assigned = "homework_assigned"
    ptm_reminder = "ptm_reminder"
    birthday = "birthday"
    custom = "custom"


class NotificationTemplate(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "notification_templates"
    __table_args__ = (
        UniqueConstraint("school_id", "event_trigger", "name", name="notif_templates_school_evt_name_ux"),
    )

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    channel: Mapped[str] = mapped_column("channels", String(30), nullable=False)
    event_trigger: Mapped[str] = mapped_column(String(50), nullable=False)
    subject: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    body: Mapped[Optional[str]] = mapped_column("body_template", Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    @property
    def channels(self) -> list:
        """Expose channel as a list for schema compatibility."""
        return self.channel.split(",") if self.channel else []

    @property
    def body_template(self) -> str:
        """Expose body as body_template for schema compatibility."""
        return self.body or ""


class Notification(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "notifications"

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    channel: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    data: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    read_at: Mapped[Optional[object]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    @property
    def sent_at(self):
        """Compatibility alias — notifications are sent immediately at creation."""
        return self.created_at


class BulkMessage(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "bulk_messages"

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    channels: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False, default="all")
    target_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    target_class_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=True), nullable=True)
    target_section_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=True), nullable=True)
    scheduled_at: Mapped[Optional[object]] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[Optional[object]] = mapped_column(DateTime(timezone=True), nullable=True)
    total_recipients: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sent_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    created_by: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    @property
    def channel(self) -> str:
        """Return first channel for schema compatibility."""
        return self.channels[0] if self.channels else ""

    @property
    def audience(self) -> str:
        """Expose target_type as audience for schema compatibility."""
        return self.target_type or "all"

    @property
    def audience_filter(self):
        return None


class MessageLog(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "message_logs"

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    bulk_message_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bulk_messages.id"), nullable=True
    )
    recipient_user_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=True), nullable=True)
    recipient_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    recipient_email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    channel: Mapped[str] = mapped_column(String(30), nullable=False)
    event_trigger: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    subject: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="queued")
    provider_message_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, index=True)
    gateway_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sent_at: Mapped[Optional[object]] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[Optional[object]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Announcement(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "announcements"

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    content: Mapped[Optional[str]] = mapped_column("body", Text, nullable=True)
    attachment_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    audience: Mapped[str] = mapped_column(String(20), nullable=False, default="all")
    target_class_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("classes.id"), nullable=True
    )
    target_section_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sections.id"), nullable=True
    )
    is_published: Mapped[bool] = mapped_column("is_active", Boolean, nullable=False, default=False)
    published_at: Mapped[Optional[object]] = mapped_column("publish_at", DateTime(timezone=True), nullable=True)
    expires_at: Mapped[Optional[object]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    @property
    def body(self) -> str:
        """Expose content as body for schema compatibility."""
        return self.content or ""

    @property
    def is_active(self) -> bool:
        """Alias is_published as is_active for schema compatibility."""
        return self.is_published

    @property
    def publish_at(self):
        """Alias published_at as publish_at for schema serialization (read-only)."""
        return self.published_at

    @property
    def audience_filter(self):
        return None


class DeviceToken(Base, UUIDPrimaryKeyMixin):
    """A registered push target for a user (mobile Expo token, web-push subscription, or FCM token)."""
    __tablename__ = "device_tokens"
    __table_args__ = (
        UniqueConstraint("user_id", "token", name="device_tokens_user_token_ux"),
    )

    school_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=True, index=True
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    # Expo push token, FCM token, or (for web-push) the JSON subscription object as text.
    token: Mapped[str] = mapped_column(Text, nullable=False)
    provider: Mapped[str] = mapped_column(String(20), nullable=False, default="expo")  # expo | webpush | fcm
    platform: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)         # ios | android | web
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_seen: Mapped[Optional[object]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class NotificationPreference(Base, UUIDPrimaryKeyMixin):
    """Per-user opt-out for a (channel, event_trigger) pair. Absence of a row = opted-in."""
    __tablename__ = "notification_preferences"
    __table_args__ = (
        UniqueConstraint("user_id", "channel", "event_trigger", name="notif_prefs_user_chan_evt_ux"),
    )

    school_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=True, index=True
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    channel: Mapped[str] = mapped_column(String(30), nullable=False)          # sms|email|whatsapp|push|in_app|all
    event_trigger: Mapped[str] = mapped_column(String(50), nullable=False, default="all")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
