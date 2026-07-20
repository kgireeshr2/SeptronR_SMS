"""API Endpoints — Phase 14: Communications & Notifications."""
from __future__ import annotations
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
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


@notifications_router.post("/mark-all-read")
async def mark_all_read(
    school_id: str = Depends(get_school_id),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark all notifications as read for the current user."""
    from sqlalchemy import update as sa_update
    from app.models.communications import Notification
    result = await db.execute(
        sa_update(Notification)
        .where(
            Notification.school_id == school_id,
            Notification.user_id == str(current_user.id),
            Notification.is_read == False,
        )
        .values(is_read=True)
    )
    await db.commit()
    return {"marked": result.rowcount}


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


@announcements_router.patch("/{ann_id}/read")
async def ack_announcement(ann_id: UUID, current_user=Depends(get_current_user)):
    """Per-user announcement read-ack (no server-side state today — accepted for the mobile app)."""
    return {"ok": True}


# ── In-app notification center (shared by web + mobile) ───────────────────────

@notifications_router.get("/unread-count")
async def unread_count(
    school_id: str = Depends(get_school_id),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.communications import Notification
    from sqlalchemy import func
    n = (await db.execute(
        select(func.count()).select_from(Notification).where(
            Notification.school_id == school_id,
            Notification.user_id == str(current_user.id),
            Notification.is_read == False,  # noqa: E712
        )
    )).scalar() or 0
    return {"unread": int(n)}


@notifications_router.patch("/read-all")
async def mark_all_read_patch(
    school_id: str = Depends(get_school_id),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.communications import Notification
    res = await db.execute(
        sa_update(Notification).where(
            Notification.school_id == school_id,
            Notification.user_id == str(current_user.id),
            Notification.is_read == False,  # noqa: E712
        ).values(is_read=True)
    )
    await db.commit()
    return {"marked": res.rowcount}


@notifications_router.patch("/{notif_id}/read")
async def mark_one_read(
    notif_id: UUID,
    school_id: str = Depends(get_school_id),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.communications import Notification
    res = await db.execute(
        sa_update(Notification).where(
            Notification.id == notif_id,
            Notification.school_id == school_id,
            Notification.user_id == str(current_user.id),
        ).values(is_read=True)
    )
    await db.commit()
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"ok": True}


# ── Notification preferences (per-user opt-out) ───────────────────────────────

class PreferenceItem(BaseModel):
    channel: str
    event_trigger: str = "all"
    enabled: bool = True


@notifications_router.get("/preferences")
async def get_preferences(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.communications import NotificationPreference
    rows = (await db.execute(
        select(NotificationPreference).where(NotificationPreference.user_id == str(current_user.id))
    )).scalars().all()
    return [{"channel": p.channel, "event_trigger": p.event_trigger, "enabled": p.enabled} for p in rows]


@notifications_router.put("/preferences")
async def set_preferences(
    prefs: List[PreferenceItem],
    school_id: str = Depends(get_school_id),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.communications import NotificationPreference
    for item in prefs:
        existing = (await db.execute(
            select(NotificationPreference).where(
                NotificationPreference.user_id == str(current_user.id),
                NotificationPreference.channel == item.channel,
                NotificationPreference.event_trigger == item.event_trigger,
            )
        )).scalar_one_or_none()
        if existing:
            existing.enabled = item.enabled
        else:
            db.add(NotificationPreference(
                school_id=school_id, user_id=str(current_user.id),
                channel=item.channel, event_trigger=item.event_trigger, enabled=item.enabled,
            ))
    await db.commit()
    return {"ok": True, "count": len(prefs)}


# ── Delivery reports (MessageLog) ─────────────────────────────────────────────

logs_router = APIRouter(prefix="/communications/message-logs", tags=["communications"])


@logs_router.get("")
async def list_message_logs(
    channel: Optional[str] = None,
    msg_status: Optional[str] = None,
    limit: int = 100,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(permission_required("communications", "read")),
):
    from app.models.communications import MessageLog
    q = select(MessageLog).where(MessageLog.school_id == school_id)
    if channel:
        q = q.where(MessageLog.channel == channel)
    if msg_status:
        q = q.where(MessageLog.status == msg_status)
    q = q.order_by(MessageLog.created_at.desc()).limit(min(limit, 500))
    rows = (await db.execute(q)).scalars().all()
    return [
        {
            "id": str(m.id), "channel": m.channel, "status": m.status,
            "recipient_phone": m.recipient_phone, "recipient_email": m.recipient_email,
            "event_trigger": m.event_trigger, "subject": m.subject,
            "error_message": m.error_message, "provider_message_id": m.provider_message_id,
            "sent_at": m.sent_at, "created_at": m.created_at,
        }
        for m in rows
    ]


# ── Device tokens (push registration — web + mobile) ──────────────────────────

devices_router = APIRouter(prefix="/devices", tags=["notifications"])


class DeviceRegister(BaseModel):
    token: str
    provider: str = "expo"      # expo | webpush | fcm
    platform: Optional[str] = None  # ios | android | web


@devices_router.post("/register")
async def register_device(
    data: DeviceRegister,
    school_id: str = Depends(get_school_id),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.communications import DeviceToken
    from datetime import datetime, timezone
    existing = (await db.execute(
        select(DeviceToken).where(
            DeviceToken.user_id == str(current_user.id), DeviceToken.token == data.token
        )
    )).scalar_one_or_none()
    if existing:
        existing.is_active = True
        existing.provider = data.provider
        existing.platform = data.platform
        existing.last_seen = datetime.now(timezone.utc)
    else:
        db.add(DeviceToken(
            school_id=school_id, user_id=str(current_user.id), token=data.token,
            provider=data.provider, platform=data.platform,
            last_seen=datetime.now(timezone.utc),
        ))
    await db.commit()
    return {"ok": True}


@devices_router.post("/unregister")
async def unregister_device(
    data: DeviceRegister,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.communications import DeviceToken
    await db.execute(
        sa_update(DeviceToken).where(
            DeviceToken.user_id == str(current_user.id), DeviceToken.token == data.token
        ).values(is_active=False)
    )
    await db.commit()
    return {"ok": True}


@devices_router.get("/web-push-key")
async def web_push_public_key():
    """VAPID public key for browser subscription (safe to expose)."""
    return {"public_key": settings.VAPID_PUBLIC_KEY or ""}

