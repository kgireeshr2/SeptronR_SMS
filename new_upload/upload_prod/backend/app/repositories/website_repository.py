"""Data-access layer for the Public School Website feature.

Every query is school-scoped EXCEPT SchoolDomainRepository.get_by_hostname,
which is the global hostname -> school resolution entry point.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.website import (
    Enquiry,
    GalleryAlbum,
    GalleryImage,
    Notice,
    SchoolDomain,
    SchoolWebsiteConfig,
    WebsiteContentItem,
    WebsiteEvent,
)


DEFAULT_SECTIONS = {
    "home": True,
    "about": True,
    "gallery": True,
    "notices": True,
    "events": True,
    "admissions": True,
    "enquiry": True,
    "contact": True,
    # modern-school extras (off by default — admin enables as content is added)
    "faculty": False,
    "academics": False,
    "achievements": False,
    "facilities": False,
    "downloads": False,
    "testimonials": False,
}


class WebsiteConfigRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_school(self, school_id: str) -> Optional[SchoolWebsiteConfig]:
        result = await self.db.execute(
            select(SchoolWebsiteConfig).where(SchoolWebsiteConfig.school_id == school_id)
        )
        return result.scalar_one_or_none()

    async def create_default(self, school_id: str) -> SchoolWebsiteConfig:
        cfg = SchoolWebsiteConfig(
            school_id=school_id,
            is_published=False,
            sections=dict(DEFAULT_SECTIONS),
            theme_color="#1e40af",
        )
        self.db.add(cfg)
        await self.db.flush()
        await self.db.refresh(cfg)
        return cfg

    async def get_or_create(self, school_id: str) -> SchoolWebsiteConfig:
        cfg = await self.get_by_school(school_id)
        if cfg is None:
            cfg = await self.create_default(school_id)
        return cfg

    async def upsert(self, school_id: str, data: dict) -> SchoolWebsiteConfig:
        cfg = await self.get_or_create(school_id)
        for key, value in data.items():
            setattr(cfg, key, value)
        await self.db.flush()
        await self.db.refresh(cfg)
        return cfg


class GalleryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Albums ──
    async def list_albums(self, school_id: str, published_only: bool = False) -> list[GalleryAlbum]:
        q = select(GalleryAlbum).where(GalleryAlbum.school_id == school_id)
        if published_only:
            q = q.where(GalleryAlbum.is_published.is_(True))
        q = q.order_by(GalleryAlbum.sort_order, GalleryAlbum.created_at.desc())
        return list((await self.db.execute(q)).scalars().all())

    async def get_album(self, school_id: str, album_id: str) -> Optional[GalleryAlbum]:
        result = await self.db.execute(
            select(GalleryAlbum).where(GalleryAlbum.id == album_id, GalleryAlbum.school_id == school_id)
        )
        return result.scalar_one_or_none()

    async def create_album(self, school_id: str, data: dict) -> GalleryAlbum:
        album = GalleryAlbum(school_id=school_id, **data)
        self.db.add(album)
        await self.db.flush()
        await self.db.refresh(album)
        return album

    async def update_album(self, album: GalleryAlbum, data: dict) -> GalleryAlbum:
        for k, v in data.items():
            setattr(album, k, v)
        await self.db.flush()
        await self.db.refresh(album)
        return album

    async def delete_album(self, album: GalleryAlbum) -> None:
        await self.db.delete(album)
        await self.db.flush()

    # ── Images ──
    async def list_images(
        self, school_id: str, album_id: Optional[str] = None, published_only: bool = False
    ) -> list[GalleryImage]:
        q = select(GalleryImage).where(GalleryImage.school_id == school_id)
        if album_id:
            q = q.where(GalleryImage.album_id == album_id)
        if published_only:
            q = q.where(GalleryImage.is_published.is_(True))
        q = q.order_by(GalleryImage.sort_order, GalleryImage.created_at.desc())
        return list((await self.db.execute(q)).scalars().all())

    async def get_image(self, school_id: str, image_id: str) -> Optional[GalleryImage]:
        result = await self.db.execute(
            select(GalleryImage).where(GalleryImage.id == image_id, GalleryImage.school_id == school_id)
        )
        return result.scalar_one_or_none()

    async def create_image(self, school_id: str, data: dict) -> GalleryImage:
        image = GalleryImage(school_id=school_id, **data)
        self.db.add(image)
        await self.db.flush()
        await self.db.refresh(image)
        return image

    async def update_image(self, image: GalleryImage, data: dict) -> GalleryImage:
        for k, v in data.items():
            setattr(image, k, v)
        await self.db.flush()
        await self.db.refresh(image)
        return image

    async def delete_image(self, image: GalleryImage) -> None:
        await self.db.delete(image)
        await self.db.flush()


class NoticeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list(self, school_id: str) -> list[Notice]:
        q = (
            select(Notice)
            .where(Notice.school_id == school_id)
            .order_by(Notice.is_pinned.desc(), Notice.publish_at.desc().nullslast(), Notice.created_at.desc())
        )
        return list((await self.db.execute(q)).scalars().all())

    async def list_published(self, school_id: str) -> list[Notice]:
        now = datetime.now(timezone.utc)
        q = (
            select(Notice)
            .where(
                Notice.school_id == school_id,
                Notice.is_published.is_(True),
                or_(Notice.publish_at.is_(None), Notice.publish_at <= now),
                or_(Notice.expires_at.is_(None), Notice.expires_at > now),
            )
            .order_by(Notice.is_pinned.desc(), Notice.publish_at.desc().nullslast(), Notice.created_at.desc())
        )
        return list((await self.db.execute(q)).scalars().all())

    async def get(self, school_id: str, notice_id: str) -> Optional[Notice]:
        result = await self.db.execute(
            select(Notice).where(Notice.id == notice_id, Notice.school_id == school_id)
        )
        return result.scalar_one_or_none()

    async def create(self, school_id: str, data: dict) -> Notice:
        notice = Notice(school_id=school_id, **data)
        self.db.add(notice)
        await self.db.flush()
        await self.db.refresh(notice)
        return notice

    async def update(self, notice: Notice, data: dict) -> Notice:
        for k, v in data.items():
            setattr(notice, k, v)
        await self.db.flush()
        await self.db.refresh(notice)
        return notice

    async def delete(self, notice: Notice) -> None:
        await self.db.delete(notice)
        await self.db.flush()


class WebsiteEventRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list(self, school_id: str, published_only: bool = False) -> list[WebsiteEvent]:
        q = select(WebsiteEvent).where(WebsiteEvent.school_id == school_id)
        if published_only:
            q = q.where(WebsiteEvent.is_published.is_(True))
        q = q.order_by(WebsiteEvent.event_date.desc().nullslast(), WebsiteEvent.created_at.desc())
        return list((await self.db.execute(q)).scalars().all())

    async def get(self, school_id: str, event_id: str) -> Optional[WebsiteEvent]:
        result = await self.db.execute(
            select(WebsiteEvent).where(WebsiteEvent.id == event_id, WebsiteEvent.school_id == school_id)
        )
        return result.scalar_one_or_none()

    async def create(self, school_id: str, data: dict) -> WebsiteEvent:
        event = WebsiteEvent(school_id=school_id, **data)
        self.db.add(event)
        await self.db.flush()
        await self.db.refresh(event)
        return event

    async def update(self, event: WebsiteEvent, data: dict) -> WebsiteEvent:
        for k, v in data.items():
            setattr(event, k, v)
        await self.db.flush()
        await self.db.refresh(event)
        return event

    async def delete(self, event: WebsiteEvent) -> None:
        await self.db.delete(event)
        await self.db.flush()


class EnquiryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, school_id: str, data: dict) -> Enquiry:
        enquiry = Enquiry(school_id=school_id, status="new", source="website", **data)
        self.db.add(enquiry)
        await self.db.flush()
        await self.db.refresh(enquiry)
        return enquiry

    async def list(
        self, school_id: str, status: Optional[str], page: int, page_size: int
    ) -> tuple[list[Enquiry], int]:
        base = select(Enquiry).where(Enquiry.school_id == school_id)
        if status:
            base = base.where(Enquiry.status == status)
        total = (await self.db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
        rows = (
            await self.db.execute(
                base.order_by(Enquiry.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
            )
        ).scalars().all()
        return list(rows), total

    async def get(self, school_id: str, enquiry_id: str) -> Optional[Enquiry]:
        result = await self.db.execute(
            select(Enquiry).where(Enquiry.id == enquiry_id, Enquiry.school_id == school_id)
        )
        return result.scalar_one_or_none()

    async def update_status(self, enquiry: Enquiry, status: str, responded_by: Optional[str]) -> Enquiry:
        enquiry.status = status
        if status in ("responded", "closed"):
            enquiry.responded_by = responded_by
            enquiry.responded_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(enquiry)
        return enquiry

    async def count_by_status(self, school_id: str) -> dict[str, int]:
        result = await self.db.execute(
            select(Enquiry.status, func.count())
            .where(Enquiry.school_id == school_id)
            .group_by(Enquiry.status)
        )
        return {status: count for status, count in result.all()}


class WebsiteContentRepository:
    """Generic CRUD for section-discriminated content items."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list(self, school_id: str, section: str, published_only: bool = False) -> list[WebsiteContentItem]:
        q = select(WebsiteContentItem).where(
            WebsiteContentItem.school_id == school_id, WebsiteContentItem.section == section
        )
        if published_only:
            q = q.where(WebsiteContentItem.is_published.is_(True))
        q = q.order_by(WebsiteContentItem.sort_order, WebsiteContentItem.created_at.desc())
        return list((await self.db.execute(q)).scalars().all())

    async def get(self, school_id: str, section: str, item_id: str) -> Optional[WebsiteContentItem]:
        result = await self.db.execute(
            select(WebsiteContentItem).where(
                WebsiteContentItem.id == item_id,
                WebsiteContentItem.school_id == school_id,
                WebsiteContentItem.section == section,
            )
        )
        return result.scalar_one_or_none()

    async def create(self, school_id: str, section: str, data: dict) -> WebsiteContentItem:
        item = WebsiteContentItem(school_id=school_id, section=section, **data)
        self.db.add(item)
        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def update(self, item: WebsiteContentItem, data: dict) -> WebsiteContentItem:
        for k, v in data.items():
            setattr(item, k, v)
        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def delete(self, item: WebsiteContentItem) -> None:
        await self.db.delete(item)
        await self.db.flush()


class SchoolDomainRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_hostname(self, hostname: str, verified_only: bool = True) -> Optional[SchoolDomain]:
        """Global (NOT school-scoped) — the hostname -> school resolution entry point."""
        q = select(SchoolDomain).where(func.lower(SchoolDomain.hostname) == hostname.lower())
        if verified_only:
            q = q.where(SchoolDomain.is_verified.is_(True))
        return (await self.db.execute(q)).scalar_one_or_none()

    async def list_by_school(self, school_id: str) -> list[SchoolDomain]:
        result = await self.db.execute(
            select(SchoolDomain).where(SchoolDomain.school_id == school_id).order_by(SchoolDomain.created_at.desc())
        )
        return list(result.scalars().all())

    async def get(self, school_id: str, domain_id: str) -> Optional[SchoolDomain]:
        result = await self.db.execute(
            select(SchoolDomain).where(SchoolDomain.id == domain_id, SchoolDomain.school_id == school_id)
        )
        return result.scalar_one_or_none()

    async def create(self, school_id: str, hostname: str, verification_token: str) -> SchoolDomain:
        domain = SchoolDomain(
            school_id=school_id,
            hostname=hostname.lower(),
            verification_token=verification_token,
            verification_method="dns_txt",
            is_verified=False,
            ssl_status="none",
        )
        self.db.add(domain)
        await self.db.flush()
        await self.db.refresh(domain)
        return domain

    async def update(self, domain: SchoolDomain, data: dict) -> SchoolDomain:
        for k, v in data.items():
            setattr(domain, k, v)
        await self.db.flush()
        await self.db.refresh(domain)
        return domain

    async def clear_primary(self, school_id: str) -> None:
        for d in await self.list_by_school(school_id):
            if d.is_primary:
                d.is_primary = False
        await self.db.flush()

    async def delete(self, domain: SchoolDomain) -> None:
        await self.db.delete(domain)
        await self.db.flush()
