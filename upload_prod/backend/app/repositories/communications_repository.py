"""Repository — Phase 14: Communications & Notifications."""
from __future__ import annotations
from typing import List, Optional
from uuid import UUID
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.communications import (
    NotificationTemplate, Notification, BulkMessage, Announcement,
)
from app.schemas.phase14 import (
    NotificationTemplateCreate, NotificationTemplateUpdate,
    NotificationCreate, BulkMessageCreate, AnnouncementCreate,
)


# ── Notification Templates ────────────────────────────────────────────────────

async def list_templates(db: AsyncSession, school_id: str) -> List[NotificationTemplate]:
    r = await db.execute(
        select(NotificationTemplate)
        .where(NotificationTemplate.school_id == school_id)
        .order_by(NotificationTemplate.name)
    )
    return list(r.scalars().all())


async def get_template(db: AsyncSession, school_id: str, template_id: str) -> Optional[NotificationTemplate]:
    r = await db.execute(
        select(NotificationTemplate).where(
            NotificationTemplate.id == template_id,
            NotificationTemplate.school_id == school_id,
        )
    )
    return r.scalar_one_or_none()


async def create_template(
    db: AsyncSession, school_id: str, data: NotificationTemplateCreate
) -> NotificationTemplate:
    data_dict = data.model_dump()
    # Schema uses 'channels' (List[str]) but model attribute is 'channel' (str)
    channels_val = data_dict.pop("channels", None)
    channel_str = ",".join(channels_val) if isinstance(channels_val, list) else (channels_val or "")
    # Schema uses 'body_template' but model attribute is 'body'
    body_val = data_dict.pop("body_template", None)
    obj = NotificationTemplate(
        id=uuid.uuid4(), school_id=school_id,
        channel=channel_str, body=body_val, **data_dict
    )
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def update_template(
    db: AsyncSession, school_id: str, template_id: str, data: NotificationTemplateUpdate
) -> Optional[NotificationTemplate]:
    vals = {k: v for k, v in data.model_dump(exclude_none=True).items()}
    if not vals:
        return await get_template(db, school_id, template_id)
    # Schema uses 'channels' (List[str]) but model attribute is 'channel' (str)
    channels_val = vals.pop("channels", None)
    if channels_val is not None:
        vals["channel"] = ",".join(channels_val) if isinstance(channels_val, list) else channels_val
    # Schema uses 'body_template' but model attribute is 'body'
    body_val = vals.pop("body_template", None)
    if body_val is not None:
        vals["body"] = body_val
    vals["updated_at"] = datetime.now(timezone.utc)
    await db.execute(
        update(NotificationTemplate)
        .where(NotificationTemplate.id == template_id, NotificationTemplate.school_id == school_id)
        .values(**vals)
    )
    return await get_template(db, school_id, template_id)


async def delete_template(db: AsyncSession, school_id: str, template_id: str) -> bool:
    obj = await get_template(db, school_id, template_id)
    if not obj:
        return False
    await db.delete(obj)
    return True


async def set_default_template(
    db: AsyncSession, school_id: str, template_id: str
) -> Optional[NotificationTemplate]:
    """Mark a template as the default for its event_trigger, clearing any previous default."""
    obj = await get_template(db, school_id, template_id)
    if not obj:
        return None
    # Clear existing defaults for this trigger
    await db.execute(
        update(NotificationTemplate)
        .where(
            NotificationTemplate.school_id == school_id,
            NotificationTemplate.event_trigger == obj.event_trigger,
        )
        .values(is_default=False, updated_at=datetime.now(timezone.utc))
    )
    # Set the selected one as default
    await db.execute(
        update(NotificationTemplate)
        .where(NotificationTemplate.id == template_id)
        .values(is_default=True, updated_at=datetime.now(timezone.utc))
    )
    await db.flush()
    return await get_template(db, school_id, template_id)


# ── Notifications ─────────────────────────────────────────────────────────────

async def list_notifications(
    db: AsyncSession, school_id: str, user_id: Optional[str] = None,
    unread_only: bool = False
) -> List[Notification]:
    q = select(Notification).where(Notification.school_id == school_id)
    if user_id:
        q = q.where(Notification.user_id == user_id)
    if unread_only:
        q = q.where(Notification.is_read == False)
    q = q.order_by(Notification.created_at.desc())
    r = await db.execute(q)
    return list(r.scalars().all())


async def create_notification(
    db: AsyncSession, school_id: str, data: NotificationCreate
) -> Notification:
    data_dict = data.model_dump()
    # Schema uses 'extra_data' but model attribute is 'data'
    extra_data_val = data_dict.pop("extra_data", None)
    # 'scheduled_at' is not a real column on Notification model
    data_dict.pop("scheduled_at", None)
    obj = Notification(id=uuid.uuid4(), school_id=school_id, data=extra_data_val, **data_dict)
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def mark_notifications_read(
    db: AsyncSession, school_id: str, user_id: str, notification_ids: List[UUID]
) -> int:
    result = await db.execute(
        update(Notification)
        .where(
            Notification.school_id == school_id,
            Notification.user_id == user_id,
            Notification.id.in_(notification_ids),
        )
        .values(is_read=True)
    )
    return result.rowcount


# ── Bulk Messages ─────────────────────────────────────────────────────────────

async def list_bulk_messages(db: AsyncSession, school_id: str) -> List[BulkMessage]:
    r = await db.execute(
        select(BulkMessage)
        .where(BulkMessage.school_id == school_id)
        .order_by(BulkMessage.created_at.desc())
    )
    return list(r.scalars().all())


async def create_bulk_message(
    db: AsyncSession, school_id: str, created_by: UUID, data: BulkMessageCreate
) -> BulkMessage:
    data_dict = data.model_dump()
    # Schema uses 'channel' (str) but model uses 'channels' (JSONB list)
    channel_val = data_dict.pop("channel", None)
    channels = [channel_val] if channel_val else []
    # Schema uses 'audience' but model uses 'target_type'
    audience_val = data_dict.pop("audience", "all")
    # 'audience_filter' not a direct model column — discard
    data_dict.pop("audience_filter", None)
    obj = BulkMessage(
        id=uuid.uuid4(),
        school_id=school_id,
        created_by=created_by,
        channels=channels,
        target_type=audience_val,
        target_ids=[],
        **data_dict,
    )
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


# ── Announcements ─────────────────────────────────────────────────────────────

async def list_announcements(
    db: AsyncSession, school_id: str, active_only: bool = True
) -> List[Announcement]:
    q = select(Announcement).where(Announcement.school_id == school_id)
    if active_only:
        q = q.where(Announcement.is_published == True)  # is_published maps to is_active column
    q = q.order_by(Announcement.created_at.desc())
    r = await db.execute(q)
    return list(r.scalars().all())


async def get_announcement(
    db: AsyncSession, school_id: str, ann_id: str
) -> Optional[Announcement]:
    r = await db.execute(
        select(Announcement).where(
            Announcement.id == ann_id,
            Announcement.school_id == school_id,
        )
    )
    return r.scalar_one_or_none()


async def create_announcement(
    db: AsyncSession, school_id: str, created_by: UUID, data: AnnouncementCreate
) -> Announcement:
    data_dict = data.model_dump()
    # Schema uses 'body' but model attribute is 'content' (mapped to 'body' column)
    body_val = data_dict.pop("body", None)
    # 'audience_filter' not a direct model column
    data_dict.pop("audience_filter", None)
    # Schema uses 'publish_at' but model attribute is 'published_at' (column 'publish_at')
    publish_at_val = data_dict.pop("publish_at", None)
    obj = Announcement(
        id=uuid.uuid4(),
        school_id=school_id,
        created_by=created_by,
        content=body_val,
        published_at=publish_at_val,
        is_published=True,  # publish immediately upon creation
        **data_dict,
    )
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def deactivate_announcement(
    db: AsyncSession, school_id: str, ann_id: str
) -> bool:
    obj = await get_announcement(db, school_id, ann_id)
    if not obj:
        return False
    obj.is_published = False  # is_published maps to is_active column
    return True

