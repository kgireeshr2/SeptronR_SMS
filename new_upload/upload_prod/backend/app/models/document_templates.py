"""
SQLAlchemy models — Phase 17: Document Templates
Table: document_templates (single table, ENUM template_type)
⚠️ Cross-checked with Database_Schema.sql — NO separate template_types or print_templates tables
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, ForeignKey, String, Text, UniqueConstraint
from app.models.compat import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class DocumentTemplate(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "document_templates"
    __table_args__ = (
        UniqueConstraint("school_id", "template_type", "template_name",
                         name="doc_templates_school_type_name_ux"),
    )

    school_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="NO ACTION"), nullable=False, index=True
    )
    template_name: Mapped[str] = mapped_column(String(200), nullable=False)
    # ⚠️ ENUM document_template_type in DB:
    # student_id_front|student_id_back|staff_id_front|staff_id_back|
    # admit_card|fee_receipt|report_card|transfer_certificate|
    # bonafide_certificate|character_certificate|payslip|custom
    template_type: Mapped[str] = mapped_column(String(50), nullable=False)
    canvas_width_mm: Mapped[Optional[float]] = mapped_column(nullable=True)
    canvas_height_mm: Mapped[Optional[float]] = mapped_column(nullable=True)
    # drag-and-drop element positions/styles
    layout_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    # compiled Jinja2 HTML for rendering
    template_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
