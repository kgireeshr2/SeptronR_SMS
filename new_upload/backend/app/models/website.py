"""
Public School Website models.

Each school gets a configurable public marketing site (home/about, gallery,
notices & updates, events, enquiry/contact form) plus a set of "modern school"
content sections (faculty, academics, achievements, facilities, downloads,
testimonials) stored generically in `website_content_items`.

All tables are school-scoped (school_id FK) and follow the project conventions:
UUID PKs + created/updated timestamps via the shared mixins, JSON via the
db-agnostic compat alias.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.compat import UUID, JSONB


class SchoolWebsiteConfig(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """1:1 with school. Master publish toggle, section toggles and page content."""
    __tablename__ = "school_website_config"

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), unique=True, nullable=False, index=True
    )
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    # Per-section enable/disable toggle map, e.g. {"gallery": true, "notices": true, ...}
    sections: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    theme_color: Mapped[str] = mapped_column(String(20), nullable=False, server_default="#1e40af")
    secondary_color: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    # Hero / landing
    hero_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    hero_subtitle: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    hero_image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # About
    about_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    mission: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    vision: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Contact (falls back to SchoolProfile when blank)
    contact_email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    contact_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    map_embed_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Social links, e.g. {"facebook": "...", "instagram": "...", ...}
    social_links: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    # SEO
    seo_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    seo_description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)


class GalleryAlbum(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "gallery_albums"

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cover_image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")


class GalleryImage(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "gallery_images"

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    album_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("gallery_albums.id", ondelete="CASCADE"), nullable=True, index=True
    )
    image_url: Mapped[str] = mapped_column(Text, nullable=False)
    caption: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")


class Notice(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Public notices & updates board."""
    __tablename__ = "website_notices"

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, server_default="notice")
    attachment_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    publish_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    is_pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    created_by: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


class WebsiteEvent(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Public events list (separate from the internal academic CalendarEvent)."""
    __tablename__ = "website_events"

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    event_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    is_featured: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")


class Enquiry(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """General enquiry / contact form submission. Lands in the admin inbox."""
    __tablename__ = "website_enquiries"

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    subject: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    # new | read | responded | closed
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="new")
    source: Mapped[str] = mapped_column(String(50), nullable=False, server_default="website")
    responded_by: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class WebsiteContentItem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Generic, section-discriminated content item powering the "modern school"
    sections: faculty, academics (programs), achievements, facilities, downloads,
    testimonials. One table keeps these uniform sections DRY; the `section`
    column selects which page renders it.
    """
    __tablename__ = "website_content_items"

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    # faculty | academics | achievements | facilities | downloads | testimonials
    section: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    subtitle: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    link_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Section-specific extras, e.g. {"qualification": "...", "rating": 5, "level": "primary"}
    meta: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")


class SchoolDomain(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Custom domain mapping for a school's public website (Phase 3)."""
    __tablename__ = "school_domains"

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    hostname: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    verification_token: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    verification_method: Mapped[str] = mapped_column(String(20), nullable=False, server_default="dns_txt")
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    # none | pending | active | failed
    ssl_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
