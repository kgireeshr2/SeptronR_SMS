"""Service — Phase 17: Document Templates."""
from __future__ import annotations
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

import app.repositories.templates_repository as repo
from app.schemas.phase17 import DocumentTemplateCreate, DocumentTemplateUpdate, BulkPrintRequest


async def list_templates(
    db: AsyncSession, school_id: str, template_type: Optional[str] = None
):
    return await repo.list_templates(db, school_id, template_type)


async def get_template(db: AsyncSession, school_id: str, template_id: str):
    return await repo.get_template(db, school_id, template_id)


async def create_template(
    db: AsyncSession, school_id: str, created_by: UUID, data: DocumentTemplateCreate
):
    return await repo.create_template(db, school_id, created_by, data)


async def update_template(
    db: AsyncSession, school_id: str, template_id: str, data: DocumentTemplateUpdate
):
    obj = await repo.get_template(db, school_id, template_id)
    if not obj:
        raise ValueError("Template not found")
    return await repo.update_template(db, school_id, template_id, data)


async def delete_template(db: AsyncSession, school_id: str, template_id: str) -> bool:
    return await repo.delete_template(db, school_id, template_id)


async def set_default(
    db: AsyncSession, school_id: str, template_id: str
) -> None:
    obj = await repo.get_template(db, school_id, template_id)
    if not obj:
        raise ValueError("Template not found")
    await repo.set_default(db, school_id, template_id, obj.template_type)


async def bulk_print(
    db: AsyncSession, school_id: str, req: BulkPrintRequest
) -> dict:
    """
    In production: enqueue a Celery task to render PDFs for each record_id.
    Returns a task reference.
    """
    template = await repo.get_template(db, school_id, str(req.template_id))
    if not template:
        raise ValueError("Template not found")
    return {
        "status": "queued",
        "template_id": str(req.template_id),
        "record_count": len(req.record_ids),
        "message": "Bulk print job queued. Download link will be available shortly.",
    }

