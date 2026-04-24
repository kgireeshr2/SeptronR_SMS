"""API Endpoints — Phase 14: Communications & Notifications."""
from __future__ import annotations
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_school_id, get_current_user, permission_required
from app.schemas.phase14 import (
    NotificationTemplateCreate, NotificationTemplateUpdate, NotificationTemplateResponse,
    NotificationCreate, NotificationResponse,
    BulkMessageCreate, BulkMessageResponse,
    AnnouncementCreate, AnnouncementResponse,
    MarkReadRequest,
)
import app.services.communications_service as svc

templates_router = APIRouter(prefix="/communications/templates", tags=["communications"])
notifications_router = APIRouter(prefix="/notifications", tags=["notifications"])
bulk_router = APIRouter(prefix="/communications/bulk-messages", tags=["communications"])
announcements_router = APIRouter(prefix="/announcements", tags=["communications"])


# ── Notification Templates ────────────────────────────────────────────────────

@templates_router.get("", response_model=List[NotificationTemplateResponse])
async def list_templates(
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(permission_required("communications", "read")),
):
    return await svc.list_templates(db, school_id)


@templates_router.post("", response_model=NotificationTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    data: NotificationTemplateCreate,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(permission_required("communications", "write")),
):
    return await svc.create_template(db, school_id, data)


@templates_router.put("/{template_id}", response_model=NotificationTemplateResponse)
async def update_template(
    template_id: UUID,
    data: NotificationTemplateUpdate,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(permission_required("communications", "write")),
):
    obj = await svc.update_template(db, school_id, str(template_id), data)
    if not obj:
        raise HTTPException(status_code=404, detail="Template not found")
    return obj


@templates_router.post("/{template_id}/set-default", response_model=NotificationTemplateResponse)
async def set_default_template(
    template_id: UUID,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(permission_required("communications", "write")),
):
    obj = await svc.set_default_template(db, school_id, str(template_id))
    if not obj:
        raise HTTPException(status_code=404, detail="Template not found")
    return obj


@templates_router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: UUID,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(permission_required("communications", "delete")),
):
    ok = await svc.delete_template(db, school_id, str(template_id))
    if not ok:
        raise HTTPException(status_code=404, detail="Template not found")


# ── Notifications ─────────────────────────────────────────────────────────────

@notifications_router.get("", response_model=List[NotificationResponse])
async def list_my_notifications(
    unread_only: bool = False,
    school_id: str = Depends(get_school_id),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await svc.list_notifications(db, school_id, user_id=str(current_user.id), unread_only=unread_only)


@notifications_router.post("/mark-read")
async def mark_read(
    req: MarkReadRequest,
    school_id: str = Depends(get_school_id),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count = await svc.mark_read(db, school_id, str(current_user.id), req)
    return {"marked": count}


@notifications_router.post("", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def create_notification(
    data: NotificationCreate,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(permission_required("communications", "write")),
):
    return await svc.create_notification(db, school_id, data)


# ── Bulk Messages ─────────────────────────────────────────────────────────────

@bulk_router.get("", response_model=List[BulkMessageResponse])
async def list_bulk(
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(permission_required("communications", "read")),
):
    return await svc.list_bulk_messages(db, school_id)


@bulk_router.post("", response_model=BulkMessageResponse, status_code=status.HTTP_201_CREATED)
async def send_bulk(
    data: BulkMessageCreate,
    school_id: str = Depends(get_school_id),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(permission_required("communications", "write")),
):
    return await svc.create_bulk_message(db, school_id, current_user.id, data)


# ── Announcements ─────────────────────────────────────────────────────────────

@announcements_router.get("", response_model=List[AnnouncementResponse])
async def list_announcements(
    active_only: bool = True,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
):
    return await svc.list_announcements(db, school_id, active_only)


@announcements_router.post("", response_model=AnnouncementResponse, status_code=status.HTTP_201_CREATED)
async def create_announcement(
    data: AnnouncementCreate,
    school_id: str = Depends(get_school_id),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(permission_required("communications", "write")),
):
    return await svc.create_announcement(db, school_id, current_user.id, data)


@announcements_router.delete("/{ann_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_announcement(
    ann_id: UUID,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(permission_required("communications", "delete")),
):
    ok = await svc.deactivate_announcement(db, school_id, str(ann_id))
    if not ok:
        raise HTTPException(status_code=404, detail="Announcement not found")

