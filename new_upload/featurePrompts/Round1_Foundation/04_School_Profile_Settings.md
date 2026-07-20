# Feature Prompt 04 — School Profile & Settings

## Round: 1 of 4 — Foundation
## Prerequisites: Prompts 01–03 complete

---

## Objective

Implement the `schools` table (multi-tenant foundation), the `school_settings` key-value store, school profile CRUD (name, logo, address, contact), and the 9-category settings system used by all other modules. By the end, admins can update their school profile and configure module-specific settings via a tabbed Settings UI.

---

## 1. Database Models (`backend/app/models/school.py`)

```python
import uuid
from sqlalchemy import String, Boolean, ForeignKey, Text, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from app.models.base import Base, TimestampMixin, SoftDeleteMixin
import enum

class SettingsCategory(str, enum.Enum):
    GENERAL = "general"
    ADMISSION = "admission"
    ATTENDANCE = "attendance"
    FEES = "fees"
    EXAM = "exam"
    LIBRARY = "library"
    COMMUNICATION = "communication"
    SECURITY = "security"
    INTEGRATIONS = "integrations"

class School(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "schools"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country: Mapped[str] = mapped_column(String(100), default="India", nullable=False)
    pincode: Mapped[str | None] = mapped_column(String(20), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    favicon_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    established_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    board_affiliation: Mapped[str | None] = mapped_column(String(100), nullable=True)
    affiliation_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    principal_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    principal_signature_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    school_seal_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    primary_color: Mapped[str] = mapped_column(String(10), default="#2563EB", nullable=False)
    secondary_color: Mapped[str] = mapped_column(String(10), default="#7C3AED", nullable=False)
    timezone: Mapped[str] = mapped_column(String(60), default="Asia/Kolkata", nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)
    currency_symbol: Mapped[str] = mapped_column(String(5), default="₹", nullable=False)
    date_format: Mapped[str] = mapped_column(String(30), default="DD/MM/YYYY", nullable=False)
    academic_start_month: Mapped[int] = mapped_column(Integer, default=4, nullable=False)  # April
    plan: Mapped[str] = mapped_column(String(50), default="free", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class SchoolSettings(Base):
    __tablename__ = "school_settings"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    data_type: Mapped[str] = mapped_column(String(20), default="string", nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    from sqlalchemy import UniqueConstraint
    __table_args__ = (
        UniqueConstraint("school_id", "key", name="uq_school_settings_key"),
    )
```

---

## 2. All Settings Keys (seed with `seed_school_defaults`)

Seed these 30+ key-value pairs for every new school:

```python
DEFAULT_SETTINGS = [
    # category, key, value, description, data_type
    ("general", "school_name", "", "School display name", "string"),
    ("general", "timezone", "Asia/Kolkata", "School timezone", "string"),
    ("general", "currency", "INR", "Currency code", "string"),
    ("general", "currency_symbol", "₹", "Currency symbol", "string"),
    ("general", "date_format", "DD/MM/YYYY", "Date display format", "string"),
    ("general", "academic_start_month", "4", "Academic year start month (1-12)", "integer"),

    ("admission", "admission_number_format", "{PREFIX}-{YEAR}-{SEQ:04d}", "Format for admission numbers", "string"),
    ("admission", "admission_number_prefix", "ADM", "Default prefix", "string"),
    ("admission", "admission_number_last_seq", "0", "Last used sequence number", "integer"),

    ("attendance", "working_days", "[1,2,3,4,5,6]", "Working weekdays (1=Mon,7=Sun)", "json"),
    ("attendance", "morning_session_enabled", "true", "Enable morning attendance", "boolean"),
    ("attendance", "afternoon_session_enabled", "false", "Enable afternoon attendance", "boolean"),
    ("attendance", "low_attendance_threshold", "75", "Low attendance warning threshold (%)", "integer"),
    ("attendance", "absent_notify_delay_minutes", "60", "Delay before sending absent SMS", "integer"),
    ("attendance", "auto_notify_absent", "true", "Auto-send SMS for absent students", "boolean"),

    ("fees", "fine_enabled", "true", "Enable late fee fines", "boolean"),
    ("fees", "fine_per_day_paise", "100", "Fine per day in paise (1 rupee = 100 paise)", "integer"),
    ("fees", "fine_grace_period_days", "3", "Days after due before fine starts", "integer"),
    ("fees", "receipt_number_prefix", "RCP", "Receipt number prefix", "string"),
    ("fees", "receipt_number_last_seq", "0", "Last receipt sequence number", "integer"),
    ("fees", "due_reminder_days", "3", "Days before due date to send reminder", "integer"),

    ("exam", "default_pass_percentage", "33", "Default pass % per subject", "integer"),
    ("exam", "grading_scale", "cbse_10", "Grading scale to use", "string"),
    ("exam", "notify_parents_on_result", "true", "SMS parents when results published", "boolean"),

    ("library", "default_loan_days_student", "14", "Default borrow period for students", "integer"),
    ("library", "default_loan_days_staff", "30", "Default borrow period for staff", "integer"),
    ("library", "max_books_student", "3", "Max books a student can borrow", "integer"),
    ("library", "max_books_staff", "5", "Max books staff can borrow", "integer"),
    ("library", "fine_per_day_overdue_paise", "200", "Fine per day for overdue books (paise)", "integer"),

    ("security", "password_min_length", "8", "Minimum password length", "integer"),
    ("security", "max_login_attempts", "5", "Max failed logins before lockout", "integer"),
    ("security", "lockout_minutes", "30", "Account lockout duration (minutes)", "integer"),
    ("security", "session_timeout_minutes", "60", "Idle session timeout", "integer"),

    ("communication", "sms_provider", "msg91", "SMS provider: msg91 or twilio", "string"),
    ("communication", "default_sender_name", "School", "Default SMS sender name", "string"),

    ("integrations", "razorpay_enabled", "false", "Enable Razorpay payment gateway", "boolean"),
    ("integrations", "online_payments_enabled", "false", "Enable online fee payments", "boolean"),
]
```

---

## 3. Pydantic Schemas (`backend/app/schemas/phase3.py` — school + settings section)

```python
from pydantic import BaseModel, HttpUrl, field_validator
from uuid import UUID
from typing import Any

class SchoolProfileUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    pincode: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    established_year: int | None = None
    board_affiliation: str | None = None
    affiliation_number: str | None = None
    principal_name: str | None = None
    primary_color: str | None = None
    secondary_color: str | None = None
    timezone: str | None = None
    currency: str | None = None
    date_format: str | None = None
    academic_start_month: int | None = None

class SchoolResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    code: str | None
    address: str | None
    city: str | None
    state: str | None
    phone: str | None
    email: str | None
    logoUrl: str | None
    primaryColor: str
    secondaryColor: str
    timezone: str
    currency: str
    currencySymbol: str
    isActive: bool

    model_config = {"from_attributes": True}

class SettingsUpdateRequest(BaseModel):
    """Flat dict of key→value pairs. Keys must exist. Values are strings (converted types stored as strings)."""
    settings: dict[str, Any]

class SettingsResponse(BaseModel):
    """Grouped by category: {category: {key: value}}"""
    settings: dict[str, dict[str, Any]]

class TestConnectionRequest(BaseModel):
    channel: str  # "sms" | "email" | "whatsapp"
    recipient: str  # phone or email
```

---

## 4. Repository (`backend/app/repositories/school_repository.py`)

```python
async def get_school_by_id(db, school_id: UUID) -> School | None: ...
async def get_school_by_slug(db, slug: str) -> School | None: ...
async def update_school(db, school: School, data: dict) -> School: ...

async def get_settings(db, school_id: UUID) -> dict[str, dict[str, Any]]:
    """Return all settings grouped by category: {category: {key: typed_value}}"""
    rows = await db.execute(select(SchoolSettings).where(SchoolSettings.school_id == school_id))
    result = {}
    for row in rows.scalars():
        cat = result.setdefault(row.category, {})
        cat[row.key] = _cast_value(row.value, row.data_type)
    return result

async def get_setting(db, school_id: UUID, key: str) -> Any:
    """Get a single setting value (typed)."""
    ...

async def update_settings(db, school_id: UUID, updates: dict[str, Any], updated_by: UUID) -> None:
    """Bulk upsert settings."""
    ...

async def _cast_value(raw: str | None, data_type: str) -> Any:
    if raw is None: return None
    if data_type == "integer": return int(raw)
    if data_type == "boolean": return raw.lower() == "true"
    if data_type == "json": return json.loads(raw)
    return raw
```

---

## 5. Service (`backend/app/services/school_service.py`)

```python
import aiofiles, os
from PIL import Image

async def get_school_profile(db, school_id: UUID) -> School:
    school = await school_repository.get_school_by_id(db, school_id)
    if not school: raise HTTPException(404, "School not found")
    return school

async def update_school_profile(db, school_id: UUID, data: SchoolProfileUpdate, current_user) -> School:
    """Update school profile. Audit log on change."""
    ...

async def upload_logo(db, school_id: UUID, file: UploadFile, current_user) -> str:
    """
    Validate: image/jpeg or image/png, max 5MB.
    Resize to max 400×400 with Pillow.
    Save to {UPLOAD_DIR}/schools/{school_id}/logo.{ext}.
    Update school.logo_url.
    Return URL.
    """
    ...

async def get_school_settings(db, redis, school_id: UUID) -> dict:
    """
    Check Redis cache key settings:{school_id} (TTL 5min).
    On miss: query DB and cache result.
    """
    cache_key = f"settings:{school_id}"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)
    settings = await school_repository.get_settings(db, school_id)
    await redis.setex(cache_key, 300, json.dumps(settings))
    return settings

async def update_school_settings(db, redis, school_id: UUID, updates: dict, current_user) -> None:
    """Bulk update settings. Invalidate Redis cache. Audit log."""
    await school_repository.update_settings(db, school_id, updates, current_user.id)
    await redis.delete(f"settings:{school_id}")
    await log_audit(db, current_user, "settings", "updated", school_id, None, updates)

async def test_connection(db, redis, school_id: UUID, channel: str, recipient: str):
    """Send a test SMS/email/WhatsApp using school's configured credentials."""
    settings = await get_school_settings(db, redis, school_id)
    if channel == "sms":
        # Call SMS provider with test message
        ...
    elif channel == "email":
        ...
    elif channel == "whatsapp":
        ...
```

---

## 6. API Endpoints (`backend/app/api/v1/endpoints/schools.py`)

```
GET    /schools/profile           → get current school profile
PUT    /schools/profile           → update school profile  [permission: settings:update]
POST   /schools/profile/logo      → upload logo (multipart)  [permission: settings:update]
GET    /schools/settings          → get all settings grouped by category  [permission: settings:view]
PUT    /schools/settings          → bulk update settings  [permission: settings:manage]
POST   /schools/settings/test     → test SMS/email/WhatsApp connection  [permission: settings:manage]
```

---

## 7. Settings Service: `get_setting_value` Helper

Create a helper used by all other services to read a specific setting:

```python
# backend/app/utils/settings_helper.py
async def get_setting_value(db, redis, school_id: UUID, key: str, default=None):
    """Fast lookup: check Redis cache first, then DB. Returns typed value."""
    settings = await school_service.get_school_settings(db, redis, school_id)
    for category_settings in settings.values():
        if key in category_settings:
            return category_settings[key]
    return default
```

All services use this helper. Example: `low_threshold = await get_setting_value(db, redis, school_id, "low_attendance_threshold", default=75)`

---

## 8. Frontend: Types

```typescript
export interface School {
  id: string;
  name: string;
  slug: string;
  code?: string;
  address?: string;
  city?: string;
  state?: string;
  phone?: string;
  email?: string;
  logoUrl?: string;
  primaryColor: string;
  secondaryColor: string;
  timezone: string;
  currency: string;
  currencySymbol: string;
  isActive: boolean;
}

export type SettingsMap = Record<string, Record<string, string | number | boolean>>;
```

---

## 9. Frontend: API Layer (`frontend/src/api/schools.ts`)

```typescript
import api from './axios';

export const getSchoolProfileApi = async () => {
  const res = await api.get<{ data: School }>('/schools/profile');
  return res.data.data;
};

export const updateSchoolProfileApi = async (data: Partial<School>) => {
  const res = await api.put<{ data: School }>('/schools/profile', data);
  return res.data.data;
};

export const uploadLogoApi = async (file: File) => {
  const form = new FormData();
  form.append('file', file);
  const res = await api.post<{ data: { logoUrl: string } }>('/schools/profile/logo', form,
    { headers: { 'Content-Type': 'multipart/form-data' } });
  return res.data.data.logoUrl;
};

export const getSchoolSettingsApi = async () => {
  const res = await api.get<{ data: SettingsMap }>('/schools/settings');
  return res.data.data;
};

export const updateSchoolSettingsApi = async (settings: Record<string, unknown>) => {
  const res = await api.put('/schools/settings', { settings });
  return res.data;
};

export const testConnectionApi = async (channel: string, recipient: string) =>
  api.post('/schools/settings/test', { channel, recipient });
```

---

## 10. Frontend: Settings Page (`frontend/src/pages/settings/SettingsPage.tsx`)

Build a full settings page at `/settings` with 9 tabs:

### Tab 1: General
- School name, address, city, state, phone, email, website
- Logo upload (drag-and-drop or file picker) with preview
- Academic start month dropdown (Jan–Dec)
- Timezone, currency, date format dropdowns

### Tab 2: Admission
- Admission number format input (with placeholder help text)
- Admission number prefix input
- Reset sequence number button (admin only)

### Tab 3: Attendance
- Working days multi-select (Mon–Sat checkboxes)
- Morning/Afternoon sessions toggle
- Low attendance threshold % input
- Auto-notify absent toggle
- Delay minutes input

### Tab 4: Fees
- Fine enabled toggle
- Fine per day (shown in rupees, stored as paise)
- Fine grace period days
- Receipt prefix
- Due reminder days

### Tab 5: Library
- Default loan days (student/staff)
- Max books (student/staff)
- Fine per day (rupees → paise)

### Tab 6: Exam
- Default pass percentage
- Notify parents on result toggle

### Tab 7: Communication
- SMS provider dropdown (msg91/twilio)
- MSG91 auth key
- MSG91 sender ID
- SMTP host, port, user, password (optional)
- WhatsApp token and phone number ID
- "Test SMS" button → opens dialog → enter phone → send test → show result
- "Test Email" button → similar

### Tab 8: Security
- Password min length
- Max login attempts
- Lockout duration
- Session timeout

### Tab 9: Integrations
- Razorpay enabled toggle
- Razorpay key ID, secret (password fields)
- Online payments toggle

Each tab has a **Save** button. All numeric fields stored as integers (paise converter shown for money fields). All fields use React Hook Form + Zod. Changes show toast on success.

---

## 11. Sidebar Navigation

Add to `Sidebar.tsx`:
- `Settings` → `/settings` (visible to `school_admin`)

Add to `Navbar.tsx`:
- School logo in top-left (from `schoolInfo.logoUrl` in Zustand store)
- School name next to logo

---

## Verification Checklist

- [ ] `GET /api/v1/schools/profile` returns school data
- [ ] `PUT /api/v1/schools/profile` updates and returns updated profile
- [ ] Logo upload resizes image and saves to `uploads/schools/{id}/logo.{ext}`
- [ ] `GET /api/v1/schools/settings` returns all 30+ settings grouped by category
- [ ] `PUT /api/v1/schools/settings` updates settings and invalidates Redis cache
- [ ] Redis cache `settings:{school_id}` is populated after first GET and cleared after PUT
- [ ] `get_setting_value` helper returns typed values (int for integer, bool for boolean)
- [ ] Settings page loads with current values from API
- [ ] All 9 settings tabs render correctly
- [ ] Logo upload shows drag-and-drop preview
- [ ] Test connection dialog sends test message
