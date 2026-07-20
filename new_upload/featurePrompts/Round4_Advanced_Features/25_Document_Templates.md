# Feature Prompt 25 — Document Templates

## Round: 4 of 4 — Advanced Features
## Prerequisites: Prompts 09 (Students), 10 (Staff), 16 (Exams)

---

## Objective

Implement a document template system for generating dynamic PDFs: ID cards, transfer certificates (TC), bonafide letters, fee receipts, mark sheets (already in exam module), experience letters, etc.

---

## 1. Database Models (`backend/app/models/document_template.py`)

```python
import uuid
from sqlalchemy import String, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin, SoftDeleteMixin
import enum

class DocumentType(str, enum.Enum):
    STUDENT_ID_CARD = "student_id_card"
    STAFF_ID_CARD = "staff_id_card"
    TRANSFER_CERTIFICATE = "transfer_certificate"
    BONAFIDE = "bonafide"
    FEE_RECEIPT = "fee_receipt"
    MARK_SHEET = "mark_sheet"
    ADMIT_CARD = "admit_card"
    EXPERIENCE_LETTER = "experience_letter"
    SALARY_SLIP = "salary_slip"
    NOC = "noc"
    LEAVING_CERTIFICATE = "leaving_certificate"

class DocumentTemplate(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "document_templates"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    document_type: Mapped[DocumentType] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    html_template: Mapped[str] = mapped_column(Text, nullable=False)  # Jinja2 HTML
    css_styles: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    variables: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list of available vars

    from sqlalchemy import UniqueConstraint
    __table_args__ = (
        UniqueConstraint("school_id", "document_type", "is_default",
                         name="uq_document_template_default"),
    )


class GeneratedDocument(Base, TimestampMixin):
    __tablename__ = "generated_documents"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)   # student / staff
    entity_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    generated_by: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("users.id"), nullable=False)
```

---

## 2. Alembic Migration

```sql
CREATE TABLE document_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    document_type VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    html_template TEXT NOT NULL,
    css_styles TEXT,
    is_default BOOLEAN DEFAULT FALSE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    variables TEXT,
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE generated_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    document_type VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    file_url VARCHAR(500) NOT NULL,
    generated_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX ix_generated_docs_entity ON generated_documents(entity_id, document_type);
```

---

## 3. Service (`backend/app/services/document_service.py`)

```python
async def generate_document(db, school_id, doc_type, entity_id, entity_type, current_user) -> bytes:
    """
    1. Load default DocumentTemplate for doc_type.
    2. Load entity data (student/staff + school).
    3. Render Jinja2 HTML template with context data.
    4. Convert to PDF with WeasyPrint.
    5. Save to uploads/documents/{entity_id}/{doc_type}.pdf.
    6. Record in GeneratedDocument.
    7. Return bytes.
    """

def get_template_variables(doc_type: DocumentType) -> dict:
    """Return context variables for each document type."""
    VARIABLES = {
        DocumentType.BONAFIDE: {
            "student_name", "admission_number", "class_name",
            "academic_year", "school_name", "principal_name", "date"
        },
        DocumentType.TRANSFER_CERTIFICATE: {
            "student_name", "father_name", "dob", "class_name",
            "admission_date", "leaving_date", "conduct", "school_name"
        },
        # ... other types
    }
    return VARIABLES.get(doc_type, {})
```

---

## 4. Default Templates

On school creation / seed, create default HTML templates for:
- `student_id_card`: Front/back card with photo, name, class, barcode
- `staff_id_card`: Front/back card
- `bonafide`: Bonafide certificate with school letterhead
- `transfer_certificate`: TC with standard government format
- `fee_receipt`: Payment receipt (already exists in fee module — link here)

---

## 5. API Endpoints

```
GET    /document-templates?type=               → list templates                [settings:view]
POST   /document-templates                     → create template               [settings:create]
PUT    /document-templates/{id}                → update template HTML          [settings:update]
POST   /document-templates/{id}/set-default    → make default                  [settings:update]
POST   /document-templates/{id}/preview        → preview with sample data      [settings:view]

# Generation
POST   /documents/generate                     → generate PDF                  [students:export]
GET    /documents/history/{entity_id}          → generated docs for entity     [students:view]
```

---

## 6. Frontend: Template Editor Page (`/settings/document-templates`)

- Template type selector (dropdown)
- HTML editor (CodeMirror)
- Live preview panel (iframe with rendered sample)
- Variable reference sidebar
- Save + Set as Default buttons

---

## Verification Checklist

- [ ] Jinja2 template rendering with entity-specific context
- [ ] WeasyPrint PDF generation from rendered HTML
- [ ] Partial unique constraint: only one `is_default=True` per (school_id, document_type)
- [ ] `generate_document` saves file and records in generated_documents
- [ ] Template preview endpoint returns rendered HTML (not PDF) for fast preview
- [ ] Default templates seeded on school creation for all 11 document types
