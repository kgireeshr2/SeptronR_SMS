"""Pydantic schemas for the Public School Website feature."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ── Website config ────────────────────────────────────────────────────────────

class WebsiteConfigUpdate(BaseModel):
    is_published: Optional[bool] = None
    sections: Optional[dict] = None
    theme_color: Optional[str] = None
    secondary_color: Optional[str] = None
    hero_title: Optional[str] = None
    hero_subtitle: Optional[str] = None
    hero_image_url: Optional[str] = None
    about_content: Optional[str] = None
    mission: Optional[str] = None
    vision: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_address: Optional[str] = None
    map_embed_url: Optional[str] = None
    social_links: Optional[dict] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None


class PublishUpdate(BaseModel):
    is_published: bool


class SectionsUpdate(BaseModel):
    sections: dict


# ── Gallery ─────────────────────────────────────────────────────────────────

class GalleryAlbumCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    is_published: bool = True
    sort_order: int = 0


class GalleryAlbumUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    cover_image_url: Optional[str] = None
    is_published: Optional[bool] = None
    sort_order: Optional[int] = None


class GalleryImageUpdate(BaseModel):
    caption: Optional[str] = None
    album_id: Optional[UUID] = None
    is_published: Optional[bool] = None
    sort_order: Optional[int] = None


# ── Notices ─────────────────────────────────────────────────────────────────

class NoticeCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    body: Optional[str] = None
    category: str = "notice"
    attachment_url: Optional[str] = None
    publish_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_published: bool = True
    is_pinned: bool = False


class NoticeUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    category: Optional[str] = None
    attachment_url: Optional[str] = None
    publish_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_published: Optional[bool] = None
    is_pinned: Optional[bool] = None


# ── Events ────────────────────────────────────────────────────────────────────

class EventCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: Optional[str] = None
    event_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    location: Optional[str] = None
    image_url: Optional[str] = None
    is_published: bool = True
    is_featured: bool = False


class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    event_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    location: Optional[str] = None
    image_url: Optional[str] = None
    is_published: Optional[bool] = None
    is_featured: Optional[bool] = None


# ── Enquiries ─────────────────────────────────────────────────────────────────

class EnquiryCreate(BaseModel):
    """Public submission — clients may NOT set status/source."""
    name: str = Field(min_length=1, max_length=150)
    phone: Optional[str] = Field(default=None, max_length=20)
    email: Optional[EmailStr] = None
    subject: Optional[str] = Field(default=None, max_length=255)
    message: str = Field(min_length=1)


class EnquiryStatusUpdate(BaseModel):
    status: str  # new | read | responded | closed


# ── Generic content items (faculty / academics / achievements / ...) ────────────

class ContentItemCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    subtitle: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    link_url: Optional[str] = None
    meta: Optional[dict] = None
    is_published: bool = True
    sort_order: int = 0


class ContentItemUpdate(BaseModel):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    link_url: Optional[str] = None
    meta: Optional[dict] = None
    is_published: Optional[bool] = None
    sort_order: Optional[int] = None


# ── Domains ───────────────────────────────────────────────────────────────────

class DomainCreate(BaseModel):
    hostname: str = Field(min_length=3, max_length=255)


# ── Responses (used where from_attributes serialization is helpful) ─────────────

class WebsiteConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    is_published: bool
    sections: Optional[dict] = None
    theme_color: str
    secondary_color: Optional[str] = None
    hero_title: Optional[str] = None
    hero_subtitle: Optional[str] = None
    hero_image_url: Optional[str] = None
    about_content: Optional[str] = None
    mission: Optional[str] = None
    vision: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_address: Optional[str] = None
    map_embed_url: Optional[str] = None
    social_links: Optional[dict] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
