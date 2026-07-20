# FIX PROMPT 04 — Apply Fixes Already Done + Additional API Logic Fixes

## Context
This prompt documents fixes already applied (so they're not redone) and covers remaining API logic bugs discovered through testing.

---

## A. Already Fixed (Do NOT redo)

### Fix A1 — `ok()` Serialization Bug ✅ ALREADY FIXED
**File:** `backend/app/utils/response.py`

The `ok()` utility now uses `jsonable_encoder(data)` before wrapping in `APIResponse`. This fixes all `TypeError: Object of type X is not JSON serializable` 500 errors.

**Verification:** `GET /academic-years` returns 200 instead of 500.

### Fix A2 — `SchoolOverview.code` Nullable ✅ ALREADY FIXED
**File:** `backend/app/schemas/phase21.py`

`SchoolOverview.code` and `SchoolOverview.slug` are now `Optional[str] = None`.

**Verification:** `GET /superadmin/schools` returns 200 instead of 500.

---

## B. Transport Module — Class/Import Name Fixes

### Problem
The transport API routes and services likely reference `TransportRoute` and `TransportAssignment` class names, but the model file `app/models/transport.py` only has `Route` and `StudentTransport`.

### Fix

**File:** `backend/app/models/transport.py`

Add class aliases or rename to what the services expect:

```python
# Option 1: Add aliases at end of file
TransportRoute = Route
TransportAssignment = StudentTransport
```

OR find all service/repository files that reference `TransportRoute` and `TransportAssignment` and update to use `Route` and `StudentTransport`:

```bash
# Find all references
grep -r "TransportRoute\|TransportAssignment" backend/app/
```

Update each import in services/repositories to use `Route` and `StudentTransport`.

---

## C. Exam Results — Model & Endpoint Fix

### Problem
There is no `ExamResult` class in `app/models/exams.py`. The DB has a `student_marks` table. The model likely uses `StudentMark`. Check:

```bash
grep -r "class.*Mark\|class.*Result\|student_marks" backend/app/models/
```

### Fix
Find the exam results model (likely `StudentMark`) and check if it matches the DB `student_marks` table. Ensure service layer references correct class name.

---

## D. Admission Application — Model Fix

### Problem
`AdmissionApplication` class not found in `app/models/admissions.py`. DB has `admission_forms` table.

### Fix
Check the admissions model file:
```bash
cat backend/app/models/admissions.py
```

Update service references to use actual class name found.

---

## E. Redis / Background Tasks

### Problem
Redis is disabled. Background tasks (email notifications, SMS) will fail silently or raise connection errors.

### Fix — Option 1 (Development)
Add graceful fallback when Redis unavailable:

In any task file that uses Redis/Celery:
```python
try:
    # send notification via Redis queue
    task.delay(...)
except Exception:
    # fallback: log and continue, don't crash the request
    logger.warning("Redis unavailable, notification queued locally")
```

### Fix — Option 2 (Enable Redis)
Uncomment Redis in docker-compose and update `REDIS_URL` in `.env`.

---

## F. Frontend Integration — API Base URL

The frontend `vite.config.ts` proxy or `.env` must point to the correct backend URL. Verify:

**File:** `frontend/vite.config.ts` OR `frontend/.env`

```typescript
// vite.config.ts proxy section:
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
  }
}
```

OR in `frontend/src/api/` (axios baseURL):
```typescript
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
});
```

---

## G. Permission Check Middleware

After testing, verify RBAC middleware is validating permissions correctly. The superadmin user has 84+ permissions — test a staff user with limited permissions to verify:

1. Create a teacher user with limited permissions
2. Attempt to access admin-only endpoints
3. Verify 403 responses are returned correctly

---

## H. Summary of All Fix Steps in Order

Apply fixes in this sequence to minimize conflicts:

```
1. Apply Fix 01 (column renames in Python models)
   → Restart uvicorn after changes
   
2. Apply Fix 02 (Alembic migration)
   → cd backend && alembic upgrade head
   → Restart uvicorn

3. Apply Fix 03 (Pydantic schema updates)
   → Restart uvicorn

4. Apply Fix 04-B (Transport class name aliases)
5. Apply Fix 04-C (ExamResult/StudentMark class name)
6. Apply Fix 04-D (AdmissionApplication class name)

7. Run full API test suite to verify all modules return 200 on GET
8. Run CRUD test for each module (Create, Read, Update, Delete)
```

---

## I. Alembic Migration Sequence Check

After applying all fixes, verify migration history:

```bash
cd backend
alembic history
alembic current
```

Expected:
```
phase21abc123 → add_missing_cols_sync (head)
```

If `alembic current` shows wrong head or multiple heads:
```bash
alembic merge heads -m "merge_heads"
alembic upgrade head
```
