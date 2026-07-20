# FIX PROMPT 02 — Alembic Migration: Add Missing DB Columns

## Context
The SQLAlchemy models reference many columns that simply don't exist in the current DB schema. This migration adds all missing columns using `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`. These are NEW columns being added to existing tables.

This must be done **AFTER** Fix 01 (column renames) to avoid conflicts.

---

## Steps

### 1. Create the migration file

```bash
cd backend
alembic revision -m "add_missing_columns_phase2_sync"
```

### 2. Populate the migration

Paste the following into the generated file (edit `upgrade()` and `downgrade()`):

```python
"""add_missing_columns_phase2_sync

Revision ID: add_missing_cols_sync
Revises: phase21abc123
Create Date: 2025-07-18
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = 'add_missing_cols_sync'
down_revision = 'phase21abc123'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ─── STUDENTS ───────────────────────────────────────────────────────────────
    op.execute("ALTER TABLE students ADD COLUMN IF NOT EXISTS admission_date DATE")
    op.execute("ALTER TABLE students ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ")
    op.execute("ALTER TABLE students ADD COLUMN IF NOT EXISTS deleted_by UUID REFERENCES users(id)")

    # ─── STAFF ──────────────────────────────────────────────────────────────────
    op.execute("ALTER TABLE staff ADD COLUMN IF NOT EXISTS salary_type VARCHAR(20) DEFAULT 'monthly'")
    op.execute("ALTER TABLE staff ADD COLUMN IF NOT EXISTS monthly_salary NUMERIC(12,2)")
    op.execute("ALTER TABLE staff ADD COLUMN IF NOT EXISTS bank_account_no VARCHAR(30)")
    op.execute("ALTER TABLE staff ADD COLUMN IF NOT EXISTS bank_name VARCHAR(100)")
    op.execute("ALTER TABLE staff ADD COLUMN IF NOT EXISTS ifsc_code VARCHAR(20)")
    op.execute("ALTER TABLE staff ADD COLUMN IF NOT EXISTS emergency_contact VARCHAR(20)")
    op.execute("ALTER TABLE staff ADD COLUMN IF NOT EXISTS qualifications TEXT")
    op.execute("ALTER TABLE staff ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ")
    op.execute("ALTER TABLE staff ADD COLUMN IF NOT EXISTS deleted_by UUID REFERENCES users(id)")

    # ─── CLASSES ────────────────────────────────────────────────────────────────
    op.execute("ALTER TABLE classes ADD COLUMN IF NOT EXISTS academic_year_id UUID REFERENCES academic_years(id)")
    op.execute("ALTER TABLE classes ADD COLUMN IF NOT EXISTS numeric_level INTEGER")
    # Backfill numeric_level from existing `level` column (convert text to int where possible)
    op.execute("""
        UPDATE classes SET numeric_level = CASE
            WHEN level ~ '^[0-9]+$' THEN level::integer
            ELSE NULL
        END
        WHERE numeric_level IS NULL
    """)

    # ─── SECTIONS ───────────────────────────────────────────────────────────────
    op.execute("ALTER TABLE sections ADD COLUMN IF NOT EXISTS capacity INTEGER")
    # Backfill capacity from existing max_students
    op.execute("UPDATE sections SET capacity = max_students WHERE capacity IS NULL AND max_students IS NOT NULL")

    # ─── SUBJECTS ───────────────────────────────────────────────────────────────
    op.execute("ALTER TABLE subjects ADD COLUMN IF NOT EXISTS full_marks INTEGER DEFAULT 100")
    op.execute("ALTER TABLE subjects ADD COLUMN IF NOT EXISTS pass_marks INTEGER DEFAULT 35")

    # ─── HOMEWORK ───────────────────────────────────────────────────────────────
    op.execute("ALTER TABLE homework ADD COLUMN IF NOT EXISTS academic_year_id UUID REFERENCES academic_years(id)")

    # ─── PTM EVENTS ─────────────────────────────────────────────────────────────
    op.execute("ALTER TABLE ptm_events ADD COLUMN IF NOT EXISTS venue VARCHAR(255)")
    op.execute("ALTER TABLE ptm_events ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW()")

    # ─── CALENDAR EVENTS ────────────────────────────────────────────────────────
    op.execute("ALTER TABLE calendar_events ADD COLUMN IF NOT EXISTS location VARCHAR(255)")

    # ─── STUDENT ATTENDANCE ─────────────────────────────────────────────────────
    op.execute("ALTER TABLE student_attendance ADD COLUMN IF NOT EXISTS notified_at TIMESTAMPTZ")

    # ─── NOTIFICATIONS ──────────────────────────────────────────────────────────
    op.execute("ALTER TABLE notifications ADD COLUMN IF NOT EXISTS read_at TIMESTAMPTZ")
    # Note: model uses 'data' but DB has 'metadata'. 
    # After Fix 01 renames model to use 'metadata', no column add needed here.
    # If keeping model column as 'data', add:
    # op.execute("ALTER TABLE notifications ADD COLUMN IF NOT EXISTS data JSONB")

    # ─── ANNOUNCEMENTS ──────────────────────────────────────────────────────────
    # Note: After Fix 01 renames model to use 'body'/'is_active'/'publish_at', 
    # these columns already exist in DB. Only add new columns:
    op.execute("ALTER TABLE announcements ADD COLUMN IF NOT EXISTS attachment_url TEXT")
    op.execute("ALTER TABLE announcements ADD COLUMN IF NOT EXISTS target_class_id UUID REFERENCES classes(id)")
    op.execute("ALTER TABLE announcements ADD COLUMN IF NOT EXISTS target_section_id UUID REFERENCES sections(id)")

    # ─── BOOKS ──────────────────────────────────────────────────────────────────
    op.execute("ALTER TABLE books ADD COLUMN IF NOT EXISTS language VARCHAR(50) DEFAULT 'English'")
    op.execute("ALTER TABLE books ADD COLUMN IF NOT EXISTS cover_image_url TEXT")
    op.execute("ALTER TABLE books ADD COLUMN IF NOT EXISTS rack_number VARCHAR(20)")

    # ─── LIBRARY MEMBERS ────────────────────────────────────────────────────────
    op.execute("ALTER TABLE library_members ADD COLUMN IF NOT EXISTS entity_id UUID")
    op.execute("ALTER TABLE library_members ADD COLUMN IF NOT EXISTS membership_valid_until DATE")
    # Note: After Fix 01 renames model to use 'max_books_allowed', no column add needed.

    # ─── BOOK ISSUES ────────────────────────────────────────────────────────────
    op.execute("ALTER TABLE book_issues ADD COLUMN IF NOT EXISTS issued_by UUID REFERENCES users(id)")
    op.execute("ALTER TABLE book_issues ADD COLUMN IF NOT EXISTS fine_per_day NUMERIC(8,2) DEFAULT 1.00")
    op.execute("ALTER TABLE book_issues ADD COLUMN IF NOT EXISTS fine_paid BOOLEAN DEFAULT FALSE")
    op.execute("ALTER TABLE book_issues ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'issued'")
    op.execute("ALTER TABLE book_issues ADD COLUMN IF NOT EXISTS remarks TEXT")

    # ─── INCOME RECORDS ─────────────────────────────────────────────────────────
    op.execute("ALTER TABLE income_records ADD COLUMN IF NOT EXISTS academic_year_id UUID REFERENCES academic_years(id)")
    op.execute("ALTER TABLE income_records ADD COLUMN IF NOT EXISTS payment_mode VARCHAR(30)")
    op.execute("ALTER TABLE income_records ADD COLUMN IF NOT EXISTS transaction_id VARCHAR(100)")
    op.execute("ALTER TABLE income_records ADD COLUMN IF NOT EXISTS is_fee_income BOOLEAN DEFAULT FALSE")
    op.execute("ALTER TABLE income_records ADD COLUMN IF NOT EXISTS fee_payment_id UUID REFERENCES fee_payments(id)")
    op.execute("ALTER TABLE income_records ADD COLUMN IF NOT EXISTS created_by UUID REFERENCES users(id)")

    # ─── EXPENSE RECORDS ────────────────────────────────────────────────────────
    op.execute("ALTER TABLE expense_records ADD COLUMN IF NOT EXISTS academic_year_id UUID REFERENCES academic_years(id)")
    op.execute("ALTER TABLE expense_records ADD COLUMN IF NOT EXISTS payee_name VARCHAR(200)")
    op.execute("ALTER TABLE expense_records ADD COLUMN IF NOT EXISTS invoice_number VARCHAR(100)")
    op.execute("ALTER TABLE expense_records ADD COLUMN IF NOT EXISTS invoice_url TEXT")
    op.execute("ALTER TABLE expense_records ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'approved'")
    op.execute("ALTER TABLE expense_records ADD COLUMN IF NOT EXISTS created_by UUID REFERENCES users(id)")

    # ─── INVENTORY ITEMS ────────────────────────────────────────────────────────
    # Note: After Fix 01 renames 'sku'→'item_code' and 'reorder_level'→'min_stock_level'
    # in model, only add truly new columns:
    op.execute("ALTER TABLE items ADD COLUMN IF NOT EXISTS is_consumable BOOLEAN DEFAULT FALSE")

    # ─── DEPARTMENTS ────────────────────────────────────────────────────────────
    # Note: After Fix 01 renames 'hod_id'→'head_id' in model, no column add needed.
    # head_id already exists in DB.

    # ─── RENAME DB TABLES to match models ───────────────────────────────────────
    # staff_payrolls → staff_payroll (to match model __tablename__)
    op.execute("ALTER TABLE IF EXISTS staff_payrolls RENAME TO staff_payroll")
    # timetables → timetable
    op.execute("ALTER TABLE IF EXISTS timetables RENAME TO timetable")


def downgrade() -> None:
    # Reverse table renames
    op.execute("ALTER TABLE IF EXISTS staff_payroll RENAME TO staff_payrolls")
    op.execute("ALTER TABLE IF EXISTS timetable RENAME TO timetables")

    # Drop added columns (add DROP COLUMN statements for each column added above)
    # Students
    op.execute("ALTER TABLE students DROP COLUMN IF EXISTS admission_date")
    op.execute("ALTER TABLE students DROP COLUMN IF EXISTS deleted_at")
    op.execute("ALTER TABLE students DROP COLUMN IF EXISTS deleted_by")
    # Staff
    op.execute("ALTER TABLE staff DROP COLUMN IF EXISTS salary_type")
    op.execute("ALTER TABLE staff DROP COLUMN IF EXISTS monthly_salary")
    op.execute("ALTER TABLE staff DROP COLUMN IF EXISTS bank_account_no")
    op.execute("ALTER TABLE staff DROP COLUMN IF EXISTS bank_name")
    op.execute("ALTER TABLE staff DROP COLUMN IF EXISTS ifsc_code")
    op.execute("ALTER TABLE staff DROP COLUMN IF EXISTS emergency_contact")
    op.execute("ALTER TABLE staff DROP COLUMN IF EXISTS qualifications")
    op.execute("ALTER TABLE staff DROP COLUMN IF EXISTS deleted_at")
    op.execute("ALTER TABLE staff DROP COLUMN IF EXISTS deleted_by")
    # Classes
    op.execute("ALTER TABLE classes DROP COLUMN IF EXISTS academic_year_id")
    op.execute("ALTER TABLE classes DROP COLUMN IF EXISTS numeric_level")
    # Sections
    op.execute("ALTER TABLE sections DROP COLUMN IF EXISTS capacity")
    # Subjects
    op.execute("ALTER TABLE subjects DROP COLUMN IF EXISTS full_marks")
    op.execute("ALTER TABLE subjects DROP COLUMN IF EXISTS pass_marks")
    # Homework
    op.execute("ALTER TABLE homework DROP COLUMN IF EXISTS academic_year_id")
    # PTM Events
    op.execute("ALTER TABLE ptm_events DROP COLUMN IF EXISTS venue")
    op.execute("ALTER TABLE ptm_events DROP COLUMN IF EXISTS updated_at")
    # Calendar Events
    op.execute("ALTER TABLE calendar_events DROP COLUMN IF EXISTS location")
    # Student Attendance
    op.execute("ALTER TABLE student_attendance DROP COLUMN IF EXISTS notified_at")
    # Notifications
    op.execute("ALTER TABLE notifications DROP COLUMN IF EXISTS read_at")
    # Announcements
    op.execute("ALTER TABLE announcements DROP COLUMN IF EXISTS attachment_url")
    op.execute("ALTER TABLE announcements DROP COLUMN IF EXISTS target_class_id")
    op.execute("ALTER TABLE announcements DROP COLUMN IF EXISTS target_section_id")
    # Books
    op.execute("ALTER TABLE books DROP COLUMN IF EXISTS language")
    op.execute("ALTER TABLE books DROP COLUMN IF EXISTS cover_image_url")
    op.execute("ALTER TABLE books DROP COLUMN IF EXISTS rack_number")
    # Library members
    op.execute("ALTER TABLE library_members DROP COLUMN IF EXISTS entity_id")
    op.execute("ALTER TABLE library_members DROP COLUMN IF EXISTS membership_valid_until")
    # Book issues
    op.execute("ALTER TABLE book_issues DROP COLUMN IF EXISTS issued_by")
    op.execute("ALTER TABLE book_issues DROP COLUMN IF EXISTS fine_per_day")
    op.execute("ALTER TABLE book_issues DROP COLUMN IF EXISTS fine_paid")
    op.execute("ALTER TABLE book_issues DROP COLUMN IF EXISTS status")
    op.execute("ALTER TABLE book_issues DROP COLUMN IF EXISTS remarks")
    # Income records
    op.execute("ALTER TABLE income_records DROP COLUMN IF EXISTS academic_year_id")
    op.execute("ALTER TABLE income_records DROP COLUMN IF EXISTS payment_mode")
    op.execute("ALTER TABLE income_records DROP COLUMN IF EXISTS transaction_id")
    op.execute("ALTER TABLE income_records DROP COLUMN IF EXISTS is_fee_income")
    op.execute("ALTER TABLE income_records DROP COLUMN IF EXISTS fee_payment_id")
    op.execute("ALTER TABLE income_records DROP COLUMN IF EXISTS created_by")
    # Expense records
    op.execute("ALTER TABLE expense_records DROP COLUMN IF EXISTS academic_year_id")
    op.execute("ALTER TABLE expense_records DROP COLUMN IF EXISTS payee_name")
    op.execute("ALTER TABLE expense_records DROP COLUMN IF EXISTS invoice_number")
    op.execute("ALTER TABLE expense_records DROP COLUMN IF EXISTS invoice_url")
    op.execute("ALTER TABLE expense_records DROP COLUMN IF EXISTS status")
    op.execute("ALTER TABLE expense_records DROP COLUMN IF EXISTS created_by")
    # Items
    op.execute("ALTER TABLE items DROP COLUMN IF EXISTS is_consumable")
```

### 3. Apply the migration

```bash
cd backend
alembic upgrade head
```

### 4. Verify

```bash
alembic current
# Should show: add_missing_cols_sync (head)
```

---

## Important Notes

1. Run Fix 01 FIRST (column renames in Python models) before this migration
2. The table renames at end of `upgrade()` (staff_payrolls→staff_payroll, timetables→timetable) must be done carefully — any existing data will be preserved
3. If the `alembic_version` table has the old revision, check with `alembic history` before running
4. After applying, restart the uvicorn server: the models will now find all columns

---

## Post-Migration API Test

```powershell
$token = (Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/auth/login" -ContentType "application/json" -Body '{"username":"superadmin","password":"SuperAdmin@123"}').data.access_token
$headers = @{Authorization = "Bearer $token"}

# These should now all return 200:
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/students" -Headers $headers
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/staff" -Headers $headers
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/classes" -Headers $headers
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/attendance/holidays" -Headers $headers
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/library/books" -Headers $headers
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/accounting/income" -Headers $headers
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/homework" -Headers $headers
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/notifications" -Headers $headers
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/announcements" -Headers $headers
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/calendar/events" -Headers $headers
```
