# PHASE 3 — SCHOOL SETTINGS, ACADEMIC YEAR & ONLINE ADMISSIONS

## Pre-Requisite
Phase 2 complete. Auth, JWT, RBAC working. Super admin can log in.

## Objective
Implement school profile/settings management, academic year & terms CRUD, and the fully functional online admissions module (public form + admin review workflow).

---

## 3.1 Database Tables (Verify Exist)

```sql
-- Section 2: Foundation
schools (id UUID PK, name VARCHAR(200), slug VARCHAR(100) UNIQUE,
         is_active BOOL, created_at, updated_at)

school_profile (id UUID PK, school_id UUID UNIQUE FK→schools,
    school_name, tagline, address, city, state, country DEFAULT 'India',
    pincode, phone, email, website, logo_url, favicon_url,
    established_year SMALLINT, affiliation_board, affiliation_number,
    principal_name, principal_signature_url, school_seal_url,
    timezone DEFAULT 'Asia/Kolkata', currency DEFAULT 'INR',
    date_format DEFAULT 'DD/MM/YYYY', academic_start_month SMALLINT DEFAULT 4,
    updated_at)

school_settings (id UUID PK, school_id UUID FK→schools,
    category VARCHAR(50), key VARCHAR(100), value TEXT,
    data_type VARCHAR(20) DEFAULT 'string',   -- string|integer|boolean|json
    is_public BOOL DEFAULT FALSE,
    updated_by UUID FK→users, updated_at,
    UNIQUE(school_id, key))

-- Section 5: Academic
academic_years (id UUID PK, school_id UUID FK→schools,
    name VARCHAR(20), start_date DATE, end_date DATE,
    is_current BOOL DEFAULT FALSE, is_locked BOOL DEFAULT FALSE,
    created_at, updated_at,
    CHECK(end_date > start_date))
-- Partial UNIQUE INDEX: UNIQUE(school_id) WHERE is_current = TRUE

academic_terms (id UUID PK, school_id UUID FK→schools,
    academic_year_id UUID FK→academic_years,
    name VARCHAR(50), start_date DATE, end_date DATE,
    is_current BOOL DEFAULT FALSE,
    created_at, updated_at,
    CHECK(end_date > start_date))
-- Partial UNIQUE INDEX: UNIQUE(academic_year_id) WHERE is_current = TRUE

-- Section 6: Admissions
admission_form_configs (id UUID PK, school_id UUID FK→schools,
    academic_year_id UUID FK→academic_years,
    fields_config JSONB DEFAULT '[]',      -- [{field, label, required, type}]
    required_documents JSONB DEFAULT '[]', -- [{doc_type, label, required}]
    open_date DATE, close_date DATE,
    is_active BOOL DEFAULT FALSE,
    created_at, updated_at)

admission_forms (id UUID PK, school_id UUID FK→schools,
    academic_year_id UUID FK→academic_years,
    reference_number VARCHAR(30),
    applicant_name VARCHAR(200), date_of_birth DATE,
    gender VARCHAR(10), applying_for_class_id UUID FK→classes (nullable),
    parent_name, parent_phone, parent_email, address TEXT,
    previous_school VARCHAR(200),
    documents JSONB DEFAULT '[]',  -- [{doc_type, file_url}]
    status admission_status DEFAULT 'draft',
        -- ENUM: draft|submitted|under_review|approved|rejected|waitlisted
    assigned_admission_number VARCHAR(50),
    submitted_at TIMESTAMPTZ, reviewed_by UUID FK→users,
    reviewed_at TIMESTAMPTZ, remarks TEXT,
    created_at, updated_at,
    UNIQUE(school_id, reference_number))
```

---

## 3.2 SQLAlchemy Models

### `backend/app/models/foundation.py`
```python
# School, SchoolProfile, SchoolSettings
```

### `backend/app/models/academic.py`
```python
# AcademicYear, AcademicTerm
```

### `backend/app/models/admissions.py`
```python
# AdmissionFormConfig, AdmissionForm
# Include Python Enum: AdmissionStatus (draft, submitted, under_review, approved, rejected, waitlisted)
```

---

## 3.3 Pydantic Schemas

### School Profile
```python
class SchoolProfileUpdate(BaseModel):
    school_name: Optional[str]
    tagline: Optional[str]
    address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    country: Optional[str]
    pincode: Optional[str]
    phone: Optional[str]
    email: Optional[EmailStr]
    website: Optional[str]
    established_year: Optional[int]
    affiliation_board: Optional[str]
    affiliation_number: Optional[str]
    principal_name: Optional[str]
    timezone: Optional[str]
    currency: Optional[str]
    date_format: Optional[str]
    academic_start_month: Optional[int] = Field(ge=1, le=12)

class SchoolProfileResponse(SchoolProfileUpdate):
    id: UUID
    school_id: UUID
    logo_url: Optional[str]
    favicon_url: Optional[str]
    principal_signature_url: Optional[str]
    school_seal_url: Optional[str]
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
```

### School Settings
```python
class SettingUpdate(BaseModel):
    value: str

class BulkSettingsUpdate(BaseModel):
    settings: Dict[str, str]  # {key: value}

class SettingResponse(BaseModel):
    key: str
    value: str
    category: str
    data_type: str
    is_public: bool
```

### Academic Year
```python
class AcademicYearCreate(BaseModel):
    name: str                  # "2025-2026"
    start_date: date
    end_date: date

class AcademicYearUpdate(BaseModel):
    name: Optional[str]
    start_date: Optional[date]
    end_date: Optional[date]

class AcademicYearResponse(BaseModel):
    id: UUID
    school_id: UUID
    name: str
    start_date: date
    end_date: date
    is_current: bool
    is_locked: bool
    created_at: datetime
    terms: Optional[List[AcademicTermResponse]]
    model_config = ConfigDict(from_attributes=True)

class AcademicTermCreate(BaseModel):
    name: str
    start_date: date
    end_date: date

class AcademicTermResponse(BaseModel):
    id: UUID
    academic_year_id: UUID
    name: str
    start_date: date
    end_date: date
    is_current: bool
```

### Admissions
```python
class AdmissionFormConfigCreate(BaseModel):
    academic_year_id: UUID
    fields_config: List[Dict]
    required_documents: List[Dict]
    open_date: Optional[date]
    close_date: Optional[date]
    is_active: bool = False

class AdmissionApplicationCreate(BaseModel):
    school_slug: str              # to identify which school (public form)
    academic_year_id: UUID
    applicant_name: str
    date_of_birth: date
    gender: str
    applying_for_class_id: Optional[UUID]
    parent_name: str
    parent_phone: str
    parent_email: Optional[EmailStr]
    address: Optional[str]
    previous_school: Optional[str]

class AdmissionReviewRequest(BaseModel):
    status: Literal["approved", "rejected", "waitlisted", "under_review"]
    remarks: Optional[str]
    assigned_admission_number: Optional[str]   # required when approving

class AdmissionFormResponse(BaseModel):
    id: UUID
    reference_number: str
    applicant_name: str
    date_of_birth: date
    gender: str
    status: str
    parent_name: Optional[str]
    parent_phone: Optional[str]
    submitted_at: Optional[datetime]
    reviewed_at: Optional[datetime]
    remarks: Optional[str]
    documents: List[Dict]
    model_config = ConfigDict(from_attributes=True)
```

---

## 3.4 Repository Layer

### `backend/app/repositories/school_repository.py`
```python
class SchoolRepository:
    async def get_by_id(self, school_id: str) -> Optional[School]: ...
    async def get_by_slug(self, slug: str) -> Optional[School]: ...
    async def create(self, data: dict) -> School: ...
    async def update(self, school_id: str, data: dict) -> School: ...
    async def list_all(self, page: int, page_size: int) -> tuple: ...  # super admin

class SchoolProfileRepository:
    async def get_by_school(self, school_id: str) -> Optional[SchoolProfile]: ...
    async def upsert(self, school_id: str, data: dict) -> SchoolProfile: ...

class SchoolSettingsRepository:
    async def get_all(self, school_id: str) -> List[SchoolSetting]: ...
    async def get_by_category(self, school_id: str, category: str) -> List[SchoolSetting]: ...
    async def get_value(self, school_id: str, key: str) -> Optional[str]: ...
    async def upsert(self, school_id: str, key: str, value: str, updated_by: str): ...
    async def bulk_upsert(self, school_id: str, settings: dict, updated_by: str): ...
```

### `backend/app/repositories/academic_repository.py`
```python
class AcademicYearRepository:
    async def list_by_school(self, school_id: str) -> List[AcademicYear]: ...
    async def get_current(self, school_id: str) -> Optional[AcademicYear]: ...
    async def get_by_id(self, year_id: str) -> Optional[AcademicYear]: ...
    async def create(self, school_id: str, data: dict) -> AcademicYear: ...
    async def update(self, year_id: str, data: dict) -> AcademicYear: ...
    async def set_current(self, school_id: str, year_id: str) -> AcademicYear:
        """Unset is_current on all years for school, then set on target."""
    async def lock(self, year_id: str) -> AcademicYear: ...

class AcademicTermRepository:
    async def list_by_year(self, year_id: str) -> List[AcademicTerm]: ...
    async def create(self, year_id: str, school_id: str, data: dict) -> AcademicTerm: ...
    async def set_current(self, year_id: str, term_id: str) -> AcademicTerm: ...
```

### `backend/app/repositories/admission_repository.py`
```python
class AdmissionRepository:
    async def get_config(self, school_id: str, year_id: str) -> Optional[AdmissionFormConfig]: ...
    async def upsert_config(self, school_id: str, data: dict) -> AdmissionFormConfig: ...
    async def list_forms(self, school_id: str, filters: dict, page: int, page_size: int): ...
    async def get_form_by_id(self, form_id: str) -> Optional[AdmissionForm]: ...
    async def get_form_by_reference(self, school_id: str, ref: str) -> Optional[AdmissionForm]: ...
    async def create_form(self, data: dict) -> AdmissionForm: ...
    async def update_status(self, form_id: str, data: dict) -> AdmissionForm: ...
    async def count_by_status(self, school_id: str, year_id: str) -> dict: ...
```

---

## 3.5 Service Layer

### `backend/app/services/academic_service.py`
```python
async def create_academic_year(school_id: str, data: AcademicYearCreate) -> AcademicYear:
    """Validate dates don't overlap with existing years, then create."""

async def set_current_year(school_id: str, year_id: str) -> AcademicYear:
    """Transactionally unset current on all, set on target."""

async def lock_year(year_id: str) -> AcademicYear:
    """Mark is_locked=True. Prevents edits on locked years in all modules."""
```

### `backend/app/services/admission_service.py`
```python
async def submit_application(school_slug: str, data: AdmissionApplicationCreate, files: List) -> AdmissionForm:
    """
    1. Resolve school by slug
    2. Check admission config is_active and within open/close dates
    3. Generate reference_number = '{SLUG-UPPER}-{YEAR}-{YYYYMMDDHHMMSS}'
    4. Upload documents to storage
    5. Create AdmissionForm with status='submitted'
    6. Enqueue Celery: send_admission_acknowledgement_email(parent_email, ref_no)
    7. Return form with reference_number
    """

async def review_application(form_id: str, reviewer_id: str, data: AdmissionReviewRequest) -> AdmissionForm:
    """
    1. Load form
    2. Update status + reviewed_by + reviewed_at + remarks
    3. If approved:
       a. Create student record (calls student_service.create_from_admission)
       b. Create parent user + student_parent record
       c. Enqueue email: send_admission_approved_email(parent_email, admission_number)
       d. Enqueue notification: ADMISSION_APPROVED
    4. If rejected: enqueue rejection email
    """

async def bulk_approve(form_ids: List[str], class_section_map: dict, reviewer_id: str) -> int:
    """Bulk approve with class/section assignment."""
```

---

## 3.6 API Endpoints

### School Profile
```
GET  /api/v1/schools/profile         → get school profile
PUT  /api/v1/schools/profile         → update profile [settings:update]
POST /api/v1/schools/profile/logo    → upload logo (multipart/form-data) [settings:update]
GET  /api/v1/schools/settings        → get all settings grouped by category
PUT  /api/v1/schools/settings        → bulk update settings [settings:update]
GET  /api/v1/schools/settings/{key}  → get single setting value
PUT  /api/v1/schools/settings/{key}  → update single setting
```

### Academic Years
```
GET    /api/v1/academic-years                → list all years
POST   /api/v1/academic-years                → create year [academic_years:create]
GET    /api/v1/academic-years/{id}           → get year with terms
PUT    /api/v1/academic-years/{id}           → update year
DELETE /api/v1/academic-years/{id}           → delete (block if has enrollments)
POST   /api/v1/academic-years/{id}/set-current → make current year
POST   /api/v1/academic-years/{id}/lock      → lock year

GET    /api/v1/academic-years/{id}/terms     → list terms for year
POST   /api/v1/academic-years/{id}/terms     → create term
PUT    /api/v1/academic-years/{id}/terms/{tid} → update term
POST   /api/v1/academic-years/{id}/terms/{tid}/set-current → make current term
DELETE /api/v1/academic-years/{id}/terms/{tid} → delete term
```

### Admissions
```
GET  /api/v1/admissions/config               → get config for current year [admissions:view]
PUT  /api/v1/admissions/config               → upsert config [admissions:update]

POST /api/v1/admissions/apply                → PUBLIC (no auth) — submit application
GET  /api/v1/admissions/check/{reference}    → PUBLIC — check application status by ref no

GET  /api/v1/admissions                      → list applications (filters: status, year, class) [admissions:view]
GET  /api/v1/admissions/{id}                 → get application detail [admissions:view]
PUT  /api/v1/admissions/{id}/review          → approve/reject/waitlist [admissions:approve]
POST /api/v1/admissions/bulk-approve         → bulk approve [admissions:approve]
GET  /api/v1/admissions/export               → export to Excel [admissions:export]
GET  /api/v1/admissions/stats                → counts by status (for dashboard widget)
```

---

## 3.7 File Upload Utility (`backend/app/utils/file_upload.py`)

```python
async def save_upload(file: UploadFile, folder: str, school_id: str) -> str:
    """
    Validate: MIME type in allowed list + size < MAX_FILE_SIZE_MB
    If STORAGE_BACKEND == 'local': save to UPLOAD_DIR/{school_id}/{folder}/{uuid}_{filename}
    If STORAGE_BACKEND == 's3': upload to S3 bucket with same key path
    Returns public URL or relative path
    """

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_DOCUMENT_TYPES = {"application/pdf", "image/jpeg", "image/png"}
```

---

## 3.8 Settings Categories & Keys Reference

All defaults inserted by `seed_school_defaults()` (Phase 2):

| Category | Key | Default | Type |
|----------|-----|---------|------|
| general | academic_start_month | 4 | integer |
| general | timezone | Asia/Kolkata | string |
| general | currency | INR | string |
| general | date_format | DD/MM/YYYY | string |
| admission | admission_number_prefix | STU | string |
| admission | admission_number_start | 1001 | integer |
| admission | admission_number_format | {PREFIX}-{YEAR}-{SEQ:04d} | string |
| attendance | working_days | [1,2,3,4,5] | json |
| attendance | sessions_enabled | full_day | string |
| attendance | low_attendance_threshold_pct | 75 | integer |
| attendance | absent_notify_delay_minutes | 30 | integer |
| attendance | notify_parents_sms | true | boolean |
| attendance | notify_parents_whatsapp | true | boolean |
| fees | fine_enabled | true | boolean |
| fees | fine_per_day_paise | 0 | integer |
| fees | receipt_number_prefix | RCP | string |
| fees | due_reminder_days_before | 3 | integer |
| library | max_books_student | 3 | integer |
| library | max_books_staff | 5 | integer |
| library | default_loan_days | 14 | integer |
| library | fine_per_day_overdue_paise | 100 | integer |
| exam | default_pass_percentage | 35 | integer |
| exam | result_sms_on_publish | true | boolean |
| security | password_min_length | 8 | integer |
| security | session_timeout_minutes | 60 | integer |
| security | max_login_attempts | 5 | integer |
| security | lockout_duration_minutes | 15 | integer |
| security | tfa_enabled | false | boolean |

---

## 3.9 Frontend Pages

### Academic Year Selector Enhancement (Navbar)
- On app load: fetch `GET /api/v1/academic-years`
- Store in `academicYearStore.setYears()`
- Current year auto-selected in store
- Selector dropdown: switch year → store updates → all pages re-fetch with new year ID

### `/admin/academic-years` Page
- Table: Year Name, Start Date, End Date, Terms, Status (Current/Locked), Actions
- Create Year dialog: name, start date, end date (Zod: end > start)
- Edit Year dialog
- Set Current button (confirm dialog: "This will change the active year for all users")
- Lock Year button (confirm: "Locked years cannot be edited")
- Expandable row: term list with Create/Edit/Set Current for terms

### `/admin/settings` Page (Placeholder — full implementation in Phase 19)
- Render at least General settings: school name, logo upload, timezone, currency
- Other categories shown as tabs with placeholder "coming soon"

### `/admin/admissions` Page
- Stats bar: Draft | Submitted | Under Review | Approved | Rejected | Waitlisted counts
- Filter bar: status, year, applying class, search by name/phone
- Table: Ref No, Applicant Name, D.O.B, Class Applied, Parent Phone, Status, Submitted Date, Actions
- View Application modal: full details + documents preview + approve/reject form
- Kanban view toggle (optional: columns by status, drag to change status)
- Bulk action: select multiple → bulk approve (with class/section picker)
- Export button: CSV/Excel

### Public Admission Form (`/admissions/apply/:slug`)
- NO authentication required
- Dynamically renders fields from `admission_form_configs.fields_config`
- File upload for required documents
- Multi-step form: Step 1 (Student Info) → Step 2 (Parent Info) → Step 3 (Documents) → Step 4 (Review & Submit)
- On submit: show reference number + "Save this for tracking your application"
- Status check page: enter reference number → see current status

### `frontend/src/api/admissions.ts`
```typescript
export const admissionsApi = {
  getConfig: (yearId: string) => api.get(`/admissions/config?year_id=${yearId}`),
  updateConfig: (data: AdmissionConfigRequest) => api.put('/admissions/config', data),
  submitApplication: (data: FormData) => api.post('/admissions/apply', data, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  checkStatus: (reference: string) => api.get(`/admissions/check/${reference}`),
  list: (params: AdmissionListParams) => api.get('/admissions', { params }),
  get: (id: string) => api.get(`/admissions/${id}`),
  review: (id: string, data: ReviewRequest) => api.put(`/admissions/${id}/review`, data),
  bulkApprove: (data: BulkApproveRequest) => api.post('/admissions/bulk-approve', data),
  export: (params: AdmissionListParams) => api.get('/admissions/export', { params, responseType: 'blob' }),
  stats: (yearId: string) => api.get(`/admissions/stats?year_id=${yearId}`),
};
```

---

## 3.10 Celery Tasks

```python
@celery.task(queue="emails")
def send_admission_acknowledgement(parent_email: str, reference_number: str, school_name: str, applicant_name: str):
    """Send confirmation email with reference number."""

@celery.task(queue="emails")
def send_admission_approved(parent_email: str, student_name: str, admission_number: str, school_name: str):
    """Send admission approval email."""

@celery.task(queue="emails")
def send_admission_rejected(parent_email: str, student_name: str, remarks: str, school_name: str):
    """Send rejection email."""
```

---

## 3.11 Tests

```python
# Academic years
async def test_create_academic_year(): ...
async def test_only_one_current_year_per_school(): ...   # partial unique index enforcement
async def test_lock_prevents_edit(): ...
async def test_create_term_with_overlapping_dates_fails(): ...

# Admissions
async def test_public_form_submission_no_auth(): ...
async def test_status_check_by_reference(): ...
async def test_approve_creates_student_record(): ...
async def test_admission_config_closed_form_rejected(): ...  # after close_date → 400
```

---

## 3.12 Deliverables Checklist

- [ ] School profile GET/PUT working with file upload for logo
- [ ] Settings GET/PUT working — reads and writes key-value pairs grouped by category
- [ ] Academic year CRUD: create, list, update, delete (blocked if has data)
- [ ] Set current year works (only one current per school enforced at DB level)
- [ ] Lock year blocks subsequent edits
- [ ] Terms CRUD within a year
- [ ] Navbar academic year selector populated and switchable
- [ ] Admission config configurable (fields, documents, open/close dates)
- [ ] Public admission form renders dynamic fields
- [ ] Application submission stores in DB + sends acknowledgement email
- [ ] Reference number status check (no auth)
- [ ] Admin admission list with filters and status update
- [ ] Approve action creates student record + sends approval email
- [ ] Bulk approve with class assignment
- [ ] Excel export of applications
- [ ] Admission stats widget data available for dashboard
