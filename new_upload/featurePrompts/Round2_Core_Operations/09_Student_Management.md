# Feature Prompt 09 — Student Management

## Round: 2 of 4 — Core Operations
## Prerequisites: Prompts 01–08 complete

---

## Objective

Implement full student profile management: student registration with auto-generated admission numbers, class enrollment, parent/guardian profiles, document management, student search, bulk import/export, promotion workflow, Transfer Certificate generation, and ID card PDF. Students can also be created via the admissions approval flow (Prompt 08).

---

## 1. Database Models (`backend/app/models/students.py`)

```python
import uuid
from datetime import date, datetime
from sqlalchemy import String, Boolean, Date, DateTime, ForeignKey, Text, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from app.models.base import Base, TimestampMixin
import enum

class StudentStatus(str, enum.Enum):
    ENROLLED = "enrolled"
    TRANSFERRED = "transferred"
    GRADUATED = "graduated"
    DECEASED = "deceased"
    ON_LEAVE = "on_leave"

class Student(Base, TimestampMixin):
    __tablename__ = "students"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("users.id"), nullable=True)  # linked login account
    admission_number: Mapped[str] = mapped_column(String(50), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[str] = mapped_column(String(10), nullable=False)
    blood_group: Mapped[str | None] = mapped_column(String(5), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    pincode: Mapped[str | None] = mapped_column(String(10), nullable=True)
    aadhar_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    religion: Mapped[str | None] = mapped_column(String(50), nullable=True)
    caste: Mapped[str | None] = mapped_column(String(50), nullable=True)
    category: Mapped[str | None] = mapped_column(String(10), nullable=True)  # Gen/OBC/SC/ST
    nationality: Mapped[str] = mapped_column(String(50), default="Indian", nullable=False)
    previous_school: Mapped[str | None] = mapped_column(String(200), nullable=True)
    admission_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[StudentStatus] = mapped_column(String(20), default=StudentStatus.ENROLLED)
    tc_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tc_issued_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    leaving_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    enrollments: Mapped[list["StudentEnrollment"]] = relationship("StudentEnrollment",
                                                                    back_populates="student")
    parents: Mapped[list["StudentParent"]] = relationship("StudentParent", back_populates="student")
    documents: Mapped[list["StudentDocument"]] = relationship("StudentDocument", back_populates="student")

    __table_args__ = (
        UniqueConstraint("school_id", "admission_number", name="uq_student_admission_number"),
    )


class StudentEnrollment(Base, TimestampMixin):
    __tablename__ = "student_enrollments"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("academic_years.id"), nullable=False, index=True)
    class_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("classes.id"), nullable=False, index=True)
    section_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("sections.id"), nullable=False, index=True)
    roll_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    promoted_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    promotion_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    student: Mapped[Student] = relationship("Student", back_populates="enrollments")

    __table_args__ = (
        UniqueConstraint("student_id", "academic_year_id", name="uq_enrollment_student_year"),
    )


class StudentParent(Base, TimestampMixin):
    __tablename__ = "student_parents"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("users.id"), nullable=True)
    parent_relation: Mapped[str] = mapped_column(String(20), nullable=False)  # father/mother/guardian
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    occupation: Mapped[str | None] = mapped_column(String(200), nullable=True)
    qualification: Mapped[str | None] = mapped_column(String(200), nullable=True)
    annual_income: Mapped[int | None] = mapped_column(Integer, nullable=True)  # paise
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_emergency_contact: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_access_portal: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    student: Mapped[Student] = relationship("Student", back_populates="parents")


class StudentDocument(Base, TimestampMixin):
    __tablename__ = "student_documents"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    document_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    file_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    student: Mapped[Student] = relationship("Student", back_populates="documents")
```

---

## 2. Alembic Migration

```sql
CREATE TABLE students (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id),
    admission_number VARCHAR(50) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender VARCHAR(10) NOT NULL,
    blood_group VARCHAR(5),
    photo_url VARCHAR(500),
    phone VARCHAR(20),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    pincode VARCHAR(10),
    aadhar_number VARCHAR(20),
    religion VARCHAR(50),
    caste VARCHAR(50),
    category VARCHAR(10),
    nationality VARCHAR(50) DEFAULT 'Indian' NOT NULL,
    previous_school VARCHAR(200),
    admission_date DATE,
    status VARCHAR(20) DEFAULT 'enrolled' NOT NULL,
    tc_number VARCHAR(50),
    tc_issued_date DATE,
    leaving_date DATE,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT uq_student_admission_number UNIQUE (school_id, admission_number)
);

CREATE INDEX ix_students_school_id ON students(school_id);
CREATE INDEX ix_students_admission_number ON students(school_id, admission_number);

CREATE TABLE student_enrollments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    academic_year_id UUID NOT NULL REFERENCES academic_years(id),
    class_id UUID NOT NULL REFERENCES classes(id),
    section_id UUID NOT NULL REFERENCES sections(id),
    roll_number VARCHAR(20),
    is_current BOOLEAN DEFAULT TRUE NOT NULL,
    promoted_by UUID,
    promotion_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT uq_enrollment_student_year UNIQUE (student_id, academic_year_id)
);

CREATE INDEX ix_enrollment_year_class ON student_enrollments(academic_year_id, class_id, section_id);

CREATE TABLE student_parents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id),
    parent_relation VARCHAR(20) NOT NULL,
    full_name VARCHAR(200) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(255),
    occupation VARCHAR(200),
    qualification VARCHAR(200),
    annual_income INTEGER,
    is_primary BOOLEAN DEFAULT FALSE NOT NULL,
    is_emergency_contact BOOLEAN DEFAULT FALSE NOT NULL,
    can_access_portal BOOLEAN DEFAULT TRUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE student_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    document_type VARCHAR(100) NOT NULL,
    file_url VARCHAR(500) NOT NULL,
    file_name VARCHAR(200),
    uploaded_by UUID,
    is_verified BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
```

---

## 3. Admission Number Generation (`backend/app/utils/admission_number.py`)

```python
from sqlalchemy import select, update, text
from app.models.school import SchoolSettings

async def generate_admission_number(db, redis, school_id: UUID) -> str:
    """
    Atomically increment admission_number_last_seq using SELECT FOR UPDATE.
    Format: apply {PREFIX}-{YEAR}-{SEQ:04d} template from settings.
    Retry up to 5 times if collision.
    """
    # SELECT FOR UPDATE on the school_settings row
    async with db.begin_nested():
        result = await db.execute(
            select(SchoolSettings)
            .where(SchoolSettings.school_id == school_id)
            .where(SchoolSettings.key == "admission_number_last_seq")
            .with_for_update()
        )
        seq_row = result.scalar_one()
        new_seq = int(seq_row.value or "0") + 1
        seq_row.value = str(new_seq)
        await db.flush()

    # Get format template
    fmt = await get_setting_value(db, redis, school_id, "admission_number_format",
                                   default="{PREFIX}-{YEAR}-{SEQ:04d}")
    prefix = await get_setting_value(db, redis, school_id, "admission_number_prefix", default="ADM")
    from datetime import datetime
    year = str(datetime.now().year)
    return fmt.format(PREFIX=prefix, YEAR=year, SEQ=new_seq)
```

---

## 4. Pydantic Schemas

```python
class StudentCreate(BaseModel):
    firstName: str
    lastName: str
    dateOfBirth: date
    gender: str
    bloodGroup: str | None = None
    phone: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    nationality: str = "Indian"
    religion: str | None = None
    caste: str | None = None
    category: str | None = None
    previousSchool: str | None = None
    admissionDate: date | None = None
    # Enrollment info (required)
    academicYearId: UUID
    classId: UUID
    sectionId: UUID
    rollNumber: str | None = None

class StudentUpdate(BaseModel):
    firstName: str | None = None
    lastName: str | None = None
    phone: str | None = None
    address: str | None = None
    city: str | None = None
    bloodGroup: str | None = None
    religion: str | None = None
    category: str | None = None

class StudentResponse(BaseModel):
    id: UUID
    admissionNumber: str
    firstName: str
    lastName: str
    fullName: str
    dateOfBirth: date
    gender: str
    bloodGroup: str | None
    photoUrl: str | None
    status: str
    isActive: bool
    currentClass: str | None = None
    currentSection: str | None = None
    rollNumber: str | None = None
    model_config = {"from_attributes": True}

class StudentListFilter(BaseModel):
    academicYearId: UUID | None = None
    classId: UUID | None = None
    sectionId: UUID | None = None
    gender: str | None = None
    status: str | None = None
    category: str | None = None
    search: str | None = None  # searches admission_number, first_name, last_name

class BulkPromoteRequest(BaseModel):
    fromAcademicYearId: UUID
    toAcademicYearId: UUID
    promotions: list[dict]  # [{student_id, to_class_id, to_section_id}]

class TransferCertificateRequest(BaseModel):
    leavingDate: date
    reason: str | None = None
    tcNumber: str | None = None  # auto-generated if not provided

class ParentCreate(BaseModel):
    parentRelation: str  # father/mother/guardian
    fullName: str
    phone: str
    email: str | None = None
    occupation: str | None = None
    isPrimary: bool = False
    isEmergencyContact: bool = False
    createPortalAccount: bool = True
```

---

## 5. Service (`backend/app/services/student_service.py`)

```python
async def create_student(db, redis, school_id, data: StudentCreate, current_user) -> Student:
    """
    1. Generate admission number.
    2. Create Student record.
    3. Create StudentEnrollment in specified class/section/year.
    4. Optionally create User account for student (role: student).
    5. Audit log.
    """
    ...

async def create_from_admission(db, redis, form: AdmissionForm, class_id, section_id,
                                 academic_year_id, created_by) -> Student:
    """Called by admission_service.review_application on approval."""
    ...

async def promote_students(db, school_id, data: BulkPromoteRequest, current_user) -> dict:
    """
    For each promotion:
      1. Find current enrollment, set is_current=False.
      2. Create new enrollment in to_year/class/section.
    Return {promoted: N, skipped: N, errors: [...]}
    """
    ...

async def issue_transfer_certificate(db, student_id, school_id, data: TCRequest, current_user) -> Student:
    """
    1. Set student.status=transferred.
    2. Set tc_number (auto-generate if not provided), tc_issued_date, leaving_date.
    3. Set current enrollment is_current=False.
    4. Deactivate student's user account.
    5. Audit log.
    """
    ...

async def bulk_import_from_excel(db, redis, school_id, file_content: bytes, academic_year_id, current_user) -> dict:
    """
    Parse xlsx using openpyxl.
    Required columns: first_name, last_name, dob (DD/MM/YYYY), gender, class_name, section_name.
    Optional: father_name, father_phone, mother_name, mother_phone, blood_group, category.
    Return {success: N, failed: N, errors: [{row, reason}]}
    """
    ...

async def export_students_excel(db, school_id, filters: StudentListFilter) -> bytes:
    """openpyxl export with all student fields + enrollment info."""
    ...

async def generate_id_card_pdf(db, student_id, school_id) -> bytes:
    """Load ID card template (DocumentTemplate type=student_id_front), render with student data."""
    ...
```

---

## 6. API Endpoints (`backend/app/api/v1/endpoints/students.py`)

```
GET    /students                        → paginated list with filters   [students:view]
POST   /students                        → create student                [students:create]
GET    /students/{id}                   → student detail                [students:view]
PUT    /students/{id}                   → update student                [students:update]
DELETE /students/{id}                   → soft delete (is_active=False) [students:delete]
POST   /students/{id}/photo             → upload photo (multipart)      [students:update]
GET    /students/{id}/enrollments       → enrollment history            [students:view]
POST   /students/promote                → bulk promote                  [students:update]
POST   /students/{id}/transfer-certificate → issue TC + PDF            [students:update]
GET    /students/{id}/id-card           → download ID card PDF          [students:export]

# Parents
GET    /students/{id}/parents           → list parents                  [students:view]
POST   /students/{id}/parents           → add parent                    [students:update]
PUT    /students/{id}/parents/{pid}     → update parent                 [students:update]
DELETE /students/{id}/parents/{pid}     → remove parent link            [students:update]

# Documents
GET    /students/{id}/documents         → list documents                [students:view]
POST   /students/{id}/documents         → upload document               [students:update]
DELETE /students/{id}/documents/{did}   → remove document               [students:update]

# Bulk
POST   /students/import                 → Excel bulk import             [students:create]
GET    /students/export                 → Excel export                  [students:export]
GET    /students/stats                  → counts by class/gender/status [students:view]
```

---

## 7. Frontend: Types

```typescript
export interface Student {
  id: string;
  admissionNumber: string;
  firstName: string;
  lastName: string;
  fullName: string;
  dateOfBirth: string;
  gender: string;
  bloodGroup?: string;
  photoUrl?: string;
  status: string;
  isActive: boolean;
  currentClass?: string;
  currentSection?: string;
  rollNumber?: string;
}

export interface StudentParent {
  id: string;
  parentRelation: string;
  fullName: string;
  phone: string;
  email?: string;
  isPrimary: boolean;
  canAccessPortal: boolean;
}
```

---

## 8. Frontend: Student Pages

### Students List Page (`/students`)
- **PageHeader**: "Students" + "Add Student" + "Import Excel" + "Export Excel" buttons
- **Filter bar**: Year selector, Class, Section, Gender, Category, Status, Search input
- **TanStack Table**: Admission# | Photo | Name | Class/Section | DOB | Status | Actions
- **Pagination** (20 per page)
- **Row actions**: View Profile, Edit, Generate ID Card, Issue TC, Delete

### Student Detail Page (`/students/:id`)
6-tab profile page:
1. **Personal**: All personal fields, photo upload
2. **Parents**: Parent list + add/edit parents
3. **Enrollment**: Enrollment history table + current class/section
4. **Documents**: Document list with upload and verify toggle
5. **Attendance**: Summary widget (link to attendance page filtered by student)
6. **Fees**: Outstanding fees summary (link to fees page)

### Student Registration Form
5-step form:
1. Personal Info
2. Contact & Address
3. Class Assignment (year, class, section, roll no)
4. Parent/Guardian details
5. Review & Create

### Promote Students Page (`/students/promote`)
- From year + To year selectors
- Class grid: for each class in from-year, select destination class/section
- Student count per class
- "Preview" → show promotion plan → "Confirm Promote"

---

## 9. Sidebar Navigation

Add under "Students" section:
- `All Students` → `/students`
- `Promote Students` → `/students/promote`

---

## Verification Checklist

- [ ] `POST /students` creates student with auto-generated unique admission number
- [ ] Admission number follows format from settings (`ADM-2025-0001`)
- [ ] Duplicate admission number in same school returns 409
- [ ] `POST /students/promote` sets old enrollment `is_current=False` and creates new one
- [ ] TC generation sets `status=transferred` and locks enrollment
- [ ] Parent portal account (`User` with role=parent) created automatically on student registration when `createPortalAccount=true`
- [ ] `POST /students/import` processes Excel and returns `{success, failed, errors}`
- [ ] `GET /students/{id}/id-card` returns PDF
- [ ] Student photo upload saves to `uploads/students/{id}/photo.jpg`
- [ ] Frontend student list filter by class/section works with year selector
- [ ] Student detail page shows all 6 tabs with correct data
