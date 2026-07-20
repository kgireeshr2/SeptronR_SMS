# Feature Prompt 08 — Online Admissions

## Round: 2 of 4 — Core Operations
## Prerequisites: Prompts 01–07 complete (all Round 1)

---

## Objective

Implement the complete admissions workflow: configurable public admission form (no auth), document upload, reference number generation, admin review (approve/reject/waitlist), and auto-creation of student + parent accounts upon approval.

---

## 1. Database Models (`backend/app/models/admissions.py`)

```python
import uuid
from datetime import date, datetime
from sqlalchemy import String, Boolean, Date, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from app.models.base import Base, TimestampMixin
import enum

class AdmissionStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    WAITLISTED = "waitlisted"

class AdmissionForm(Base, TimestampMixin):
    """Student application record."""
    __tablename__ = "admission_forms"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("academic_years.id"), nullable=False, index=True)
    reference_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    status: Mapped[AdmissionStatus] = mapped_column(String(30), default=AdmissionStatus.DRAFT, nullable=False, index=True)

    # Student info
    student_first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    student_last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[str] = mapped_column(String(10), nullable=False)
    applying_class_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("classes.id"), nullable=True)
    previous_school: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Parent info
    parent_name: Mapped[str] = mapped_column(String(200), nullable=False)
    parent_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    parent_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Dynamic fields + documents
    custom_fields: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    documents: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # {doc_type: file_url}

    # Review
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    assigned_class_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("classes.id"), nullable=True)
    assigned_section_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("sections.id"), nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Created student + parent users after approval
    created_student_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("students.id"), nullable=True)


class AdmissionFormConfig(Base, TimestampMixin):
    """Per-school, per-year form configuration."""
    __tablename__ = "admission_form_configs"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    academic_year_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("academic_years.id"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    open_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    close_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    max_applications: Mapped[int | None] = mapped_column(nullable=True)
    fields_config: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    required_documents: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    from sqlalchemy import UniqueConstraint
    __table_args__ = (
        UniqueConstraint("school_id", "academic_year_id", name="uq_admission_config_school_year"),
    )
```

---

## 2. Alembic Migration

```sql
CREATE TABLE admission_form_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    academic_year_id UUID NOT NULL REFERENCES academic_years(id),
    is_active BOOLEAN DEFAULT FALSE NOT NULL,
    open_date TIMESTAMPTZ,
    close_date TIMESTAMPTZ,
    max_applications INTEGER,
    fields_config JSONB,
    required_documents JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT uq_admission_config_school_year UNIQUE (school_id, academic_year_id)
);

CREATE TABLE admission_forms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    academic_year_id UUID NOT NULL REFERENCES academic_years(id),
    reference_number VARCHAR(50) UNIQUE NOT NULL,
    status VARCHAR(30) DEFAULT 'draft' NOT NULL,
    student_first_name VARCHAR(100) NOT NULL,
    student_last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender VARCHAR(10) NOT NULL,
    applying_class_id UUID REFERENCES classes(id),
    previous_school VARCHAR(200),
    parent_name VARCHAR(200) NOT NULL,
    parent_phone VARCHAR(20) NOT NULL,
    parent_email VARCHAR(255),
    address TEXT,
    custom_fields JSONB,
    documents JSONB,
    reviewed_by UUID REFERENCES users(id),
    reviewed_at TIMESTAMPTZ,
    remarks TEXT,
    assigned_class_id UUID REFERENCES classes(id),
    assigned_section_id UUID REFERENCES sections(id),
    submitted_at TIMESTAMPTZ,
    created_student_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX ix_admission_forms_school_status ON admission_forms(school_id, status);
CREATE INDEX ix_admission_forms_reference ON admission_forms(reference_number);
```

---

## 3. Pydantic Schemas

```python
class AdmissionFormConfigCreate(BaseModel):
    academicYearId: UUID
    isActive: bool = False
    openDate: datetime | None = None
    closeDate: datetime | None = None
    maxApplications: int | None = None
    fieldsConfig: list[dict] | None = None  # [{field, label, type, required}]
    requiredDocuments: list[str] | None = None  # ["birth_certificate", "photo"]

class PublicAdmissionApply(BaseModel):
    """No auth required. School slug in URL path."""
    studentFirstName: str
    studentLastName: str
    dateOfBirth: date
    gender: str
    applyingClassId: UUID | None = None
    previousSchool: str | None = None
    parentName: str
    parentPhone: str
    parentEmail: str | None = None
    address: str | None = None
    customFields: dict | None = None

class AdmissionReviewRequest(BaseModel):
    status: AdmissionStatus  # approved / rejected / waitlisted
    remarks: str | None = None
    assignedClassId: UUID | None = None
    assignedSectionId: UUID | None = None

class BulkApproveRequest(BaseModel):
    applicationIds: list[UUID]
    assignedClassId: UUID
    assignedSectionId: UUID

class AdmissionFormResponse(BaseModel):
    id: UUID
    referenceNumber: str
    status: str
    studentFirstName: str
    studentLastName: str
    dateOfBirth: date
    gender: str
    parentName: str
    parentPhone: str
    parentEmail: str | None
    submittedAt: datetime | None
    reviewedAt: datetime | None
    remarks: str | None
    createdStudentId: UUID | None
    model_config = {"from_attributes": True}
```

---

## 4. Repository (`backend/app/repositories/admission_repository.py`)

```python
async def get_admission_config(db, school_id, academic_year_id) -> AdmissionFormConfig | None: ...
async def upsert_admission_config(db, school_id, academic_year_id, data: dict) -> AdmissionFormConfig: ...
async def create_admission_form(db, school_id, academic_year_id, reference_number, data: dict) -> AdmissionForm: ...
async def get_admission_form_by_id(db, form_id, school_id) -> AdmissionForm | None: ...
async def get_admission_form_by_reference(db, reference_number: str) -> AdmissionForm | None: ...
async def list_admission_forms(db, school_id, academic_year_id, status=None, page=1, page_size=20): ...
async def update_admission_status(db, form: AdmissionForm, status: str, reviewed_by, reviewed_at,
                                   remarks: str | None, class_id, section_id) -> AdmissionForm: ...
async def count_applications_by_status(db, school_id, academic_year_id) -> dict: ...
```

---

## 5. Service (`backend/app/services/admission_service.py`)

```python
import secrets, string

async def generate_reference_number(school_id: UUID, year_name: str) -> str:
    """Generate unique reference: ADM-{YEAR_SHORT}-{RANDOM6}. Check uniqueness in DB."""
    short_year = year_name.split("-")[0][-2:]
    for _ in range(10):
        code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        ref = f"ADM-{short_year}-{code}"
        # Check uniqueness; return if unique
    raise RuntimeError("Could not generate unique reference number")

async def get_or_create_config(db, school_id, academic_year_id) -> AdmissionFormConfig:
    """Get config; create default if not exists."""
    ...

async def apply_public(db, school_id: str, data: PublicAdmissionApply) -> dict:
    """
    1. Find school by slug.
    2. Check config.is_active and (now between open_date and close_date).
    3. Check max_applications not exceeded.
    4. Generate reference number.
    5. Create AdmissionForm with status=submitted, submitted_at=now.
    6. Enqueue: send_admission_acknowledgement_task(parent_email, reference_number, school_name).
    Return: {referenceNumber, submittedAt}
    """
    ...

async def review_application(db, form_id, school_id, data: AdmissionReviewRequest,
                              current_user) -> AdmissionForm:
    """
    1. Find form.
    2. Update status, reviewed_by, reviewed_at, remarks, assigned_class/section.
    3. If approved: call student_service.create_from_admission(form, assigned_class, section).
    4. Enqueue notification email/SMS for parent.
    5. Audit log.
    """
    ...

async def bulk_approve(db, school_id, data: BulkApproveRequest, current_user) -> dict:
    """Process each application ID. Return {approved: N, errors: [...]}"""
    ...

async def export_applications_excel(db, school_id, academic_year_id, status=None) -> bytes:
    """Use openpyxl to create xlsx. Return bytes."""
    ...
```

---

## 6. API Endpoints (`backend/app/api/v1/endpoints/admissions.py`)

```
# Public (NO AUTH)
POST   /admissions/apply/{school_slug}         → public admission application
GET    /admissions/status/{reference_number}   → check application status (by reference)
POST   /admissions/{id}/documents              → upload documents for application

# Admin (AUTH REQUIRED)
GET    /admissions/config                      → get form configuration     [admissions:view]
PUT    /admissions/config                      → update config/toggle        [admissions:manage]
GET    /admissions                             → list applications with filters [admissions:view]
GET    /admissions/{id}                        → get application detail     [admissions:view]
PUT    /admissions/{id}/review                 → approve/reject/waitlist     [admissions:approve]
POST   /admissions/bulk-approve                → bulk approve               [admissions:approve]
GET    /admissions/stats                       → count by status             [admissions:view]
GET    /admissions/export                      → download Excel              [admissions:export]
```

---

## 7. Celery Tasks (`backend/app/tasks/emails.py`)

```python
@celery_app.task(queue="emails", max_retries=3)
def send_admission_acknowledgement_task(to_email: str, reference_number: str,
                                         student_name: str, school_name: str):
    subject = f"Admission Application Received — {school_name}"
    body = f"""Dear Parent,

Your admission application for {student_name} has been received.

Reference Number: {reference_number}

You can check your application status at: {settings.FRONTEND_URL}/admissions/status/{reference_number}

Regards,
{school_name}"""
    _send_email(to_email, subject, body)

@celery_app.task(queue="emails", max_retries=3)
def send_admission_decision_task(to_email: str, to_phone: str, reference_number: str,
                                  status: str, remarks: str, school_name: str, login_url: str = ""):
    """Send approval/rejection/waitlist notification."""
    ...
```

---

## 8. Integration: Auto-Create Student on Approval

When `review_application` sets status to `approved`:
```python
# In admission_service.py
if data.status == AdmissionStatus.APPROVED:
    student = await student_service.create_from_admission(
        db=db,
        form=form,
        class_id=data.assignedClassId,
        section_id=data.assignedSectionId,
        academic_year_id=form.academic_year_id,
        created_by=current_user.id,
    )
    form.created_student_id = student.id
```

`student_service.create_from_admission` should:
1. Create `Student` record from form data
2. Create `StudentEnrollment` with assigned class/section
3. Create parent `User` account (username=phone, password=random 8-char)
4. Create `StudentParent` link
5. Enqueue welcome email/SMS with login credentials

---

## 9. Frontend: Types

```typescript
export type AdmissionStatus = 'draft' | 'submitted' | 'under_review' | 'approved' | 'rejected' | 'waitlisted';

export interface AdmissionForm {
  id: string;
  referenceNumber: string;
  status: AdmissionStatus;
  studentFirstName: string;
  studentLastName: string;
  dateOfBirth: string;
  gender: string;
  parentName: string;
  parentPhone: string;
  parentEmail?: string;
  submittedAt?: string;
  reviewedAt?: string;
  remarks?: string;
  createdStudentId?: string;
}

export interface AdmissionStats {
  total: number;
  submitted: number;
  underReview: number;
  approved: number;
  rejected: number;
  waitlisted: number;
}
```

---

## 10. Frontend: API Layer (`frontend/src/api/admissions.ts`)

```typescript
import api from './axios';
import axios from 'axios';  // public endpoints don't need auth

export const submitPublicApplicationApi = async (schoolSlug: string, data: unknown) =>
  axios.post(`/api/v1/admissions/apply/${schoolSlug}`, data);

export const checkApplicationStatusApi = async (reference: string) =>
  axios.get(`/api/v1/admissions/status/${reference}`);

export const getAdmissionsApi = async (params: Record<string, string>) => {
  const res = await api.get('/admissions', { params });
  return res.data;
};

export const reviewApplicationApi = async (id: string, data: unknown) =>
  api.put(`/admissions/${id}/review`, data);

export const bulkApproveApi = async (data: unknown) =>
  api.post('/admissions/bulk-approve', data);

export const getAdmissionStatsApi = async () => {
  const res = await api.get('/admissions/stats');
  return res.data.data;
};

export const exportAdmissionsApi = async (params: Record<string, string>) => {
  const res = await api.get('/admissions/export', { params, responseType: 'blob' });
  return res.data;
};
```

---

## 11. Frontend: Public Application Form (`frontend/src/pages/admissions/PublicAdmissionApplyPage.tsx`)

Route: `/apply/:schoolSlug` (no auth required — accessible without login)

4-step form:
1. **Step 1 — Student Info**: First name, last name, DOB, gender, applying class
2. **Step 2 — Parent Info**: Parent name, phone, email, address
3. **Step 3 — Documents**: Upload required docs (if config requires them)
4. **Step 4 — Review & Submit**: Summary of all entered data + submit

On submit: show success screen with reference number and "Save reference number!" message.

---

## 12. Frontend: Admissions Admin Page (`frontend/src/pages/admissions/AdmissionsPage.tsx`)

Route: `/admissions`

- **Stats bar**: Count cards for each status (Submitted/Under Review/Approved/Rejected/Waitlisted)
- **View toggle**: Table view / Kanban view (columns by status)
- **Table columns**: Reference, Name, DOB, Applying Class, Parent Phone, Status badge, Submitted At, Actions
- **Filter bar**: status dropdown, search by name/reference, date range
- **Actions**: View Detail, Approve, Reject, Waitlist
- **Bulk select + "Bulk Approve" button**: opens dialog to assign class+section for all selected
- **"Export Excel" button**

**Review Modal**: Full application details + status dropdown + remarks + class/section assignment + Save

---

## 13. Frontend: Application Status Page (`frontend/src/pages/admissions/AdmissionStatusPage.tsx`)

Route: `/admissions/status` (public, no auth)

- Reference number input
- On submit: show application status with timeline (Submitted → Under Review → Decision)

---

## 14. Sidebar Navigation

Add:
- `Admissions` → `/admissions` (visible to: `school_admin`, `receptionist`, `principal`)

---

## Verification Checklist

- [ ] `POST /admissions/apply/{slug}` creates application without auth; returns reference number
- [ ] Submitted application triggers acknowledgement email (check Flower task queue)
- [ ] `GET /admissions/status/{ref}` returns application status for any reference
- [ ] Admin review → approved → student record auto-created; `created_student_id` set on form
- [ ] Approved student has `StudentEnrollment` in assigned class/section
- [ ] Parent `User` account created with phone as username; welcome email enqueued
- [ ] Closed form (past close_date or is_active=False) returns 400 error
- [ ] Bulk approve processes all applications and returns success/error counts
- [ ] Excel export includes all fields with status filter
- [ ] Frontend kanban view shows applications in status columns
- [ ] Public form submits without being logged in
