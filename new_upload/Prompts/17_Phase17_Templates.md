# PHASE 17 — ID CARD & TEMPLATE BUILDER

## Pre-Requisite
Phases 1–16 complete. Students and staff exist with photos.

## Objective
Visual drag-and-drop template builder for ID cards, certificates, and report card layouts. Templates configurable per school with custom branding, QR codes, and bulk PDF generation.

---

## 17.1 Database Tables (Verify Exist)

```sql
-- ⚠️ ACTUAL SCHEMA (cross-checked with Database_Schema.sql)

-- Section 22: Document Templates — Single table (NOT separate template_types + print_templates)
-- ⚠️ NO separate template_types, print_templates, or bulk_print_jobs tables.
-- A single 'document_templates' table handles all template types.

document_templates (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    template_name VARCHAR(200) NOT NULL,
    template_type document_template_type NOT NULL,  -- ENUM type
        -- ENUM values: student_id_front|student_id_back|staff_id_front|staff_id_back|
        --              admit_card|fee_receipt|report_card|transfer_certificate|
        --              bonafide_certificate|character_certificate|payslip|custom
    canvas_width_mm DECIMAL(6,2),     -- e.g., 85.6 for ID card
    canvas_height_mm DECIMAL(6,2),    -- e.g., 54.0 for ID card
    layout_json JSONB,          -- drag-and-drop element positions/styles
    template_html TEXT,         -- compiled Jinja2 HTML for render
    is_default BOOL DEFAULT FALSE,
    is_active BOOL DEFAULT TRUE,
    created_by UUID FK→users, created_at, updated_at,
    UNIQUE(school_id, template_type, template_name)
)
-- NOTE: Bulk print job tracking should be done via a separate 'print_jobs' table
-- if needed (add via Alembic migration). Use Celery task state (task_id) for progress.
```

> **Migration note**: The original prompt references `print_templates`, `template_types`, and `bulk_print_jobs` — none of these exist. All templates are stored in `document_templates` with a `template_type` ENUM. If separate bulk job tracking is needed, create a `print_jobs` table via Alembic migration with fields: `id, school_id, template_id, target_type, target_ids JSONB, status, output_url, celery_task_id`.


---

## 17.2 Service Layer

```python
async def render_template(template_id: str, context: dict) -> bytes:
    """
    1. Load document_templates by id (uses template_html + layout_json)
    2. Render with Jinja2Engine (context = student/staff/school data)
    3. WeasyPrint: HTML → PDF bytes; canvas size from canvas_width_mm × canvas_height_mm
    """

async def get_default_template(school_id: str, template_type: str) -> DocumentTemplate:
    """
    Load document_templates WHERE school_id=:sid AND template_type=:type AND is_default=TRUE
    """

async def render_bulk_pdfs(school_id: str, template_id: str, entity_ids: list, task_id: str) -> str:
    """
    Celery task body:
    1. Load document_templates
    2. For each entity_id: build context (student data or staff data based on template_type)
    3. Render PDF per entity using WeasyPrint
    4. Merge all PDFs using pypdf (PdfWriter.append)
    5. Upload merged PDF to storage
    6. Return output_url
    Use Celery task state for progress: update_state(state='PROGRESS', meta={'current': i, 'total': n})
    """
```

```
# Templates (⚠️ All in document_templates table, no separate template_types)
GET  /api/v1/templates                          → list (filter: template_type) [templates:view]
POST /api/v1/templates                          → create [templates:manage]
GET  /api/v1/templates/{id}                     → get template
PUT  /api/v1/templates/{id}                     → update [templates:manage]
DELETE /api/v1/templates/{id}                   → delete
POST /api/v1/templates/{id}/set-default         → set as default for its template_type
POST /api/v1/templates/{id}/preview             → render preview with sample data → PDF bytes
GET  /api/v1/templates/{id}/render/{entity_id}  → render for specific student/staff → PDF
POST /api/v1/templates/{id}/bulk-render         → async bulk render → {task_id}
GET  /api/v1/templates/jobs/{task_id}/status    → Celery task state {state, current, total}
GET  /api/v1/templates/jobs/{task_id}/download  → download merged PDF [templates:print]

# Available template_type values for filtering/creating:
# student_id_front | student_id_back | staff_id_front | staff_id_back |
# admit_card | fee_receipt | report_card | transfer_certificate |
# bonafide_certificate | character_certificate | payslip | custom
```

---

## 17.4 Frontend Pages

### `/admin/templates` Page (Permission: `templates:view`)

**Template List Tab:**
- Cards per template type: Student ID Card, Staff ID Card, Bonafide, TC, Certificate
- Each card shows current default template + edit/new buttons

**Template Editor:**
- HTML/CSS code editor (Monaco Editor or CodeMirror)
- Live preview pane (rendered via API)
- Available variables panel: {{student.name}}, {{student.photo_url}}, {{school.logo_url}} etc.
- Page size selector
- Save Draft + Set as Default + Preview buttons

**Bulk Print Tab:**
- Select template type → pick class/section or individual students
- "Generate PDFs" → shows job progress bar
- Download when done

### `frontend/src/api/templates.ts`
```typescript
export const templatesApi = {
  list: () => api.get('/templates'),
  create: (data: TemplateCreate) => api.post('/templates', data),
  update: (id: string, data: Partial<TemplateCreate>) => api.put(`/templates/${id}`, data),
  preview: (id: string, sampleData: dict) =>
    api.post(`/templates/${id}/preview`, sampleData, { responseType: 'blob' }),
  render: (id: string, entityId: string) =>
    api.get(`/templates/${id}/render/${entityId}`, { responseType: 'blob' }),
  bulkRender: (id: string, targetIds: string[]) =>
    api.post(`/templates/${id}/bulk-render`, { target_ids: targetIds }),
  getJobStatus: (jobId: string) => api.get(`/templates/jobs/${jobId}`),
  downloadJob: (jobId: string) =>
    api.get(`/templates/jobs/${jobId}/download`, { responseType: 'blob' }),
};
```

---

## 17.5 Built-in Template Variables

```
# Student ID Card Variables
{{student.full_name}}, {{student.admission_number}}, {{student.photo_url}}
{{student.date_of_birth}}, {{student.blood_group}}, {{student.gender}}
{{enrollment.class_name}}, {{enrollment.section_name}}
{{parent.phone}} (primary contact)
{{school.school_name}}, {{school.logo_url}}, {{school.address}}
{{school.phone}}, {{school.tagline}}
{{qr_code_url}}  ← base64 QR code of student admission_number

# Staff ID Card Variables
{{staff.full_name}}, {{staff.employee_id}}, {{staff.photo_url}}
{{staff.designation_name}}, {{staff.department_name}}
{{staff.joining_date}}, {{staff.phone}}, {{staff.email}}
{{school.school_name}}, {{school.logo_url}}
{{qr_code_url}}  ← QR of employee_id

# Certificate Variables
{{student.full_name}}, {{school.school_name}}, {{school.principal_name}}
{{school.principal_signature_url}}, {{school.seal_url}}
{{current_date}}, {{enrollment.class_name}}, {{enrollment.academic_year_name}}
```

---

## 17.6 Celery Tasks

```python
@celery.task(queue="pdf_generation", bind=True)
def generate_bulk_pdf_task(self, job_id: str):
    """
    Process bulk_print_job:
    - Render each entity PDF
    - Merge into single PDF using pypdf
    - Upload to storage
    - Update job status and output_file_url
    """
```

---

## 17.7 Tests

```python
async def test_template_render_produces_bytes(): ...
async def test_bulk_job_created_and_queued(): ...
async def test_bulk_job_poll_shows_progress(): ...
async def test_default_template_only_one_per_type(): ...
```

---

## 17.8 Deliverables Checklist

- [ ] Template CRUD (HTML/CSS editor)
- [ ] Default template designation per template_key
- [ ] Live preview rendering via API (WeasyPrint)
- [ ] Per-entity PDF render (student, staff)
- [ ] Bulk PDF generation job with progress tracking
- [ ] Merged PDF download when job complete
- [ ] QR code generation in templates (use `qrcode` Python package)
- [ ] Built-in sample templates for student ID card, staff ID card, bonafide certificate
- [ ] Monaco/CodeMirror editor in frontend with variable hints
