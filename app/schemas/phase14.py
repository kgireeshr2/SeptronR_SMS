"""Schemas for Phase 14 — Communications & Notifications."""
from __future__ import annotations
from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime


# ── Notification Template ─────────────────────────────────────────────────────
class NotificationTemplateCreate(BaseModel):
    name: str
    event_trigger: str
    channels: List[str]
    subject: Optional[str] = None
    body_template: str
    is_active: bool = True
    is_default: bool = False


class NotificationTemplateUpdate(BaseModel):
    name: Optional[str] = None
    subject: Optional[str] = None
    body_template: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class NotificationTemplateResponse(NotificationTemplateCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    school_id: UUID
    is_default: bool
    created_at: datetime
    updated_at: datetime


# ── Notification ──────────────────────────────────────────────────────────────
class NotificationCreate(BaseModel):
    user_id: UUID
    type: str
    title: str
    body: str
    channel: str = "in_app"
    scheduled_at: Optional[datetime] = None
    extra_data: Optional[Any] = None  # renamed from 'metadata' to avoid SQLAlchemy conflict


class NotificationResponse(NotificationCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    school_id: UUID
    is_read: bool
    sent_at: Optional[datetime]
    created_at: datetime


# ── Bulk Message ──────────────────────────────────────────────────────────────
class BulkMessageCreate(BaseModel):
    title: str
    body: str
    channel: str
    audience: str = "all"
    audience_filter: Optional[Any] = None
    scheduled_at: Optional[datetime] = None


class BulkMessageResponse(BulkMessageCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    school_id: UUID
    created_by: UUID
    status: str
    sent_count: int
    failed_count: int
    created_at: datetime


# ── Announcement ──────────────────────────────────────────────────────────────
class AnnouncementCreate(BaseModel):
    title: str
    body: str
    audience: str = "all"
    audience_filter: Optional[Any] = None
    publish_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class AnnouncementResponse(AnnouncementCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    school_id: UUID
    created_by: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ── Mark Read ─────────────────────────────────────────────────────────────────
class MarkReadRequest(BaseModel):
    notification_ids: List[UUID]
