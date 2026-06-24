"""Schemas for Phase 17 — Document Templates."""
from __future__ import annotations
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime


class DocumentTemplateCreate(BaseModel):
    template_name: str
    template_type: str
    canvas_width_mm: float = 85.6
    canvas_height_mm: float = 54.0
    layout_json: Optional[Any] = None
    template_html: Optional[str] = None
    is_default: bool = False
    is_active: bool = True


class DocumentTemplateUpdate(BaseModel):
    template_name: Optional[str] = None
    canvas_width_mm: Optional[float] = None
    canvas_height_mm: Optional[float] = None
    layout_json: Optional[Any] = None
    template_html: Optional[str] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


class DocumentTemplateResponse(DocumentTemplateCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    school_id: UUID
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime


class BulkPrintRequest(BaseModel):
    template_id: UUID
    record_ids: list[UUID]
