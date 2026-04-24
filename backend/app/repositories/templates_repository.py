"""Repository — Phase 17: Document Templates."""
from __future__ import annotations
from typing import List, Optional
from uuid import UUID
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document_templates import DocumentTemplate
from app.schemas.phase17 import DocumentTemplateCreate, DocumentTemplateUpdate


async def list_templates(
    db: AsyncSession,
    school_id: str,
    template_type: Optional[str] = None,
) -> List[DocumentTemplate]:
    q = select(DocumentTemplate).where(
        DocumentTemplate.school_id == school_id,
        DocumentTemplate.is_active == True,
    )
    if template_type:
        q = q.where(DocumentTemplate.template_type == template_type)
    q = q.order_by(DocumentTemplate.template_name)
    r = await db.execute(q)
    return list(r.scalars().all())


async def get_template(
    db: AsyncSession, school_id: str, template_id: str
) -> Optional[DocumentTemplate]:
    r = await db.execute(
        select(DocumentTemplate).where(
            DocumentTemplate.id == template_id,
            DocumentTemplate.school_id == school_id,
        )
    )
    return r.scalar_one_or_none()


async def create_template(
    db: AsyncSession, school_id: str, created_by: UUID, data: DocumentTemplateCreate
) -> DocumentTemplate:
    obj = DocumentTemplate(
        id=uuid.uuid4(),
        school_id=school_id,
        created_by=created_by,
        **data.model_dump(),
    )
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def update_template(
    db: AsyncSession, school_id: str, template_id: str, data: DocumentTemplateUpdate
) -> Optional[DocumentTemplate]:
    vals = {k: v for k, v in data.model_dump(exclude_none=True).items()}
    if vals:
        vals["updated_at"] = datetime.now(timezone.utc)
        await db.execute(
            update(DocumentTemplate)
            .where(
                DocumentTemplate.id == template_id,
                DocumentTemplate.school_id == school_id,
            )
            .values(**vals)
            .execution_options(synchronize_session="fetch")
        )
        await db.flush()
    return await get_template(db, school_id, template_id)


async def delete_template(
    db: AsyncSession, school_id: str, template_id: str
) -> bool:
    obj = await get_template(db, school_id, template_id)
    if not obj:
        return False
    obj.is_active = False
    return True


async def set_default(
    db: AsyncSession, school_id: str, template_id: str, template_type: str
) -> None:
    """Clear existing default for the type, then set the new one."""
    await db.execute(
        update(DocumentTemplate)
        .where(
            DocumentTemplate.school_id == school_id,
            DocumentTemplate.template_type == template_type,
        )
        .values(is_default=False)
    )
    await db.execute(
        update(DocumentTemplate)
        .where(
            DocumentTemplate.id == template_id,
            DocumentTemplate.school_id == school_id,
        )
        .values(is_default=True)
    )

