"""API Endpoints — Phase 17: Document Templates."""
from __future__ import annotations
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_school_id, get_current_user, permission_required
from app.schemas.phase17 import (
    DocumentTemplateCreate, DocumentTemplateUpdate, DocumentTemplateResponse,
    BulkPrintRequest,
)
import app.services.templates_service as svc

templates_router = APIRouter(prefix="/document-templates", tags=["templates"])


@templates_router.get("", response_model=List[DocumentTemplateResponse])
async def list_templates(
    template_type: Optional[str] = None,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(permission_required("templates", "read")),
):
    return await svc.list_templates(db, school_id, template_type)


@templates_router.get("/{template_id}", response_model=DocumentTemplateResponse)
async def get_template(
    template_id: UUID,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(permission_required("templates", "read")),
):
    obj = await svc.get_template(db, school_id, str(template_id))
    if not obj:
        raise HTTPException(status_code=404, detail="Template not found")
    return obj


@templates_router.post("", response_model=DocumentTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    data: DocumentTemplateCreate,
    school_id: str = Depends(get_school_id),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(permission_required("templates", "write")),
):
    return await svc.create_template(db, school_id, current_user.id, data)


@templates_router.put("/{template_id}", response_model=DocumentTemplateResponse)
async def update_template(
    template_id: UUID,
    data: DocumentTemplateUpdate,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(permission_required("templates", "write")),
):
    try:
        return await svc.update_template(db, school_id, str(template_id), data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@templates_router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: UUID,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(permission_required("templates", "delete")),
):
    ok = await svc.delete_template(db, school_id, str(template_id))
    if not ok:
        raise HTTPException(status_code=404, detail="Template not found")


@templates_router.post("/{template_id}/set-default", status_code=status.HTTP_204_NO_CONTENT)
async def set_default(
    template_id: UUID,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(permission_required("templates", "write")),
):
    try:
        await svc.set_default(db, school_id, str(template_id))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@templates_router.post("/bulk-print")
async def bulk_print(
    req: BulkPrintRequest,
    school_id: str = Depends(get_school_id),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(permission_required("templates", "write")),
):
    try:
        return await svc.bulk_print(db, school_id, req)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

