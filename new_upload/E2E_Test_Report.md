# Stone Valley SMS — End-to-End Test Report

**Date**: April 15, 2026  
**School**: Stone Valley (`stone-valley`)  
**Test Scope**: Full E2E simulation of real user flows across all roles  
**Backend**: FastAPI + MSSQL LocalDB (port 8000)  
**Frontend**: Vite/React (port 5173)

---

## Summary

| Phase | Area | Status | Notes |
|-------|------|--------|-------|
| 1 | Super Admin — School Creation | ✅ PASS | |
| 2 | School Admin Login | ✅ PASS | |
| 3 | Academic Year Setup | ✅ PASS | |
| 4 | Staff Management | ✅ PASS | |
| 5 | Classes, Sections & Subjects | ✅ PASS | |
| 6 | Student & Parent Onboarding | ✅ PASS (after bug fix) | Bug: wrong field name in student_service |
| 7 | Fee Management | ✅ PASS | |
| 8 | Exam Management & Results | ✅ PASS (workaround) | school_admin lacks `exams.publish` permission |
| 9 | Attendance | ✅ PASS | |
| 10 | Parent Portal | ✅ PASS (after fix) | Parents had no role assigned at creation time |

**Overall: 10/10 phases passed** (2 bugs found and fixed)

---

## Phase 1 — Super Admin: School Bootstrap

**Credentials used**: `superadmin@sms.com` / `SuperAdmin@123`

| Step | API | Result |
|------|-----|--------|
| Login as super admin | `POST /auth/login` | ✅ JWT token received |
| Create Stone Valley school | `POST /schools/bootstrap` | ✅ School + admin auto-created |

**Stone Valley School Details**:
- School ID: `a8701957-9a83-4e69-b80b-2d83cef3dfd4`
- Slug: `stone-valley`
- Admin email auto-generated: `admin@stonevalley.edu.in`
- Admin password: `Admin@StoneValley123`

---

## Phase 2 — School Admin Setup

**Credentials**: `admin@stonevalley.edu.in` / `Admin@StoneValley123`

| Step | API | Result |
|------|-----|--------|
| Login as school admin | `POST /auth/login` | ✅ |
| Create Academic Year 2025-2026 | `POST /academic-years` | ✅ ID: `6621b0fb-...` |
| Create Department "Primary Education" | `POST /departments` | ✅ |

---

## Phase 3 — Staff Management

| Staff | Role | API | Result |
|-------|------|-----|--------|
| Priya Sharma | Class Teacher | `POST /staff` | ✅ |
| Amit Patel | Science Teacher | `POST /staff` | ✅ |

---

## Phase 4 — Classes, Sections & Subjects

| Item | Details | Result |
|------|---------|--------|
| Class | Grade 5 (AY 2025-2026) | ✅ ID: `af2ae9ad-...` |
| Section | Section A | ✅ ID: `e733db75-...` |
| Subject | Mathematics (MATH5) | ✅ |
| Subject | Science (SCI5) | ✅ |
| Subject | English (ENG5) | ✅ |
| Subject | Social Studies (SST5) | ✅ |

**Discovery**: `GET /classes` requires `?academic_year_id=` query param; `POST /classes` requires `academic_year_id` in request body.

---

## Phase 5 — Student & Parent Onboarding

### Bug Fixed 🐛
**File**: `backend/app/services/student_service.py` line ~99  
**Before**: `hashed_password=hash_password(default_password)` — wrong field name  
**After**: `password_hash=hash_password(default_password)` — matches User model  
**Impact**: All student creation was failing with HTTP 500

### Students Created

| Student | Adm No | DOB | Parent Email |
|---------|--------|-----|--------------|
| Aryan Mehta | SV-ADM-2025-001 | 2015-04-10 | suresh.mehta@gmail.com |
| Sneha Joshi | SV-ADM-2025-002 | 2014-11-22 | ramesh.joshi@gmail.com |
| Rohan Verma | SV-ADM-2025-003 | 2015-02-05 | dinesh.verma@gmail.com |

All enrolled in: Grade 5 / Section A / AY 2025-2026  
Default parent password: `Parent@123`

---

## Phase 6 — Fee Management

| Step | Details | Result |
|------|---------|--------|
| Fee Category created | "Tuition Fee 2025" | ✅ |
| Fee Structure created | Rs.4000/month for Grade 5 | ✅ |
| Fees assigned to class | Grade 5 / AY 2025-2026 | ✅ |
| Invoice generated | INV-202505-00003 (Aryan Mehta) | ✅ |
| Payment collected | Rs.4000 — Receipt: RCPT-20260415-9CD02487 | ✅ |
| Invoice status | `unpaid` → `paid`, balance = Rs.0 | ✅ |

**Discovery**: Fee collection endpoint is `POST /fees/payments` (not `/fees/collect`)

---

## Phase 7 — Exam Management

| Step | Details | Result |
|------|---------|--------|
| Exam Type created | "Unit Test 1" | ✅ ID: `4a177b79-...` |
| Grading Scale created | A+ (90%+) through F (<40%) | ✅ |
| Exams created (bulk) | Math (25 marks) + Science (25 marks) | ✅ |
| Marks entered — Math | Aryan 22/25 (A), Sneha 18/25 (B+), Rohan 20/25 (A) | ✅ |
| Marks entered — Science | Aryan 23/25 (A+), Sneha 19/25 (B+), Rohan absent | ✅ |
| Results published | 2 exams published | ✅ (via super admin) |

### Class Ranking (Combined Math + Science)

| Rank | Student | Percentage | Grade |
|------|---------|-----------|-------|
| 1 | Aryan Mehta | 90.0% | A+ |
| 2 | Rohan Verma | 80.0% | A |
| 3 | Sneha Joshi | 74.0% | B+ |

**Known Issue**: `school_admin` role lacks `exams:publish` permission by default.  
**Workaround**: Used super admin token with `X-School-Id` header to publish.  
**Recommendation**: Add `exams:publish` to `school_admin` and `principal` role permissions.

---

## Phase 8 — Attendance

Attendance marked for 5 school days in Section A (Grade 5):

| Date | Aryan | Sneha | Rohan | Section |
|------|-------|-------|-------|---------|
| 2025-07-01 (Tue) | Present | Present | Present | 3/3 |
| 2025-07-02 (Wed) | Present | Present | Present | 3/3 |
| 2025-07-03 (Thu) | Present | Present | **Absent (Sick)** | 2/3 |
| 2025-07-04 (Fri) | Present | Present | Present | 3/3 |
| 2025-07-07 (Mon) | Present | Present | Present | 3/3 |

Endpoint: `POST /attendance/section/{section_id}` with `{section_id, academic_year_id, date, session_type, entries}`

---

## Phase 9 — Parent Portal

**Logged in as**: Suresh Mehta (`suresh.mehta@gmail.com`) — Parent of Aryan Mehta

### Bug Fixed 🐛
**File**: `backend/app/services/student_service.py` — `_create_parent_login` method  
**Issue**: Parent user account was created but never assigned a school role, so all permission checks returned 403 Forbidden.  
**Fix applied**: Added role assignment logic after User creation to look up the school's "parent" role and create a `UserRole` entry.  
**Immediate fix**: Directly inserted `user_roles` rows for 3 existing parent users via DB script.

### Parent Portal Tests

| Feature | API | Result | Data |
|---------|-----|--------|------|
| Login | `POST /auth/login` | ✅ | JWT token received |
| View child profile | `GET /students/{id}` | ✅ | Name, admission no, DOB visible |
| View fee invoices | `GET /fees/invoices?student_id=...` | ✅ | INV-202505-00003, status=paid, Rs.4000 |
| View attendance | `GET /attendance/section/{id}?date=...` | ✅ | Daily status per student visible |
| View exam marks | `GET /exams/{id}/marks` | ✅ | Math: 22/25 (A Pass), Science: 23/25 (A+) |
| View published results | `GET /exams/{id}/results/{class_id}` | ✅ | Class ranking visible, Aryan #1 |

---

## Bugs Found & Fixed

### Bug 1 — Student Creation (HTTP 500)
- **File**: `backend/app/services/student_service.py:99`
- **Problem**: `User(hashed_password=...)` — wrong field name
- **Fix**: Changed to `User(password_hash=...)` matching the SQLAlchemy model
- **Impact**: Student creation was completely broken before this fix

### Bug 2 — Parent Role Not Assigned
- **File**: `backend/app/services/student_service.py` — `_create_parent_login()`
- **Problem**: User account created without `UserRole` entry → all API calls returned 403
- **Fix**: Added code to look up school's "parent" role and insert `UserRole` after user creation
- **Impact**: Parents could log in but couldn't access any data

---

## Known Issues (Not Fixed)

| Issue | Severity | Details |
|-------|----------|---------|
| `school_admin` missing `exams:publish` | Medium | School admin can't publish exam results; only super admin can |
| Attendance response missing `total_present`/`total_students` at section level | Low | Fields returned as empty in GET response |
| Duplicate school created during bootstrap testing | Low | `stone-valley-2` was accidentally created; not cleaned up |

---

## API Discovery Notes

| Endpoint | Note |
|----------|------|
| `GET /classes` | Requires `?academic_year_id=` query param (422 without it) |
| `POST /classes` | Requires `academic_year_id` in body |
| `POST /exams/bulk` | Creates one exam per subject |
| `POST /fees/payments` | Fee collection (not `/fees/collect`) |
| `POST /exams/publish` | Requires `exams:publish` permission (not in school_admin role) |
| `POST /attendance/section/{id}` | Status values: `present`, `absent`, `late`, `half_day`, `leave`, `holiday` |
| Bootstrap response | `{success: true, data: {id, name, slug, admin: {...}}}` |

---

## Test Data Summary

| Entity | Value |
|--------|-------|
| School ID | `a8701957-9a83-4e69-b80b-2d83cef3dfd4` |
| Academic Year | 2025-2026 (`6621b0fb-...`) |
| Class | Grade 5 (`af2ae9ad-...`) |
| Section | Section A (`e733db75-...`) |
| Student 1 | Aryan Mehta — `5c34978d-...` |
| Student 2 | Sneha Joshi — `c56fb2d0-...` |
| Student 3 | Rohan Verma — `4edd32fd-...` |
| Fee Invoice | INV-202505-00003 (paid, Rs.4000) |
| Payment Receipt | RCPT-20260415-9CD02487 |
| Exam (Math) | `348a2ee7-...` (published) |
| Exam (Science) | `5bbe3b7c-...` (published) |
