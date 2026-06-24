"""
Authenticated admin endpoints for managing a school's public website.

Served under /api/v1/website. Every route is permission-gated and school-scoped
via get_school_id (JWT/X-School-Id). Content writes return serialized dicts with
resolved file URLs.
"""
import secrets
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_school_id, permission_required
from app.db.session import get_db
from app.repositories.website_repository import (
    EnquiryRepository,
    GalleryRepository,
    NoticeRepository,
    SchoolDomainRepository,
    WebsiteConfigRepository,
    WebsiteContentRepository,
    WebsiteEventRepository,
)
from app.schemas.website import (
    ContentItemCreate,
    ContentItemUpdate,
    DomainCreate,
    EnquiryStatusUpdate,
    EventCreate,
    EventUpdate,
    GalleryAlbumCreate,
    GalleryAlbumUpdate,
    GalleryImageUpdate,
    NoticeCreate,
    NoticeUpdate,
    PublishUpdate,
    SectionsUpdate,
    WebsiteConfigUpdate,
)
from app.services import website_service as ws
from app.services.website_service import CONTENT_SECTIONS, WebsiteService
from app.utils.file_upload import ALLOWED_DOCUMENT_TYPES, ALLOWED_IMAGE_TYPES, save_upload_file
from app.utils.response import ok

router = APIRouter(prefix="/website", tags=["Website Admin"])


def _folder(school_id) -> str:
    return f"{school_id}/website"


# ── Config ────────────────────────────────────────────────────────────────────

@router.get("/config", dependencies=[Depends(permission_required("website", "view"))])
async def get_config(
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
):
    service = WebsiteService(db)
    cfg = await service.config.get_or_create(str(school_id))
    school = await service.schools.get_by_id(str(school_id))
    profile = await service.profiles.get_by_school(str(school_id))
    await db.commit()
    return ok(ws.serialize_config(cfg, school, profile), "Website config")


@router.put("/config", dependencies=[Depends(permission_required("website", "update"))])
async def update_config(
    data: WebsiteConfigUpdate,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
):
    service = WebsiteService(db)
    cfg = await service.config.upsert(str(school_id), data.model_dump(exclude_none=True))
    school = await service.schools.get_by_id(str(school_id))
    profile = await service.profiles.get_by_school(str(school_id))
    await db.commit()
    return ok(ws.serialize_config(cfg, school, profile), "Website config updated")


@router.put("/publish", dependencies=[Depends(permission_required("website", "publish"))])
async def set_publish(
    data: PublishUpdate,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
):
    cfg = await WebsiteConfigRepository(db).upsert(str(school_id), {"is_published": data.is_published})
    await db.commit()
    return ok({"is_published": cfg.is_published}, "Publish status updated")


@router.put("/sections", dependencies=[Depends(permission_required("website", "update"))])
async def set_sections(
    data: SectionsUpdate,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
):
    cfg = await WebsiteConfigRepository(db).upsert(str(school_id), {"sections": data.sections})
    await db.commit()
    return ok({"sections": cfg.sections}, "Sections updated")


@router.post("/hero-image", dependencies=[Depends(permission_required("website", "update"))])
async def upload_hero(
    file: UploadFile = File(...),
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
):
    path = await save_upload_file(file, folder=_folder(school_id), allowed_types=ALLOWED_IMAGE_TYPES)
    cfg = await WebsiteConfigRepository(db).upsert(str(school_id), {"hero_image_url": path})
    await db.commit()
    return ok({"hero_image_url": ws._url(cfg.hero_image_url)}, "Hero image uploaded")


# ── Gallery ─────────────────────────────────────────────────────────────────

@router.get("/gallery/albums", dependencies=[Depends(permission_required("website", "view"))])
async def list_albums(school_id: UUID = Depends(get_school_id), db: AsyncSession = Depends(get_db)):
    albums = await GalleryRepository(db).list_albums(str(school_id))
    return ok([ws.serialize_album(a) for a in albums], "Albums")


@router.post("/gallery/albums", status_code=201, dependencies=[Depends(permission_required("website", "create"))])
async def create_album(
    data: GalleryAlbumCreate,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
):
    album = await GalleryRepository(db).create_album(str(school_id), data.model_dump())
    await db.commit()
    return ok(ws.serialize_album(album), "Album created")


@router.put("/gallery/albums/{album_id}", dependencies=[Depends(permission_required("website", "update"))])
async def update_album(
    album_id: UUID,
    data: GalleryAlbumUpdate,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
):
    repo = GalleryRepository(db)
    album = await repo.get_album(str(school_id), str(album_id))
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    album = await repo.update_album(album, data.model_dump(exclude_none=True))
    await db.commit()
    return ok(ws.serialize_album(album), "Album updated")


@router.delete("/gallery/albums/{album_id}", dependencies=[Depends(permission_required("website", "delete"))])
async def delete_album(
    album_id: UUID,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
):
    repo = GalleryRepository(db)
    album = await repo.get_album(str(school_id), str(album_id))
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    await repo.delete_album(album)
    await db.commit()
    return ok(None, "Album deleted")


@router.get("/gallery/images", dependencies=[Depends(permission_required("website", "view"))])
async def list_images(
    album_id: str = Query(default=None),
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
):
    images = await GalleryRepository(db).list_images(str(school_id), album_id)
    return ok([ws.serialize_image(i) for i in images], "Images")


@router.post("/gallery/images", status_code=201, dependencies=[Depends(permission_required("website", "create"))])
async def upload_image(
    file: UploadFile = File(...),
    album_id: str = Query(default=None),
    caption: str = Query(default=None),
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
):
    path = await save_upload_file(file, folder=_folder(school_id), allowed_types=ALLOWED_IMAGE_TYPES)
    repo = GalleryRepository(db)
    if album_id:
        album = await repo.get_album(str(school_id), album_id)
        if not album:
            raise HTTPException(status_code=404, detail="Album not found")
    image = await repo.create_image(
        str(school_id), {"image_url": path, "album_id": album_id, "caption": caption}
    )
    await db.commit()
    return ok(ws.serialize_image(image), "Image uploaded")


@router.put("/gallery/images/{image_id}", dependencies=[Depends(permission_required("website", "update"))])
async def update_image(
    image_id: UUID,
    data: GalleryImageUpdate,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
):
    repo = GalleryRepository(db)
    image = await repo.get_image(str(school_id), str(image_id))
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    payload = data.model_dump(exclude_none=True)
    if "album_id" in payload and payload["album_id"]:
        payload["album_id"] = str(payload["album_id"])
    image = await repo.update_image(image, payload)
    await db.commit()
    return ok(ws.serialize_image(image), "Image updated")


@router.delete("/gallery/images/{image_id}", dependencies=[Depends(permission_required("website", "delete"))])
async def delete_image(
    image_id: UUID,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
):
    repo = GalleryRepository(db)
    image = await repo.get_image(str(school_id), str(image_id))
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    await repo.delete_image(image)
    await db.commit()
    return ok(None, "Image deleted")


# ── Notices ─────────────────────────────────────────────────────────────────

@router.get("/notices", dependencies=[Depends(permission_required("website", "view"))])
async def list_notices(school_id: UUID = Depends(get_school_id), db: AsyncSession = Depends(get_db)):
    rows = await NoticeRepository(db).list(str(school_id))
    return ok([ws.serialize_notice(n) for n in rows], "Notices")


@router.post("/notices", status_code=201, dependencies=[Depends(permission_required("website", "create"))])
async def create_notice(
    data: NoticeCreate,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    payload = data.model_dump(exclude_none=True)
    payload["created_by"] = str(current_user.id)
    notice = await NoticeRepository(db).create(str(school_id), payload)
    await db.commit()
    return ok(ws.serialize_notice(notice), "Notice created")


@router.put("/notices/{notice_id}", dependencies=[Depends(permission_required("website", "update"))])
async def update_notice(
    notice_id: UUID,
    data: NoticeUpdate,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
):
    repo = NoticeRepository(db)
    notice = await repo.get(str(school_id), str(notice_id))
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found")
    notice = await repo.update(notice, data.model_dump(exclude_none=True))
    await db.commit()
    return ok(ws.serialize_notice(notice), "Notice updated")


@router.delete("/notices/{notice_id}", dependencies=[Depends(permission_required("website", "delete"))])
async def delete_notice(
    notice_id: UUID,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
):
    repo = NoticeRepository(db)
    notice = await repo.get(str(school_id), str(notice_id))
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found")
    await repo.delete(notice)
    await db.commit()
    return ok(None, "Notice deleted")


@router.post("/notices/attachment", dependencies=[Depends(permission_required("website", "create"))])
async def upload_notice_attachment(
    file: UploadFile = File(...),
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
):
    path = await save_upload_file(
        file, folder=_folder(school_id), allowed_types=ALLOWED_IMAGE_TYPES | ALLOWED_DOCUMENT_TYPES
    )
    return ok({"attachment_url": ws._url(path), "path": path}, "Attachment uploaded")


# ── Events ────────────────────────────────────────────────────────────────────

@router.get("/events", dependencies=[Depends(permission_required("website", "view"))])
async def list_events(school_id: UUID = Depends(get_school_id), db: AsyncSession = Depends(get_db)):
    rows = await WebsiteEventRepository(db).list(str(school_id))
    return ok([ws.serialize_event(e) for e in rows], "Events")


@router.post("/events", status_code=201, dependencies=[Depends(permission_required("website", "create"))])
async def create_event(
    data: EventCreate,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
):
    event = await WebsiteEventRepository(db).create(str(school_id), data.model_dump(exclude_none=True))
    await db.commit()
    return ok(ws.serialize_event(event), "Event created")


@router.put("/events/{event_id}", dependencies=[Depends(permission_required("website", "update"))])
async def update_event(
    event_id: UUID,
    data: EventUpdate,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
):
    repo = WebsiteEventRepository(db)
    event = await repo.get(str(school_id), str(event_id))
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    event = await repo.update(event, data.model_dump(exclude_none=True))
    await db.commit()
    return ok(ws.serialize_event(event), "Event updated")


@router.delete("/events/{event_id}", dependencies=[Depends(permission_required("website", "delete"))])
async def delete_event(
    event_id: UUID,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
):
    repo = WebsiteEventRepository(db)
    event = await repo.get(str(school_id), str(event_id))
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    await repo.delete(event)
    await db.commit()
    return ok(None, "Event deleted")


# ── Generic content sections ────────────────────────────────────────────────

def _validate_section(section: str) -> str:
    if section not in CONTENT_SECTIONS:
        raise HTTPException(status_code=400, detail=f"Unknown section '{section}'")
    return section


@router.get("/content/{section}", dependencies=[Depends(permission_required("website", "view"))])
async def list_content(
    section: str,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
):
    _validate_section(section)
    rows = await WebsiteContentRepository(db).list(str(school_id), section)
    return ok([ws.serialize_content(c) for c in rows], "Content")


@router.post("/content/{section}", status_code=201, dependencies=[Depends(permission_required("website", "create"))])
async def create_content(
    section: str,
    data: ContentItemCreate,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
):
    _validate_section(section)
    item = await WebsiteContentRepository(db).create(str(school_id), section, data.model_dump(exclude_none=True))
    await db.commit()
    return ok(ws.serialize_content(item), "Content created")


@router.put("/content/{section}/{item_id}", dependencies=[Depends(permission_required("website", "update"))])
async def update_content(
    section: str,
    item_id: UUID,
    data: ContentItemUpdate,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
):
    _validate_section(section)
    repo = WebsiteContentRepository(db)
    item = await repo.get(str(school_id), section, str(item_id))
    if not item:
        raise HTTPException(status_code=404, detail="Content item not found")
    item = await repo.update(item, data.model_dump(exclude_none=True))
    await db.commit()
    return ok(ws.serialize_content(item), "Content updated")


@router.delete("/content/{section}/{item_id}", dependencies=[Depends(permission_required("website", "delete"))])
async def delete_content(
    section: str,
    item_id: UUID,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
):
    _validate_section(section)
    repo = WebsiteContentRepository(db)
    item = await repo.get(str(school_id), section, str(item_id))
    if not item:
        raise HTTPException(status_code=404, detail="Content item not found")
    await repo.delete(item)
    await db.commit()
    return ok(None, "Content deleted")


@router.post("/content-image", dependencies=[Depends(permission_required("website", "create"))])
async def upload_content_image(
    file: UploadFile = File(...),
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
):
    path = await save_upload_file(
        file, folder=_folder(school_id), allowed_types=ALLOWED_IMAGE_TYPES | ALLOWED_DOCUMENT_TYPES
    )
    return ok({"image_url": ws._url(path), "path": path}, "File uploaded")


# ── Enquiries inbox ─────────────────────────────────────────────────────────

@router.get("/enquiries", dependencies=[Depends(permission_required("enquiries", "view"))])
async def list_enquiries(
    status: str = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
):
    rows, total = await EnquiryRepository(db).list(str(school_id), status, page, page_size)
    return ok(
        {"items": [ws.serialize_enquiry(e) for e in rows], "total": total, "page": page, "page_size": page_size},
        "Enquiries",
    )


@router.get("/enquiries/stats", dependencies=[Depends(permission_required("enquiries", "view"))])
async def enquiry_stats(school_id: UUID = Depends(get_school_id), db: AsyncSession = Depends(get_db)):
    counts = await EnquiryRepository(db).count_by_status(str(school_id))
    return ok(counts, "Enquiry stats")


@router.get("/enquiries/{enquiry_id}", dependencies=[Depends(permission_required("enquiries", "view"))])
async def get_enquiry(
    enquiry_id: UUID,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
):
    enquiry = await EnquiryRepository(db).get(str(school_id), str(enquiry_id))
    if not enquiry:
        raise HTTPException(status_code=404, detail="Enquiry not found")
    return ok(ws.serialize_enquiry(enquiry), "Enquiry")


@router.put("/enquiries/{enquiry_id}/status", dependencies=[Depends(permission_required("enquiries", "update"))])
async def update_enquiry_status(
    enquiry_id: UUID,
    data: EnquiryStatusUpdate,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    repo = EnquiryRepository(db)
    enquiry = await repo.get(str(school_id), str(enquiry_id))
    if not enquiry:
        raise HTTPException(status_code=404, detail="Enquiry not found")
    enquiry = await repo.update_status(enquiry, data.status, str(current_user.id))
    await db.commit()
    return ok(ws.serialize_enquiry(enquiry), "Enquiry updated")


# ── Custom domains ────────────────────────────────────────────────────────────

@router.get("/domains", dependencies=[Depends(permission_required("domains", "view"))])
async def list_domains(school_id: UUID = Depends(get_school_id), db: AsyncSession = Depends(get_db)):
    rows = await SchoolDomainRepository(db).list_by_school(str(school_id))
    return ok([ws.serialize_domain(d) for d in rows], "Domains")


@router.post("/domains", status_code=201, dependencies=[Depends(permission_required("domains", "manage"))])
async def add_domain(
    data: DomainCreate,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
):
    token = secrets.token_hex(16)
    domain = await SchoolDomainRepository(db).create(str(school_id), data.hostname, token)
    await db.commit()
    result = ws.serialize_domain(domain)
    result["dns_instructions"] = {
        "txt_record": {"host": f"_sms-verify.{domain.hostname}", "value": token},
        "cname_record": {"host": domain.hostname, "value": "septronr-sms.onrender.com"},
    }
    return ok(result, "Domain added — create the DNS records, then verify")


@router.post("/domains/{domain_id}/verify", dependencies=[Depends(permission_required("domains", "manage"))])
async def verify_domain(
    domain_id: UUID,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
):
    repo = SchoolDomainRepository(db)
    domain = await repo.get(str(school_id), str(domain_id))
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    verified = False
    try:
        import dns.resolver  # type: ignore

        answers = dns.resolver.resolve(f"_sms-verify.{domain.hostname}", "TXT")
        for rdata in answers:
            txt = b"".join(rdata.strings).decode() if hasattr(rdata, "strings") else str(rdata).strip('"')
            if txt == domain.verification_token:
                verified = True
                break
    except Exception as e:  # noqa: BLE001 — DNS lookup is best-effort
        raise HTTPException(status_code=400, detail=f"DNS verification failed: {str(e)[:120]}")

    if not verified:
        raise HTTPException(status_code=400, detail="TXT record not found or does not match. DNS may still be propagating.")

    domain = await repo.update(domain, {"is_verified": True, "ssl_status": "pending"})
    await db.commit()
    return ok(ws.serialize_domain(domain), "Domain verified. SSL provisioning pending.")


@router.put("/domains/{domain_id}/primary", dependencies=[Depends(permission_required("domains", "manage"))])
async def set_primary_domain(
    domain_id: UUID,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
):
    repo = SchoolDomainRepository(db)
    domain = await repo.get(str(school_id), str(domain_id))
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    if not domain.is_verified:
        raise HTTPException(status_code=400, detail="Verify the domain before making it primary")
    await repo.clear_primary(str(school_id))
    domain = await repo.update(domain, {"is_primary": True})
    await db.commit()
    return ok(ws.serialize_domain(domain), "Primary domain set")


@router.delete("/domains/{domain_id}", dependencies=[Depends(permission_required("domains", "manage"))])
async def delete_domain(
    domain_id: UUID,
    school_id: UUID = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
):
    repo = SchoolDomainRepository(db)
    domain = await repo.get(str(school_id), str(domain_id))
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    await repo.delete(domain)
    await db.commit()
    return ok(None, "Domain deleted")
