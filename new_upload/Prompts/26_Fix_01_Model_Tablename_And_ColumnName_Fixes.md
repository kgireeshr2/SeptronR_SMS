# FIX PROMPT 01 — Model Tablename & Column Name Alignment

## Context
The SQLAlchemy models were written with column names that differ from the DB columns created by the Alembic migration. In several cases the DB column name is correct and the model should be updated to match. This prompt covers **renaming columns in the models only** (no DB schema change needed — the DB already has these columns under different names).

Run AFTER the backend server is stopped. After changes, run: `alembic revision --autogenerate -m "sync_model_column_names"` to generate a migration if any rename is detected (postgres `ALTER TABLE ... RENAME COLUMN`).

---

## 1. Fix `StaffPayroll` tablename

**File:** `backend/app/models/staff.py`

Find the `StaffPayroll` class. Change:
```python
__tablename__ = "staff_payroll"
```
to:
```python
__tablename__ = "staff_payrolls"
```

---

## 2. Fix `Timetable` tablename

**File:** `backend/app/models/classes.py`

Find the `Timetable` class. Change:
```python
__tablename__ = "timetable"
```
to:
```python
__tablename__ = "timetables"
```

---

## 3. Fix `StaffLeave` column names

**File:** `backend/app/models/staff.py`

In `StaffLeave`:
- Rename column `total_days` → `days_count` (DB column name)
- Rename column `approved_by` → `reviewed_by` (DB column name)  
- Rename column `approved_at` → `reviewed_at` (DB column name)

```python
# Change:
total_days: Mapped[float] = mapped_column(...)
approved_by: Mapped[Optional[UUID]] = mapped_column(...)
approved_at: Mapped[Optional[datetime]] = mapped_column(...)

# To:
days_count: Mapped[float] = mapped_column(...)
reviewed_by: Mapped[Optional[UUID]] = mapped_column(...)
reviewed_at: Mapped[Optional[datetime]] = mapped_column(...)
```

Also update any service/schema/repository that references `total_days`, `approved_by`, `approved_at` for leaves.

---

## 4. Fix `StaffAttendance` column names

**File:** `backend/app/models/attendance.py`

In `StaffAttendance`:
- Rename `check_in` → `check_in_time`
- Rename `check_out` → `check_out_time`

Also update all services/schemas/repositories referencing these fields.

---

## 5. Fix `Holiday` column name

**File:** `backend/app/models/attendance.py`

In `Holiday`:
- Rename `holiday_type` → `type`

Update all services/schemas using `holiday_type`.

---

## 6. Fix `Department` column name

**File:** `backend/app/models/staff.py`

In `Department`:
- Rename `hod_id` → `head_id` (DB column name)

Update all services/schemas referencing `hod_id`.

---

## 7. Fix `Notification` column names

**File:** `backend/app/models/communications.py`

In `Notification`:
- Rename `data` → `metadata` (DB column name; note `metadata` is a reserved SQLAlchemy name — use `info` or keep as `notification_data` with `mapped_column("metadata")`)

Recommended approach — keep Python attribute name but map to DB column:
```python
notification_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, nullable=True)
```

Or simply rename to `metadata` with a `Column("metadata", ...)` if not conflicting.

Also add missing column `scheduled_at` and `sent_at` to the model (these exist in DB but not model).

---

## 8. Fix `Announcement` column names

**File:** `backend/app/models/communications.py`

In `Announcement`:
- Rename `content` → `body` (DB column name)
- Rename `published_at` → `publish_at` (DB column name)
- Rename `is_published` → `is_active` (DB column name)

Remove these from model if not in DB: `attachment_url`, `target_class_id`, `target_section_id` (or add them as nullable+migration, see Fix 02).

Also add `audience_filter` column that exists in DB but not model.

---

## 9. Fix `NotificationTemplate` column names

**File:** `backend/app/models/communications.py`

In `NotificationTemplate`:
- Rename `channel` → `channels` (DB column name — it stores array/JSON of channels)
- Rename `body` → `body_template` (DB column name)

---

## 10. Fix `Item` (Inventory) column names

**File:** `backend/app/models/inventory.py`

In `Item`:
- Rename `sku` → `item_code` (DB column name)
- Rename `reorder_level` → `min_stock_level` (DB column name)

---

## 11. Fix `LibraryMember` column name

**File:** `backend/app/models/library.py`

In `LibraryMember`:
- Rename `max_books` → `max_books_allowed` (DB column name)

---

## 12. Update All Schemas/Services/Repositories

After updating model column names, search for and update every reference in:
- `backend/app/schemas/` — all Pydantic schema files
- `backend/app/services/` — all service files
- `backend/app/repositories/` — all repository files
- `backend/app/api/` — all route files

Use VSCode search-replace for each rename:
- `total_days` → `days_count` (in leave context)
- `approved_by` → `reviewed_by` (in leave context)
- `approved_at` → `reviewed_at` (in leave context)
- `check_in` → `check_in_time` (in staff attendance context)
- `check_out` → `check_out_time` (in staff attendance context)
- `holiday_type` → `type` (in holiday context — careful: `type` is generic)
- `hod_id` → `head_id` (in department context)
- `sku` → `item_code` (in inventory context)
- `reorder_level` → `min_stock_level` (in inventory context)
- `max_books` → `max_books_allowed` (in library context)
- `content` → `body` (in announcement context)
- `is_published` → `is_active` (in announcement context)
- `published_at` → `publish_at` (in announcement context)
- `channel` → `channels` (in notification template context)
- `.body` → `.body_template` (in notification template context)

---

## 13. Generate & Apply Migration

```bash
cd backend
alembic revision --autogenerate -m "sync_column_renames"
# Review the generated migration file
alembic upgrade head
```

## Post-Fix Verification

```bash
# Test models that were failing
python -c "
import asyncio, sys
sys.path.insert(0, '.')
from sqlalchemy import select
async def test():
    from app.db.session import async_session_factory
    from app.models.staff import StaffLeave, StaffPayroll, Department
    from app.models.attendance import StaffAttendance, Holiday
    from app.models.communications import Notification, Announcement, NotificationTemplate
    from app.models.inventory import Item
    from app.models.library import LibraryMember
    for model in [StaffLeave, StaffPayroll, Department, StaffAttendance, Holiday,
                  Notification, Announcement, NotificationTemplate, Item, LibraryMember]:
        async with async_session_factory() as s:
            await s.execute(select(model).limit(1))
            print(f'OK: {model.__name__}')
asyncio.run(test())
"
```
