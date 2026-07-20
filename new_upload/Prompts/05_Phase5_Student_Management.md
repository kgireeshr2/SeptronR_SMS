# PHASE 5 — STUDENT MANAGEMENT

## Pre-Requisite
Phases 1–4 complete. Classes, sections, academic years exist. Admission approval can trigger student creation.

## Objective
Complete student lifecycle: registration, enrollment, ID generation, profile management, parent linking, document storage, class promotion, TC issuance.

---

## 5.1 Database Tables (Verify Exist)

```sql
-- ⚠️ ACTUAL SCHEMA (cross-checked with Database_Schema.sql)

-- Section 9: Students
students (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    admission_number VARCHAR(30) UNIQUE,
    user_id UUID FK→users UNIQUE (nullable),  -- student portal login
    first_name VARCHAR(100) NOT NULL, last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL, gender VARCHAR(10) NOT NULL,
    blood_group VARCHAR(5),
    religion VARCHAR(50),
    category VARCHAR(30),        -- General|OBC|SC|ST|EWS
    nationality VARCHAR(60) DEFAULT 'Indian',
    photo_url TEXT,
    admission_date DATE NOT NULL,
    is_active BOOL DEFAULT TRUE,
    created_at, updated_at,
    deleted_at TIMESTAMPTZ, deleted_by UUID FK→users,
    UNIQUE(school_id, admission_number)
)
-- NOTE: address, aadhaar, previous_school, tc fields are NOT in the core schema.
-- Store these in student_documents or a separate student_details JSONB extension.
-- The schema intentionally keeps students table lean. Extend via student_documents.

student_parents (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    student_id UUID FK→students ON DELETE CASCADE,
    user_id UUID FK→users (nullable),  -- for parent portal login
    relation parent_relation NOT NULL DEFAULT 'father',
        -- ENUM: father|mother|guardian|sibling|other
    name VARCHAR(200) NOT NULL,
    phone VARCHAR(20), email VARCHAR(200),
    occupation VARCHAR(100), address TEXT,
    is_primary_contact BOOL DEFAULT FALSE,
    can_access_portal BOOL DEFAULT TRUE,
    created_at, updated_at
)

student_enrollments (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    student_id UUID FK→students ON DELETE CASCADE,
    class_id UUID FK→classes, section_id UUID FK→sections,
    academic_year_id UUID FK→academic_years,
    roll_number VARCHAR(20),
    is_current BOOL DEFAULT TRUE,
    created_at, updated_at,
    UNIQUE(student_id, academic_year_id)
)

student_documents (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    student_id UUID FK→students ON DELETE CASCADE,
    doc_type VARCHAR(60),  -- BirthCertificate|Aadhaar|Marksheet|TC|Photo|Other
    file_url TEXT NOT NULL,
    uploaded_at TIMESTAMPTZ DEFAULT NOW()
)

student_promotions (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    student_id UUID FK→students ON DELETE CASCADE,
    from_class_id UUID FK→classes, to_class_id UUID FK→classes,
    from_year_id UUID FK→academic_years, to_year_id UUID FK→academic_years,
    promoted_by UUID FK→users,
    promoted_at TIMESTAMPTZ DEFAULT NOW()
)

student_transfers (
    id UUID PK, school_id UUID FK→schools ON DELETE CASCADE,
    student_id UUID FK→students ON DELETE CASCADE,
    transfer_certificate_no VARCHAR(50) NOT NULL,
    leaving_date DATE NOT NULL,
    reason TEXT,
    issued_by UUID FK→users,
    issued_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(school_id, transfer_certificate_no)
)
```

> **Schema note**: The `student_parents` table does **not** have `alternate_phone`, `annual_income`, `education_qualification`, `aadhaar_number`, `photo_url`, or `is_emergency_contact`. If these are needed, add them via a migration or store in a `parent_details JSONB` column. The `students` table does **not** have `address/city/state/pincode`, `aadhaar_number`, or `tc_number` — store these in `student_documents` or via DB migration if required.


---

## 5.2 SQLAlchemy Models (`backend/app/models/students.py`)

```python
from enum import Enum as PyEnum

class StudentStatus(str, PyEnum):
    active = "active"
    inactive = "inactive"
    transferred = "transferred"
    passed_out = "passed_out"
    expelled = "expelled"

class Student(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "students"
    school_id: Mapped[UUID]
    admission_number: Mapped[str]
    first_name: Mapped[str]; last_name: Mapped[str]
    date_of_birth: Mapped[Optional[date]]
    gender: Mapped[Optional[str]]
    blood_group: Mapped[Optional[str]]
    photo_url: Mapped[Optional[str]]
    status: Mapped[StudentStatus]
    user_id: Mapped[Optional[UUID]]
    is_active: Mapped[bool]
    # ... all other columns
    # Relationships: parents, enrollments, documents, current_enrollment (viewonly)

class StudentParent(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "student_parents"
    student_id: Mapped[UUID]; user_id: Mapped[Optional[UUID]]
    relation: Mapped[str]; name: Mapped[str]; phone: Mapped[str]
    is_primary_contact: Mapped[bool]; is_emergency_contact: Mapped[bool]

class StudentEnrollment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "student_enrollments"
    student_id: Mapped[UUID]; class_id: Mapped[UUID]; section_id: Mapped[UUID]
    academic_year_id: Mapped[UUID]; roll_number: Mapped[Optional[str]]
    enrollment_date: Mapped[date]; is_current: Mapped[bool]
    # Relationships: student, class_, section, academic_year

class StudentDocument(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "student_documents"
    student_id: Mapped[UUID]; document_type: Mapped[str]
    file_url: Mapped[str]; file_name: Mapped[str]; uploaded_by: Mapped[UUID]
    created_at: Mapped[datetime]
```

---

## 5.3 Pydantic Schemas

```python
class ParentCreate(BaseModel):
    relation: Literal["father", "mother", "guardian"]
    name: str
    phone: str
    alternate_phone: Optional[str]
    email: Optional[EmailStr]
    occupation: Optional[str]
    annual_income: Optional[int]
    is_primary_contact: bool = False
    is_emergency_contact: bool = False
    create_login: bool = False   # if True, create user account with temp password

class StudentCreate(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: Optional[date]
    gender: Optional[str]
    blood_group: Optional[str]
    religion: Optional[str]
    caste: Optional[str]
    nationality: str = "Indian"
    aadhaar_number: Optional[str]
    address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    pincode: Optional[str]
    previous_school: Optional[str]
    joining_date: date
    # Enrollment info (required):
    class_id: UUID
    section_id: UUID
    academic_year_id: UUID
    roll_number: Optional[str]
    # Optional parents:
    parents: List[ParentCreate] = []

class StudentUpdate(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
    # ...all profile fields (no admission_number, no enrollment change via this endpoint)

class StudentResponse(BaseModel):
    id: UUID
    admission_number: str
    first_name: str; last_name: str
    full_name: str        # computed: f"{first_name} {last_name}"
    date_of_birth: Optional[date]
    age: Optional[int]   # computed at serialization
    gender: Optional[str]
    blood_group: Optional[str]
    photo_url: Optional[str]
    status: str
    is_active: bool
    current_enrollment: Optional[EnrollmentSummary]
    parents: Optional[List[ParentResponse]]
    model_config = ConfigDict(from_attributes=True)

class EnrollmentSummary(BaseModel):
    class_id: UUID; class_name: str
    section_id: UUID; section_name: str
    academic_year_id: UUID; academic_year_name: str
    roll_number: Optional[str]

class StudentListResponse(BaseModel):
    id: UUID
    admission_number: str
    full_name: str
    photo_url: Optional[str]
    class_name: str; section_name: str
    gender: Optional[str]
    parent_phone: Optional[str]   # primary contact phone
    status: str

class PromoteStudentsRequest(BaseModel):
    academic_year_id: UUID          # destination year
    promotions: List[StudentPromotion]

class StudentPromotion(BaseModel):
    student_id: UUID
    new_class_id: UUID
    new_section_id: UUID
    new_roll_number: Optional[str]

class TCRequest(BaseModel):
    student_id: UUID
    tc_number: Optional[str]   # auto-generated if not provided
    leaving_date: date
    reason: Optional[str]
```

---

## 5.4 Admission Number Generation (`backend/app/utils/admission_number.py`)

```python
async def generate_admission_number(school_id: str, db: AsyncSession) -> str:
    """
    1. Fetch settings: admission_number_prefix, admission_number_start, admission_number_format
    2. SELECT MAX(admission_number) for school → extract numeric suffix
    3. next_seq = max + 1 (or start if no students yet)
    4. format = settings['admission_number_format']   # e.g., "{PREFIX}-{YEAR}-{SEQ:04d}"
    5. Return formatted string
    Atomic: use SELECT FOR UPDATE on a sequence row or handle in transaction
    """
```

---

## 5.5 Repository Layer (`backend/app/repositories/student_repository.py`)

```python
class StudentRepository:
    async def create(self, school_id: str, data: dict) -> Student: ...
    async def get_by_id(self, student_id: str, school_id: str) -> Optional[Student]: ...
    async def get_by_admission_number(self, school_id: str, adm_no: str) -> Optional[Student]: ...
    async def list(self, school_id: str, filters: StudentFilter, page: int, page_size: int) -> tuple[List[Student], int]: ...
    async def update(self, student_id: str, data: dict) -> Student: ...
    async def soft_delete(self, student_id: str, deleted_by: str) -> None: ...
    async def enroll(self, student_id: str, enrollment_data: dict) -> StudentEnrollment: ...
    async def get_current_enrollment(self, student_id: str, year_id: str) -> Optional[StudentEnrollment]: ...
    async def list_by_section(self, section_id: str, year_id: str) -> List[Student]: ...
    async def list_by_class(self, class_id: str, year_id: str) -> List[Student]: ...
    async def bulk_create(self, school_id: str, students: List[dict]) -> List[Student]: ...
    async def add_parent(self, student_id: str, data: dict) -> StudentParent: ...
    async def update_parent(self, parent_id: str, data: dict) -> StudentParent: ...
    async def delete_parent(self, parent_id: str) -> None: ...
    async def add_document(self, student_id: str, data: dict) -> StudentDocument: ...
    async def delete_document(self, doc_id: str) -> None: ...
    async def issue_tc(self, student_id: str, tc_data: dict) -> Student: ...
    async def promote_students(self, promotions: List[dict], year_id: str) -> int: ...
    async def count_by_section(self, school_id: str, year_id: str) -> List[dict]: ...
    async def count_by_gender(self, school_id: str) -> dict: ...
```

---

## 5.6 Service Layer (`backend/app/services/student_service.py`)

```python
async def create_student(school_id: str, data: StudentCreate, created_by: str) -> Student:
    """
    1. Generate admission_number (atomic)
    2. Create Student record
    3. Create StudentEnrollment for given class/section
    4. For each parent in data.parents:
       a. Create StudentParent record
       b. If create_login=True: create User(role=parent) with temp password
          → send_welcome_sms(parent.phone, student_name, temp_password)
    5. Return student with all relations
    """

async def create_from_admission(admission_form_id: str, class_id: str, section_id: str, db: AsyncSession) -> Student:
    """Called by admission approval flow. Maps admission fields to Student fields."""

async def promote_students(data: PromoteStudentsRequest, promoted_by: str) -> dict:
    """
    1. Validate all student_ids and new class/section belong to same school
    2. For each student: set current enrollment is_current=False
    3. Create new enrollment for destination year/class/section
    4. Return {promoted: N, errors: [...]}
    """

async def issue_transfer_certificate(data: TCRequest, issued_by: str) -> Student:
    """
    1. Update student: status=transferred, tc_number, tc_issued_date, leaving_date
    2. Set is_current=False on enrollment
    3. Set is_active=False on student user account if exists
    4. Log audit
    5. Return updated student
    """

async def import_students_from_excel(school_id: str, file: UploadFile, year_id: str, created_by: str) -> dict:
    """
    Parse columns: first_name, last_name, dob, gender, class_name, section_name, 
                   father_name, father_phone, mother_name, mother_phone
    Return {success: N, failed: [{row, reason}]}
    """
```

---

## 5.7 API Endpoints

```
GET    /api/v1/students                     → list (filters: class, section, year, gender, status, search) [students:view]
POST   /api/v1/students                     → create new student [students:create]
GET    /api/v1/students/{id}                → get full profile with parents, documents, enrollments
PUT    /api/v1/students/{id}                → update profile [students:update]
DELETE /api/v1/students/{id}                → soft delete [students:delete]
POST   /api/v1/students/{id}/photo          → upload photo [students:update]

GET    /api/v1/students/{id}/parents        → list parents
POST   /api/v1/students/{id}/parents        → add parent [students:update]
PUT    /api/v1/students/{id}/parents/{pid}  → update parent
DELETE /api/v1/students/{id}/parents/{pid}  → remove parent

GET    /api/v1/students/{id}/documents      → list documents
POST   /api/v1/students/{id}/documents      → upload document [students:update]
DELETE /api/v1/students/{id}/documents/{did}→ delete document

GET    /api/v1/students/{id}/enrollments    → enrollment history
POST   /api/v1/students/promote             → bulk promote [students:promote]
POST   /api/v1/students/{id}/transfer-certificate → issue TC [students:update]
GET    /api/v1/students/{id}/id-card        → generate ID card PDF [students:view]

POST   /api/v1/students/bulk-import         → Excel upload [students:create]
GET    /api/v1/students/export              → Export list to Excel [students:export]
GET    /api/v1/students/stats               → count by class/gender/status [students:view]
```

---

## 5.8 Frontend Pages

### `/admin/students` Page (Permission: `students:view`)
**Filter bar:** Academic Year, Class, Section, Gender, Status, Search (name / admission no / parent phone)
**Table columns:** Photo, Admission No, Student Name, Class-Section, DOB/Age, Gender, Parent Phone, Status, Actions
**Actions per row:** View, Edit, Delete (with confirmation)
**Bulk actions:** Select multiple → Promote, Export, Print ID Cards

### `/admin/students/new` Page
Multi-step form:
- Step 1: Personal Info (name, DOB, gender, blood group, photo upload)
- Step 2: Address & Background (address, previous school, aadhaar)
- Step 3: Enrollment (academic year, class, section, roll number)
- Step 4: Parent/Guardian (add up to 3 parents — at least 1 required)
- Step 5: Review & Submit

### `/admin/students/:id` Page
Tabs: Profile | Parents | Documents | Enrollments | Attendance | Fees | Exam Results

### `/admin/students/promote` Page
- Select "From Year" and "To Year"
- Load all students with current enrollment
- Table with new class/section dropdowns per row
- Group by class — select all in class to same class
- Submit promotion → shows progress + errors

### Student ID Card Generation
- Button on student profile → calls `/students/{id}/id-card`
- Backend uses Jinja2 template + WeasyPrint
- Template includes: school logo, student photo, name, admission no, class-section, DOB, blood group, address, parent phone, QR code (links to school website or student info)

### `frontend/src/api/students.ts`
```typescript
export const studentsApi = {
  list: (params: StudentListParams) => api.get('/students', { params }),
  get: (id: string) => api.get(`/students/${id}`),
  create: (data: StudentCreate) => api.post('/students', data),
  update: (id: string, data: StudentUpdate) => api.put(`/students/${id}`, data),
  delete: (id: string) => api.delete(`/students/${id}`),
  uploadPhoto: (id: string, file: File) => {
    const form = new FormData(); form.append('file', file);
    return api.post(`/students/${id}/photo`, form, { headers: { 'Content-Type': 'multipart/form-data' } });
  },
  addParent: (id: string, data: ParentCreate) => api.post(`/students/${id}/parents`, data),
  updateParent: (id: string, pid: string, data: Partial<ParentCreate>) => api.put(`/students/${id}/parents/${pid}`, data),
  deleteParent: (id: string, pid: string) => api.delete(`/students/${id}/parents/${pid}`),
  uploadDocument: (id: string, docType: string, file: File) => {
    const form = new FormData(); form.append('file', file); form.append('document_type', docType);
    return api.post(`/students/${id}/documents`, form);
  },
  promote: (data: PromoteStudentsRequest) => api.post('/students/promote', data),
  issueTC: (id: string, data: TCRequest) => api.post(`/students/${id}/transfer-certificate`, data),
  getIdCard: (id: string) => api.get(`/students/${id}/id-card`, { responseType: 'blob' }),
  bulkImport: (file: File, yearId: string) => {
    const form = new FormData(); form.append('file', file); form.append('year_id', yearId);
    return api.post('/students/bulk-import', form);
  },
  export: (params: StudentListParams) => api.get('/students/export', { params, responseType: 'blob' }),
  stats: (yearId: string) => api.get(`/students/stats?year_id=${yearId}`),
};
```

---

## 5.9 ID Card Jinja2 Template (`backend/app/templates/id_card.html`)

```html
<!DOCTYPE html>
<html>
<head>
  <style>
    /* 85.6mm × 53.98mm — standard card size */
    @page { size: 85.6mm 53.98mm; margin: 0; }
    .card { width: 85.6mm; height: 53.98mm; font-family: Arial; position: relative; overflow: hidden; }
    .header { background: {{ school.primary_color or '#1a56db' }}; color: white; padding: 3mm; text-align: center; }
    .photo { width: 15mm; height: 18mm; object-fit: cover; border-radius: 1mm; }
    .info { font-size: 7pt; }
    .name { font-weight: bold; font-size: 9pt; }
    .footer { background: #f5f5f5; font-size: 6pt; text-align: center; padding: 1mm; }
  </style>
</head>
<body>
  <div class="card">
    <div class="header">
      <img src="{{ school.logo_url }}" height="10mm"> {{ school.school_name }}
    </div>
    <div style="display:flex; padding: 2mm">
      <img src="{{ student.photo_url }}" class="photo">
      <div style="margin-left: 2mm">
        <div class="name">{{ student.full_name }}</div>
        <div class="info">Adm No: {{ student.admission_number }}</div>
        <div class="info">Class: {{ enrollment.class_name }}-{{ enrollment.section_name }}</div>
        <div class="info">DOB: {{ student.date_of_birth|date }}</div>
        <div class="info">Blood: {{ student.blood_group }}</div>
        <div class="info">Parent: {{ primary_parent.phone }}</div>
      </div>
    </div>
    <div class="footer">{{ school.address }}, {{ school.city }} | {{ school.phone }}</div>
  </div>
</body>
</html>
```

---

## 5.10 Tests

```python
async def test_create_student_generates_unique_admission_number(): ...
async def test_student_enrollment_unique_per_year(): ...        # UNIQUE(student_id, academic_year_id)
async def test_promote_creates_new_enrollment(): ...
async def test_promote_blocks_if_already_enrolled_in_target_year(): ...
async def test_issue_tc_sets_status_transferred(): ...
async def test_bulk_import_partial_success(): ...               # valid rows succeed, invalid rows return errors
async def test_create_parent_with_login(): ...                  # creates user account
async def test_student_soft_delete_not_hard_delete(): ...
```

---

## 5.11 Deliverables Checklist

- [ ] Student CRUD with multi-step registration form
- [ ] Admission number auto-generated using school setting format
- [ ] Parent records created with optional login account
- [ ] Photo upload working for students and parents
- [ ] Student enrollment linked to class/section/year
- [ ] Bulk import from Excel with row-level error reporting
- [ ] Class promotion: marks old enrollment inactive, creates new
- [ ] Transfer certificate issuance: status → transferred, TC number assigned
- [ ] Document upload/delete per student
- [ ] ID card PDF generation (Jinja2 + WeasyPrint)
- [ ] Student profile page with all tabs (profile, parents, docs, enrollment history)
- [ ] Student list with all filters working (class, section, year, gender, search)
- [ ] Admission-to-student flow works via `create_from_admission()`
- [ ] Excel export of student list
- [ ] Stats endpoint returns counts by class, gender, status
