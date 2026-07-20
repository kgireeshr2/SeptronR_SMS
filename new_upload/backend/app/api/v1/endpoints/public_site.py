"""
Public (unauthenticated) endpoints for the per-school website.

Mirrors the public admission pattern in admissions.py: resolve the school by
slug (or verified custom-domain hostname) with NO auth, and only ever return
published content. Served under /api/v1/public.
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.website import EnquiryCreate
from app.services.website_service import CONTENT_SECTIONS, WebsiteService
from app.utils.response import ok

router = APIRouter(prefix="/public", tags=["Public Website"])


@router.get("/resolve")
async def resolve(
    response: Response,
    host: Optional[str] = Query(default=None),
    slug: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Map a Host header (custom domain) or ?slug= to a school's public identity."""
    response.headers["Cache-Control"] = "public, max-age=300"
    data = await WebsiteService(db).resolve_host(host or "", fallback_slug=slug)
    return ok(data, "Resolved")


@router.get("/site/{slug}")
async def get_site(slug: str, response: Response, db: AsyncSession = Depends(get_db)):
    response.headers["Cache-Control"] = "public, max-age=120"
    data = await WebsiteService(db).get_public_site(slug)
    return ok(data, "School website")


@router.get("/site/{slug}/notices")
async def list_notices(slug: str, db: AsyncSession = Depends(get_db)):
    data = await WebsiteService(db).list_public_notices(slug)
    return ok(data, "Notices")


@router.get("/site/{slug}/notices/{notice_id}")
async def get_notice(slug: str, notice_id: str, db: AsyncSession = Depends(get_db)):
    data = await WebsiteService(db).get_public_notice(slug, notice_id)
    return ok(data, "Notice")


@router.get("/site/{slug}/gallery")
async def list_gallery(slug: str, db: AsyncSession = Depends(get_db)):
    data = await WebsiteService(db).list_public_gallery(slug)
    return ok(data, "Gallery")


@router.get("/site/{slug}/events")
async def list_events(slug: str, db: AsyncSession = Depends(get_db)):
    data = await WebsiteService(db).list_public_events(slug)
    return ok(data, "Events")


@router.get("/site/{slug}/content/{section}")
async def list_content(slug: str, section: str, db: AsyncSession = Depends(get_db)):
    """Generic section content: faculty | academics | achievements | facilities | downloads | testimonials."""
    if section not in CONTENT_SECTIONS:
        data: list = []
        return ok(data, "Content")
    data = await WebsiteService(db).list_public_content(slug, section)
    return ok(data, "Content")


@router.post("/site/{slug}/enquiry")
async def submit_enquiry(slug: str, payload: EnquiryCreate, db: AsyncSession = Depends(get_db)):
    data = await WebsiteService(db).submit_enquiry(slug, payload.model_dump(exclude_none=True))
    return ok(data, "Enquiry submitted")
