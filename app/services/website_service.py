"""Business logic for the Public School Website feature.

This is where the "only published content is exposed publicly" rules live, plus
serialization that turns stored relative file paths into accessible URLs.
"""
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.foundation import SchoolProfile
from app.models.school import School
from app.repositories.school_repository import SchoolProfileRepository, SchoolRepository
from app.repositories.website_repository import (
    DEFAULT_SECTIONS,
    EnquiryRepository,
    GalleryRepository,
    NoticeRepository,
    WebsiteConfigRepository,
    WebsiteContentRepository,
    WebsiteEventRepository,
)
from app.utils.file_upload import get_file_url

CONTENT_SECTIONS = {"faculty", "academics", "achievements", "facilities", "downloads", "testimonials"}


def _url(path: Optional[str]) -> Optional[str]:
    """Convert a stored relative path to an accessible URL (None-safe)."""
    if not path:
        return None
    # already absolute (http/https or already-prefixed) → leave as-is
    if path.startswith("http://") or path.startswith("https://") or path.startswith("/uploads/"):
        return path
    return get_file_url(path)


# ── Serializers ───────────────────────────────────────────────────────────────

def serialize_config(cfg, school: School, profile: Optional[SchoolProfile]) -> dict:
    sections = cfg.sections or dict(DEFAULT_SECTIONS)
    return {
        "id": str(cfg.id),
        "school_id": str(cfg.school_id),
        "is_published": cfg.is_published,
        "sections": sections,
        "theme_color": cfg.theme_color,
        "secondary_color": cfg.secondary_color,
        "hero_title": cfg.hero_title,
        "hero_subtitle": cfg.hero_subtitle,
        "hero_image_url": _url(cfg.hero_image_url),
        "about_content": cfg.about_content,
        "mission": cfg.mission,
        "vision": cfg.vision,
        "contact_email": cfg.contact_email or (profile.email if profile else None),
        "contact_phone": cfg.contact_phone or (profile.phone if profile else None),
        "contact_address": cfg.contact_address or (profile.address if profile else None),
        "map_embed_url": cfg.map_embed_url,
        "social_links": cfg.social_links or {},
        "seo_title": cfg.seo_title,
        "seo_description": cfg.seo_description,
        # school identity (merged for convenience on the public site)
        "school": {
            "id": str(school.id),
            "name": school.name,
            "slug": school.slug,
            "logo_url": _url(school.logo_url),
            "tagline": profile.tagline if profile else None,
            "established_year": profile.established_year if profile else None,
            "affiliation_board": profile.affiliation_board if profile else None,
            "city": profile.city if profile else None,
            "state": profile.state if profile else None,
        },
    }


def serialize_album(a) -> dict:
    return {
        "id": str(a.id),
        "title": a.title,
        "description": a.description,
        "cover_image_url": _url(a.cover_image_url),
        "is_published": a.is_published,
        "sort_order": a.sort_order,
        "created_at": a.created_at,
    }


def serialize_image(i) -> dict:
    return {
        "id": str(i.id),
        "album_id": str(i.album_id) if i.album_id else None,
        "image_url": _url(i.image_url),
        "caption": i.caption,
        "is_published": i.is_published,
        "sort_order": i.sort_order,
    }


def serialize_notice(n) -> dict:
    return {
        "id": str(n.id),
        "title": n.title,
        "body": n.body,
        "category": n.category,
        "attachment_url": _url(n.attachment_url),
        "publish_at": n.publish_at,
        "expires_at": n.expires_at,
        "is_published": n.is_published,
        "is_pinned": n.is_pinned,
        "created_at": n.created_at,
    }


def serialize_event(e) -> dict:
    return {
        "id": str(e.id),
        "title": e.title,
        "description": e.description,
        "event_date": e.event_date,
        "end_date": e.end_date,
        "location": e.location,
        "image_url": _url(e.image_url),
        "is_published": e.is_published,
        "is_featured": e.is_featured,
    }


def serialize_enquiry(e) -> dict:
    return {
        "id": str(e.id),
        "name": e.name,
        "phone": e.phone,
        "email": e.email,
        "subject": e.subject,
        "message": e.message,
        "status": e.status,
        "source": e.source,
        "responded_by": str(e.responded_by) if e.responded_by else None,
        "responded_at": e.responded_at,
        "created_at": e.created_at,
    }


def serialize_content(c) -> dict:
    return {
        "id": str(c.id),
        "section": c.section,
        "title": c.title,
        "subtitle": c.subtitle,
        "description": c.description,
        "image_url": _url(c.image_url),
        "link_url": c.link_url,
        "meta": c.meta or {},
        "is_published": c.is_published,
        "sort_order": c.sort_order,
    }


def serialize_domain(d) -> dict:
    return {
        "id": str(d.id),
        "school_id": str(d.school_id),
        "hostname": d.hostname,
        "verification_token": d.verification_token,
        "verification_method": d.verification_method,
        "is_verified": d.is_verified,
        "is_primary": d.is_primary,
        "ssl_status": d.ssl_status,
        "created_at": d.created_at,
    }


# ── Service ─────────────────────────────────────────────────────────────────

class WebsiteService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.schools = SchoolRepository(db)
        self.profiles = SchoolProfileRepository(db)
        self.config = WebsiteConfigRepository(db)
        self.gallery = GalleryRepository(db)
        self.notices = NoticeRepository(db)
        self.events = WebsiteEventRepository(db)
        self.enquiries = EnquiryRepository(db)
        self.content = WebsiteContentRepository(db)

    async def _require_published_school(self, slug: str) -> tuple[School, object]:
        school = await self.schools.get_by_slug(slug)
        if not school or not school.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="School not found")
        cfg = await self.config.get_or_create(str(school.id))
        if not cfg.is_published:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="This website is not available")
        return school, cfg

    def _require_section(self, cfg, section: str) -> None:
        sections = cfg.sections or DEFAULT_SECTIONS
        if not sections.get(section, False):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not available")

    async def get_public_site(self, slug: str) -> dict:
        school, cfg = await self._require_published_school(slug)
        profile = await self.profiles.get_by_school(str(school.id))
        return serialize_config(cfg, school, profile)

    async def list_public_notices(self, slug: str) -> list[dict]:
        school, cfg = await self._require_published_school(slug)
        self._require_section(cfg, "notices")
        rows = await self.notices.list_published(str(school.id))
        return [serialize_notice(n) for n in rows]

    async def get_public_notice(self, slug: str, notice_id: str) -> dict:
        school, cfg = await self._require_published_school(slug)
        self._require_section(cfg, "notices")
        notice = await self.notices.get(str(school.id), notice_id)
        if not notice or not notice.is_published:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notice not found")
        return serialize_notice(notice)

    async def list_public_gallery(self, slug: str) -> list[dict]:
        school, cfg = await self._require_published_school(slug)
        self._require_section(cfg, "gallery")
        albums = await self.gallery.list_albums(str(school.id), published_only=True)
        out = []
        for album in albums:
            images = await self.gallery.list_images(str(school.id), str(album.id), published_only=True)
            data = serialize_album(album)
            data["images"] = [serialize_image(i) for i in images]
            out.append(data)
        # Loose images not in any album
        loose = [
            serialize_image(i)
            for i in await self.gallery.list_images(str(school.id), None, published_only=True)
            if i.album_id is None
        ]
        if loose:
            out.append({"id": None, "title": "Photos", "images": loose})
        return out

    async def list_public_events(self, slug: str) -> list[dict]:
        school, cfg = await self._require_published_school(slug)
        self._require_section(cfg, "events")
        rows = await self.events.list(str(school.id), published_only=True)
        return [serialize_event(e) for e in rows]

    async def list_public_content(self, slug: str, section: str) -> list[dict]:
        school, cfg = await self._require_published_school(slug)
        self._require_section(cfg, section)
        rows = await self.content.list(str(school.id), section, published_only=True)
        return [serialize_content(c) for c in rows]

    async def submit_enquiry(self, slug: str, data: dict) -> dict:
        school, cfg = await self._require_published_school(slug)
        self._require_section(cfg, "enquiry")
        enquiry = await self.enquiries.create(str(school.id), data)
        await self.db.commit()
        return {"id": str(enquiry.id), "status": enquiry.status}

    async def resolve_host(self, host: str, fallback_slug: Optional[str] = None) -> dict:
        """Map an incoming Host header (or ?slug=) to a school's public identity."""
        host = (host or "").split(":")[0].strip().lower()
        school = None
        is_custom = False
        if host:
            school = await self.schools.get_by_hostname(host)
            if school:
                is_custom = True
        if not school and fallback_slug:
            school = await self.schools.get_by_slug(fallback_slug)
        if not school or not school.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
        return {
            "slug": school.slug,
            "school_id": str(school.id),
            "name": school.name,
            "logo_url": _url(school.logo_url),
            "is_custom_domain": is_custom,
        }
