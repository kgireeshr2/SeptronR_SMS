# featurePrompts — How to Use This Folder

## Overview

This folder contains **33 self-contained feature implementation prompts** plus this guide.
Each prompt is a complete AI coding instruction covering DB models, API, and frontend for one feature.

The prompts are grouped into **4 sequential rounds**. All prompts inside a round may be executed
in parallel (by separate agents or composer runs), but a round must be fully complete before
starting the next.

---

## Round Sequence

| Round | Folder | Prompts | Theme | Prerequisite |
|-------|--------|---------|-------|-------------|
| 1 | `Round1_Foundation/` | 01–07 | Infrastructure, Auth, RBAC, Core Setup | None |
| 2 | `Round2_Core_Operations/` | 08–13 | People management, daily operations | Round 1 done |
| 3 | `Round3_Academic_Financial/` | 14–20 | Academic modules + financial | Round 2 done |
| 4 | `Round4_Advanced_Features/` | 21–33 | Communications, portals, admin tools, deployment | Round 3 done |

---

## Prompt List

### Round 1 — Foundation
- `01_Infrastructure_Setup.md` — Docker, FastAPI app, Alembic, Redis, Celery, React/Vite scaffold
- `02_Authentication_JWT.md` — Login, refresh, OTP, forgot/reset password, JWT blacklist
- `03_Roles_Permissions_RBAC.md` — 14 built-in roles, 27-module permission matrix, RBAC UI
- `04_School_Profile_Settings.md` — Schools model, key-value settings store, logo upload
- `05_Academic_Year_Terms.md` — Academic years, terms, set-current, lock-year, navbar selector
- `06_Classes_Sections_Subjects.md` — Classes, sections, subjects, class-subject assignments
- `07_Timetable.md` — Timetable model, conflict detection, drag-drop grid UI, PDF export

### Round 2 — Core Operations
- `08_Online_Admissions.md` — Public form, configurable fields, kanban admin view, auto-create student
- `09_Student_Management.md` — Student profiles, enrollment, promotion, TC, bulk import, ID cards
- `10_Staff_Management.md` — Staff profiles, departments, designations, employee ID, staff portal
- `11_Leave_Management.md` — Leave types, allocations, apply→approve workflow, balance tracker
- `12_Student_Attendance.md` — Session-based marking, absent SMS, monthly sheet PDF, low-attendance
- `13_Staff_Attendance_Holidays.md` — Manual/biometric/QR checkin, holiday model, Celery notifications

### Round 3 — Academic & Financial
- `14_Fee_Management.md` — Fee structures, discounts, invoices, payments, Razorpay hookpoint
- `15_Payroll.md` — Monthly payroll, allowances/deductions, bulk approve, payslip PDF
- `16_Exam_Management.md` — Exam schedule, marks entry, grading scale, report cards, admit cards
- `17_Library_Management.md` — Book catalog, issue/return with fine calc, overdue alerts
- `18_Transport_Management.md` — Vehicles, routes, stops, student assignment, maintenance log
- `19_Inventory_Management.md` — Items, stock in/out, PO workflow, low-stock alerts
- `20_Accounting.md` — Income/expense records, budget heads, fee-income auto-sync, P&L charts

### Round 4 — Advanced Features
- `21_Communication_Notifications.md` — 5-channel engine, WebSocket bell, bulk broadcast
- `22_Homework_Lesson_Plans.md` — Teacher assigns, student submits, grading, lesson plans
- `23_PTM_Scheduling.md` — PTM events, auto slot generation, parent booking, confirmations
- `24_Calendar.md` — FullCalendar integration, event types, iCal export
- `25_Document_Templates.md` — 11 template types, Jinja2 render, WeasyPrint bulk PDF
- `26_Reports_Module.md` — 22 report types, BaseReport registry, async PDF/Excel generation
- `27_Audit_Logs.md` — Auto-capture middleware, log_audit helper, diff view, Excel export
- `28_Dashboard.md` — Role-adaptive KPIs, 10 Recharts widgets, Redis 2-min cache
- `29_Super_Admin.md` — School CRUD, subscriptions, feature flags, impersonation
- `30_Settings_Page.md` — Full 9-tab settings UI, test-connection buttons
- `31_Parent_Portal_PWA.md` — Mobile-first PWA, multi-child, FCM, offline support
- `32_Testing_Security.md` — pytest fixtures, tenant isolation, rate limiting, Locust
- `33_Deployment.md` — Docker Compose prod, Nginx SSL, GitHub Actions CI/CD

---

## Global Coding Standards (applies to ALL prompts)

### Backend
- **Pattern**: Routes → Service → Repository → SQLAlchemy Model
- **Response envelope**: `{"success": true, "data": ..., "message": "...", "pagination": null | {...}}`
- **HTTP codes**: 200 OK · 201 Created · 400 Bad Request · 401 Unauthorized · 403 Forbidden · 404 Not Found · 422 Validation · 500 Error
- **All routes** protected with `permission_required(module, action)` dependency
- **All mutating operations** call `log_audit(db, user, module, action, record_id, old, new)`
- **Soft delete**: `is_active=False` + `deleted_at` (UTC) + `deleted_by (user_id)` — never hard delete; all list queries `WHERE is_active = TRUE`
- **Datetime**: all stored as UTC (`TIMESTAMPTZ`)
- **Money**: all amounts stored as `INTEGER` paise/cents (×100), displayed as decimal
- **Pagination**: all list endpoints accept `?page=1&page_size=20` and return `{total, page, page_size, pages}` in `pagination`
- **N+1 prevention**: use `selectinload()` for collections, `joinedload()` for FK relationships
- **Naming**: snake_case Python, camelCase JSON (FastAPI response_model handles conversion)

### Frontend
- **API calls**: only in `frontend/src/api/*.ts` — never inline in components
- **Hooks**: wrap every API call in a custom TanStack Query hook
- **Forms**: all forms use React Hook Form + Zod schema validation
- **Loading states**: every data-fetching component uses `LoadingSkeleton`
- **Error handling**: global error boundary + per-action toast notifications
- **Permissions**: gate every action button with `<PermissionGuard module="x" action="y">`
- **TypeScript**: no `any` types
- **Page layout**: PageHeader (title + breadcrumb + action buttons) → filter bar → content → pagination

---

## How to Use Each Prompt

1. Open the prompt file for the feature you want to implement
2. Paste the entire prompt into your AI coding assistant
3. The AI will implement exactly what is specified
4. Run the Verification Checklist at the bottom of each prompt to confirm completion
5. Commit before moving to the next prompt

> **Important**: Prompts within the same round can be implemented in parallel by different
> developers or agent sessions. Prompts in later rounds depend on exact model/field names
> established in prior rounds — do not rename models or tables without updating dependents.

---

## Tech Stack Reference

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI 0.111, SQLAlchemy 2.0 async, Alembic |
| Database | PostgreSQL 15 |
| Cache/Queue | Redis 7, Celery 5 |
| Auth | JWT (HS256), access 15min + refresh 7d (httpOnly cookie) |
| PDF | WeasyPrint + Jinja2 |
| Notifications | SMS (MSG91/Twilio), WhatsApp (Meta Cloud API), Email (SMTP), FCM Push, WebSocket |
| Frontend | React 18, TypeScript, Vite, TanStack Query v5, Zustand, shadcn/ui, Tailwind CSS v3 |
| Charts | Recharts |
| Calendar | FullCalendar.io |
| Forms | React Hook Form + Zod |
| Tables | TanStack Table v8 |
| Containerization | Docker + Docker Compose |
