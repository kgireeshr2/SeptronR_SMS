# FIX PROMPT 03 — Pydantic Schema & Service Logic Fixes

## Context
After applying Fix 01 (column renames) and Fix 02 (DB migration), many endpoints will start working. However, there are additional Pydantic schema issues, missing service logic, and API design problems that need to be fixed for full functionality.

---

## 1. Fix Student Schemas

**File:** `backend/app/schemas/` (find student schemas file)

The `students` table is missing several model columns that the API may expect. After Fix 02 adds `admission_date`, update:

```python
class StudentCreate(BaseModel):
    # Add these fields:
    admission_date: Optional[date] = None
    # These fields should map to DB columns (address, city, etc. already in DB):
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    aadhar_number: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_relation: Optional[str] = None
    medical_conditions: Optional[str] = None
```

**Also check** `StudentResponse` schema — ensure it includes all DB columns (address, city, phone, email, aadhar_number, etc.) that the model doesn't have but the DB does.  

Add these columns to the `Student` SQLAlchemy model as well if they're missing:
```python
# In app/models/students.py, add:
address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
pincode: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
aadhar_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
emergency_contact: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
emergency_contact_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
emergency_contact_relation: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
medical_conditions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
```

---

## 2. Fix Staff Schemas

**File:** `backend/app/schemas/` (find staff schemas file)

After Fix 01 renames `salary_type`, `monthly_salary`, etc., update `StaffCreate` and `StaffResponse`:
- Add `blood_group`, `phone`, `email`, `city`, `state`, `pincode`, `nationality`, `aadhar_number`, `pan_number` fields (these are in DB but missing from model)
- Add these to the `Staff` SQLAlchemy model in `app/models/staff.py`

Also fix `StaffLeave` schemas to use new column names: `days_count`, `reviewed_by`, `reviewed_at`.

---

## 3. Fix Class & Section Schemas

**File:** `backend/app/schemas/` (find class/section schemas)

After Fix 02 adds `academic_year_id` and `numeric_level` to `classes` table:

```python
class ClassCreate(BaseModel):
    name: str
    academic_year_id: UUID
    numeric_level: Optional[int] = None
    is_active: bool = True
```

`ClassResponse` should include both old DB cols (`code`, `level`, `description`, `max_students`) and new ones.

For `Section`, update `SectionCreate`/`SectionResponse` to use `capacity` (and optionally keep `max_students` for backward compat).

---

## 4. Fix Subject Schemas

```python
class SubjectCreate(BaseModel):
    name: str
    code: str
    full_marks: int = 100
    pass_marks: int = 35
    is_elective: bool = False
    description: Optional[str] = None
    is_active: bool = True
```

---

## 5. Fix Announcement Schemas

After Fix 01 renames `content`→`body`, `is_published`→`is_active`, `published_at`→`publish_at`:

```python
class AnnouncementCreate(BaseModel):
    title: str
    body: str  # was: content
    audience: str  # 'all', 'students', 'staff', 'parents'
    audience_filter: Optional[dict] = None
    publish_at: Optional[datetime] = None  # was: published_at
    expires_at: Optional[datetime] = None
    target_class_id: Optional[UUID] = None  # new column added in Fix 02
    target_section_id: Optional[UUID] = None  # new column added in Fix 02

class AnnouncementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str
    body: str
    is_active: bool
    # ...other fields
```

---

## 6. Fix Notification Schemas

After Fix 01 renames `data`→`metadata` (or uses mapped column):

```python
class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    type: str
    channel: str
    title: str
    body: str
    notification_metadata: Optional[dict] = None  # maps to DB 'metadata'
    is_read: bool
    scheduled_at: Optional[datetime] = None  # exists in DB, add to model
    sent_at: Optional[datetime] = None  # exists in DB, add to model
```

---

## 7. Fix Notification Template Schemas

After Fix 01 renames `channel`→`channels`, `body`→`body_template`:

```python
class NotificationTemplateCreate(BaseModel):
    name: str
    channels: list[str]  # ['sms', 'email', 'push']
    event_trigger: str
    subject: Optional[str] = None
    body_template: str  # was: body
    is_active: bool = True
```

---

## 8. Fix Library schemas

### BookCreate:
```python
class BookCreate(BaseModel):
    title: str
    author: str
    publisher: Optional[str] = None
    isbn: Optional[str] = None
    edition: Optional[str] = None
    publication_year: Optional[int] = None
    category_id: UUID
    total_copies: int = 1
    language: str = 'English'  # added in Fix 02
    cover_image_url: Optional[str] = None
    rack_number: Optional[str] = None
    description: Optional[str] = None
```

### LibraryMemberCreate:
```python
class LibraryMemberCreate(BaseModel):
    member_type: str  # 'student' or 'staff'
    entity_id: UUID   # student_id or staff_id
    user_id: UUID
    max_books_allowed: int = 3  # Fix 01 rename
    membership_valid_until: Optional[date] = None
```

### BookIssueCreate:
```python
class BookIssueCreate(BaseModel):
    book_id: UUID
    member_id: UUID
    issued_by: UUID  # user issuing the book
    due_date: date
    fine_per_day: float = 1.0
    notes: Optional[str] = None
```

---

## 9. Fix Accounting Record Schemas

```python
class IncomeRecordCreate(BaseModel):
    category_id: UUID
    academic_year_id: Optional[UUID] = None
    amount: float
    income_date: date
    description: Optional[str] = None
    payment_mode: Optional[str] = None
    transaction_id: Optional[str] = None
    reference_number: Optional[str] = None
    received_by: Optional[str] = None
    is_fee_income: bool = False
    fee_payment_id: Optional[UUID] = None

class ExpenseRecordCreate(BaseModel):
    category_id: UUID
    academic_year_id: Optional[UUID] = None
    amount: float
    expense_date: date
    description: Optional[str] = None
    payee_name: Optional[str] = None
    payment_mode: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_url: Optional[str] = None
    approved_by: Optional[str] = None
    status: str = 'approved'
```

---

## 10. Fix Inventory Item Schemas

```python
class ItemCreate(BaseModel):
    name: str
    item_code: Optional[str] = None  # Fix 01 rename from sku
    category_id: UUID
    store_id: UUID
    unit: str
    description: Optional[str] = None
    min_stock_level: int = 0  # Fix 01 rename from reorder_level
    current_stock: int = 0
    unit_cost: float = 0
    is_consumable: bool = False  # added in Fix 02
    is_active: bool = True
```

---

## 11. Fix Department Schema

```python
class DepartmentCreate(BaseModel):
    name: str
    head_id: Optional[UUID] = None  # Fix 01 rename from hod_id
    description: Optional[str] = None
    is_active: bool = True
```

---

## 12. Fix Holiday Schema

```python
class HolidayCreate(BaseModel):
    academic_year_id: UUID
    name: str
    date: date
    type: str  # Fix 01 rename from holiday_type: 'national', 'religious', 'school'
    description: Optional[str] = None
    is_optional: bool = False
```

---

## 13. Fix Staff Payroll Schema

```python
class StaffPayrollCreate(BaseModel):
    staff_id: UUID
    academic_year_id: UUID
    month: int  # 1-12
    year: int
    basic_salary: float
    allowances: float = 0
    deductions: float = 0
    # gross_salary and net_salary should be computed server-side
    payment_date: Optional[date] = None
    payment_method: Optional[str] = None
    is_paid: bool = False
```

---

## 14. Fix Homework Schema

```python
class HomeworkCreate(BaseModel):
    academic_year_id: Optional[UUID] = None  # added in Fix 02
    class_id: UUID
    section_id: Optional[UUID] = None
    subject_id: UUID
    title: str
    description: Optional[str] = None
    due_date: date
    attachments: Optional[list] = None
    is_active: bool = True
```

---

## 15. Fix CalendarEvent Schema

```python
class CalendarEventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    event_type: str
    start_datetime: datetime
    end_datetime: datetime
    all_day: bool = False
    location: Optional[str] = None  # added in Fix 02
    color_tag: Optional[str] = None
    audience: str = 'all'
    audience_filter: Optional[dict] = None
    academic_year_id: Optional[UUID] = None
    recurrence_rule: Optional[str] = None
    is_active: bool = True
```

---

## 16. Fix PTMEvent Schema

```python
class PTMEventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    ptm_date: date
    academic_year_id: UUID
    slot_duration_minutes: int = 15
    venue: Optional[str] = None  # added in Fix 02
    is_active: bool = True
```

---

## Post-Fix Integration Test

After all schema fixes, run a full CRUD test for each module:

```powershell
$base = "http://localhost:8000/api/v1"
$token = (Invoke-RestMethod -Method Post -Uri "$base/auth/login" `
    -ContentType "application/json" `
    -Body '{"username":"superadmin","password":"SuperAdmin@123"}').data.access_token
$h = @{Authorization = "Bearer $token"; "Content-Type" = "application/json"}
$ayId = "<your-academic-year-id>"
$schoolId = "<your-school-id>"

# Test Class creation
$class = Invoke-RestMethod -Method Post -Uri "$base/classes" -Headers $h `
    -Body "{`"name`":`"Grade 1`",`"academic_year_id`":`"$ayId`",`"numeric_level`":1}"

# Test Section creation
$section = Invoke-RestMethod -Method Post -Uri "$base/sections" -Headers $h `
    -Body "{`"class_id`":`"$($class.data.id)`",`"name`":`"A`",`"capacity`":40}"

# Test Subject
$sub = Invoke-RestMethod -Method Post -Uri "$base/subjects" -Headers $h `
    -Body "{`"name`":`"Mathematics`",`"code`":`"MATH`",`"full_marks`":100,`"pass_marks`":40}"

echo "Class: $($class.data.id)"
echo "Section: $($section.data.id)"
echo "Subject: $($sub.data.id)"
```
