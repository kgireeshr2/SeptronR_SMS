"""Service — Phase 14: Communications & Notifications."""
from __future__ import annotations
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

import app.repositories.communications_repository as repo
from app.schemas.phase14 import (
    NotificationTemplateCreate, NotificationTemplateUpdate,
    NotificationCreate, BulkMessageCreate, AnnouncementCreate,
    MarkReadRequest,
)


async def list_templates(db: AsyncSession, school_id: str):
    return await repo.list_templates(db, school_id)


async def create_template(db: AsyncSession, school_id: str, data: NotificationTemplateCreate):
    return await repo.create_template(db, school_id, data)


async def update_template(db: AsyncSession, school_id: str, template_id: str, data: NotificationTemplateUpdate):
    return await repo.update_template(db, school_id, template_id, data)


async def delete_template(db: AsyncSession, school_id: str, template_id: str) -> bool:
    return await repo.delete_template(db, school_id, template_id)


async def set_default_template(db: AsyncSession, school_id: str, template_id: str):
    return await repo.set_default_template(db, school_id, template_id)


async def list_notifications(
    db: AsyncSession, school_id: str, user_id: Optional[str] = None, unread_only: bool = False
):
    return await repo.list_notifications(db, school_id, user_id, unread_only)


async def create_notification(db: AsyncSession, school_id: str, data: NotificationCreate):
    return await repo.create_notification(db, school_id, data)


async def mark_read(db: AsyncSession, school_id: str, user_id: str, req: MarkReadRequest) -> int:
    return await repo.mark_notifications_read(db, school_id, user_id, req.notification_ids)


async def list_bulk_messages(db: AsyncSession, school_id: str):
    return await repo.list_bulk_messages(db, school_id)


async def create_bulk_message(
    db: AsyncSession, school_id: str, created_by: UUID, data: BulkMessageCreate
):
    # In production, this would enqueue a task to actually send the messages.
    return await repo.create_bulk_message(db, school_id, created_by, data)


async def list_announcements(db: AsyncSession, school_id: str, active_only: bool = True):
    return await repo.list_announcements(db, school_id, active_only)


async def create_announcement(
    db: AsyncSession, school_id: str, created_by: UUID, data: AnnouncementCreate
):
    return await repo.create_announcement(db, school_id, created_by, data)


async def deactivate_announcement(db: AsyncSession, school_id: str, ann_id: str) -> bool:
    return await repo.deactivate_announcement(db, school_id, ann_id)

