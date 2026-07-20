================================================================================
PROJECT: SCHOOL MANAGEMENT SYSTEM (SMS/ERP)
STACK: Python (FastAPI) · PostgreSQL · Redis · Celery | React (TypeScript) · Tailwind CSS
================================================================================

You are an expert full-stack software engineer. Build a production-grade, 
multi-tenant School Management System (SMS) step by step. Follow each phase 
completely before moving to the next. Write clean, modular, documented code.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 0 — TECHNOLOGY STACK & ARCHITECTURE DECISIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BACKEND (Python API Service):
  - Framework    : FastAPI (async, OpenAPI auto-docs)
  - ORM          : SQLAlchemy 2.x (async) + Alembic for migrations
  - Database     : PostgreSQL 15+
  - Cache/Queue  : Redis 7 + Celery 5 (background tasks, notifications, reports)
  - Auth         : JWT (access + refresh tokens), OAuth2 Password Bearer
  - File Storage : Local filesystem in dev; AWS S3 / MinIO in production
  - PDF Engine   : WeasyPrint + Jinja2 HTML templates for ID cards, admit cards,
                   fee receipts, report cards
  - SMS          : Twilio / MSG91
  - WhatsApp     : Meta Cloud API / Twilio WhatsApp
  - Email        : SMTP (smtplib) / SendGrid via Celery tasks
  - Push Notif   : Firebase Cloud Messaging (FCM)
  - WebSocket    : FastAPI WebSocket for real-time in-app notifications
  - Validation   : Pydantic v2 schemas
  - Testing      : pytest + pytest-asyncio + httpx
  - Containerize : Docker + Docker Compose

FRONTEND (React SPA):
  - Framework    : React 18 + TypeScript
  - Routing      : React Router v6
  - State/Cache  : TanStack Query (React Query) v5
  - Global State : Zustand
  - UI Library   : shadcn/ui + Tailwind CSS v3
  - Charts       : Recharts
  - Calendar     : FullCalendar.io (React)
  - Forms        : React Hook Form + Zod validation
  - Tables       : TanStack Table v8
  - Print/PDF    : react-to-print + html2canvas
  - Drag & Drop  : dnd-kit (for template builder)
  - Rich Text    : TipTap editor (for notices/communication)
  - Icons        : Lucide React
  - Date         : date-fns
  - Real-time    : Socket.io-client / native WebSocket

PROJECT STRUCTURE:
  /backend
    /app
      /api          → route handlers organized by module (all routes prefixed /api/v1/)
      /core          → config, security, dependencies
      /models        → SQLAlchemy ORM models
      /schemas       → Pydantic request/response schemas
      /services      → business logic layer
      /repositories  → database query layer
      /tasks         → Celery async tasks
      /templates     → Jinja2 HTML templates for PDF
      /utils         → helpers, file upload, pagination
    alembic/         → migrations
    tests/
    main.py
    Dockerfile
  /frontend
    /src
      /api           → Axios instances & API call functions per module
      /components    → reusable UI components
      /pages         → page-level components per module
      /hooks         → custom React hooks
      /store         → Zustand global stores
      /types         → TypeScript interfaces per module
      /utils         → formatters, validators, constants
      /routes        → route definitions with guards
  docker-compose.yml


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 1 — PROJECT SETUP & INFRASTRUCTURE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1.1 Backend Bootstrap
  - Create FastAPI app with lifespan context manager
  - Configure .env with Pydantic BaseSettings (DATABASE_URL, SECRET_KEY, 
    REDIS_URL, AWS credentials, FCM key, SMS keys, WhatsApp tokens, etc.)
  - Set up async PostgreSQL engine + session factory
  - Configure Alembic for database migrations
  - Add CORS middleware, GZip middleware, request logging middleware
  - Global exception handlers (HTTPException, ValidationError, 500 fallback)
  - Health check endpoint GET /health (DB ping, Redis ping)
  - All API routes prefixed /api/v1/ — enables versioning and zero-downtime upgrades later
  - Docker Compose: postgres, redis, backend, celery-worker, celery-beat, 
    frontend, nginx

1.2 Frontend Bootstrap
  - Vite + React + TypeScript scaffold
  - Configure absolute imports with tsconfig paths
  - Set up Tailwind CSS + shadcn/ui init
  - Configure Axios base instance with JWT interceptor (auto-attach token, 
    auto-refresh on 401)
  - Set up TanStack Query with global error handling
  - Create persistent auth store with Zustand (accessToken, refreshToken, 
    currentUser, schoolInfo)
  - Route guard: PrivateRoute wrapper that redirects unauthenticated users

1.3 Multi-School / Multi-Tenant Design
  - Each school has a UUID-based school_id
  - All major tables include school_id foreign key
  - Middleware extracts school context from subdomain or auth token
  - Super admin can manage all schools; school admin scoped to their school


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 2 — AUTHENTICATION, ROLES & PERMISSIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

2.1 Authentication Module
  Backend:
  - POST /auth/login           → verify credentials → return access + refresh JWT
  - POST /auth/refresh         → rotate refresh token → return new access token
  - POST /auth/logout          → blacklist refresh token in Redis
  - POST /auth/forgot-password → send reset link via email (Celery task)
  - POST /auth/reset-password  → validate token → update hashed password
  - POST /auth/change-password → authenticated user changes own password
  - POST /auth/send-otp        → send 6-digit OTP to phone via SMS (rate limited: 1/min)
  - POST /auth/verify-otp      → validate OTP → return access + refresh JWT (phone-based login
                                  used by parents who prefer phone over username/password)
  - GET  /auth/me              → return current user profile + permissions

  Models:
  - users (id, school_id, username, email, phone, password_hash,
           is_active, is_verified, avatar_url, last_login,
           otp_secret, created_at, updated_at)
           [NOTE: roles linked via user_roles many-to-many — no role_id column here]
  - password_reset_tokens (id, user_id, token_hash, expires_at, used_at)
  - token_blacklist (id, jti, expires_at) — stored in Redis

  Frontend:
  - Login page with form validation, show/hide password
  - Forgot password flow (email → OTP or link → reset form)
  - Auto-redirect after login based on role (admin → /dashboard, 
    teacher → /teacher/dashboard, student → /student/portal, parent → /parent/portal)

2.2 Role Management
  Built-in roles (non-deletable):
  - Super Admin, School Admin, Principal, Vice Principal, Teacher, 
    Class Teacher, Accountant, Librarian, Transport Manager, 
    Inventory Manager, Receptionist, Parent, Student, Guest

  Models:
  - roles (id, school_id, name, slug, description, is_system, is_active)
  - permissions (id, module, action, description)
    Actions: view, create, update, delete, export, approve, manage
    Modules: one per system module
  - role_permissions (role_id, permission_id)
  - user_roles (user_id, role_id) — support multiple roles per user

  API Endpoints:
  - CRUD /roles
  - GET/POST /roles/{id}/permissions
  - GET /permissions (full permission registry)

2.3 Permission Manager UI
  Frontend page /admin/roles:
  - Table of roles with Edit / Clone / Delete actions
  - Permission matrix: rows = modules, columns = actions (checkboxes)
  - Toggle All per row, Toggle All per column
  - Save changes with optimistic updates
  - Role assignment modal on user edit page
  - usePermission() hook: hasPermission('students', 'create')
  - Conditionally render UI elements based on permissions
  - Backend: permission_required dependency decorator for all protected routes


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 3 — ACADEMIC YEAR / SESSION & SCHOOL SETTINGS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

3.1 Academic Year / Session
  Models:
  - academic_years (id, school_id, name e.g. "2025-2026", start_date, end_date,
                    is_current, is_locked, created_at)
  - academic_terms (id, school_id, academic_year_id, name e.g. "Term 1", start_date,
                    end_date, is_current)

  Features:
  - Create, update, delete academic years
  - Set current academic year (only one can be active at a time)
  - Lock completed years to prevent edits
  - Promotion utility: bulk promote students from one year to next
  - All modules filter data by school_id + academic_year_id
  - Term/semester management within each year

  Frontend:
  - Academic Year selector in top navbar (persisted in Zustand)
  - All module pages respect the selected academic year context

3.2 Online Admissions
  Models:
  - admission_forms (id, school_id, academic_year_id, applicant_name,
                     date_of_birth, gender, applying_for_class_id,
                     parent_name, parent_phone, parent_email,
                     address, previous_school, documents JSON,
                     status [draft/submitted/under_review/approved/
                             rejected/waitlisted],
                     assigned_admission_number, submitted_at,
                     reviewed_by, reviewed_at, remarks, created_at)
  - admission_form_configs (id, school_id, academic_year_id,
                             fields_config JSON, required_documents JSON,
                             open_date, close_date, is_active)

  Features:
  - Configurable public admission form (no login required to apply)
  - Admin defines required fields and documents per intake year
  - Applicant uploads documents (photo, birth certificate, marksheet, etc.)
  - Submission triggers acknowledgement email with reference number
  - Admin reviews applications: approve / reject / waitlist with remarks
  - Approved applications auto-create student record + parent portal login
  - Admission form management: open/close registration window per year
  - Application status page for applicants (check by reference number)
  - Bulk approve with class/section assignment
  - Excel export of all applications with filter by status

  Frontend:
  - Public-facing admission form page (no auth, accessible via school URL)
  - Admin /admissions page: kanban or table view by status
  - Review modal: view all application details + approve/reject action
  - Application tracker widget on admin dashboard


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 4 — CLASS & SECTION MANAGEMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Models:
  - classes (id, school_id, name e.g. "Grade 1", numeric_level, 
             academic_year_id, is_active)
  - sections (id, class_id, name e.g. "A", "B", "Rose", capacity,
              class_teacher_id → FK users, room_number, is_active)
  - subjects (id, school_id, name, code, is_elective,
              full_marks, pass_marks)
              [NOTE: subjects are school-level; linked to classes via class_subjects]
  - class_subjects (class_id, subject_id, teacher_id)
  - timetable (id, school_id, section_id, subject_id, teacher_id, day_of_week,
               period_number, start_time, end_time, academic_year_id)

Features:
  - Dynamically add classes and sections per academic year
  - Assign class teacher to section
  - Assign subjects and subject teachers per class
  - Visual timetable builder: drag-and-drop grid (day × period)
  - Print/export timetable as PDF
  - Room/teacher conflict detection

Frontend /admin/classes:
  - Class list with expandable section rows
  - Timetable grid view per section
  - Subject assignment matrix per class
  - Bulk import via CSV upload


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 5 — STUDENT MANAGEMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Models:
  - students (id, school_id, admission_number [auto-generated, UNIQUE per school],
              user_id → FK, first_name, last_name,
              date_of_birth, gender, blood_group, religion, category,
              nationality, photo_url, admission_date, is_active,
              created_at, updated_at)
              [NOTE: class/section/year stored in student_enrollments, not here]
  - student_enrollments (id, student_id, academic_year_id, class_id, section_id,
                         roll_number, is_current, created_at)
                         [UNIQUE on (student_id, academic_year_id)]
  - student_parents (id, student_id, relation e.g. Father/Mother/Guardian, 
                     user_id → FK users, name, phone, email, occupation,
                     address, is_primary_contact, can_access_portal)
  - student_documents (id, student_id, doc_type, file_url, uploaded_at)
  - student_promotions (id, student_id, from_class, to_class, 
                        from_year, to_year, promoted_by, promoted_at)
  - student_transfers (id, student_id, transfer_certificate_no, 
                       leaving_date, reason, issued_by)

Features:
  - Full student registration form with photo upload
  - Auto-generate admission number (configurable format per school: 
    e.g., SCH-2025-0001)
  - Assign to class + section + roll number
  - Parent/guardian profile linked to student (multiple parents)
  - Parent portal login creation on student registration
  - Document management: upload Birth Certificate, Aadhaar, Previous Marksheet, etc.
  - Student search with advanced filters (class, section, gender, category, status)
  - Bulk import students via Excel/CSV template
  - Bulk export to Excel/PDF
  - Student promotion at year-end (bulk or individual)
  - Transfer Certificate generation with PDF template
  - Student ID card generation (batch)
  - Student profile page: all tabs (Personal, Academic, Attendance, 
    Fees, Exams, Documents, Timeline)

Student Portal (role: Student):
  - Read own profile, timetable, attendance, results, fee status, 
    homework, notices


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 6 — STAFF MANAGEMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Models:
  - staff (id, school_id, employee_id [auto-generated], user_id → FK,
           first_name, last_name, date_of_birth, gender, photo_url,
           department, designation, date_of_joining, employment_type 
           [permanent/contract/part-time], is_active, salary_type,
           monthly_salary, bank_account_no, bank_name, ifsc_code,
           address, emergency_contact, qualifications JSON, 
           experience_years, created_at)
  - staff_documents (id, staff_id, doc_type, file_url)
  - staff_leaves (id, staff_id, leave_type, from_date, to_date, 
                  reason, status [pending/approved/rejected], 
                  approved_by, remarks)
  - leave_types (id, school_id, name, max_days_per_year, is_paid)
  - staff_payroll (id, staff_id, academic_year_id, month, year, basic_salary,
                   allowances JSON, deductions JSON, net_salary,
                   payment_date, payment_method, is_paid, receipt_url)
                   [UNIQUE on (staff_id, month, year)]

Features:
  - Full staff profile with photo, qualifications, experience
  - Department and designation management (CRUD)
  - Assign roles and class/subject allocations
  - Leave management: apply → HOD/Principal approve workflow
  - Leave balance tracker (annual, sick, casual)
  - Salary/payroll processing per month with auto-calculation:
    (basic + HRA + DA + other allowances) − (PF + ESI + TDS + other deductions)
  - Payslip PDF generation per staff
  - Bulk salary payment mark as paid
  - Staff ID card generation
  - Staff attendance (links to Phase 7)

Staff Portal:
  - View profile, timetable, apply leave, view payslip, mark attendance


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 7 — ATTENDANCE MANAGEMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Models:
  - attendance_sessions (id, school_id, session_type [morning/afternoon],
                         date, class_id, section_id, taken_by, 
                         is_finalized, created_at)
  - student_attendance (id, school_id, session_id, student_id, status
                        [present/absent/late/half-day/holiday/leave],
                        remarks, notified_at)
  - staff_attendance (id, staff_id, date, check_in, check_out, 
                      status, remarks, source [manual/biometric/qr])
  - holidays (id, school_id, name, date, academic_year_id, holiday_type)

Features:
  STUDENT ATTENDANCE:
  - Class teacher marks attendance per section per day
  - Bulk mark all present, then deselect absents (efficient UI)
  - Absent students auto-trigger SMS/WhatsApp notification to parents 
    (Celery task with rate limiting)
  - Attendance status: Present / Absent / Late / Leave / Holiday
  - Date-wise, month-wise, student-wise attendance reports
  - Monthly attendance summary per class/section
  - Attendance percentage auto-calculated per student
  - Warning alert when student attendance < configurable threshold (e.g. 75%)
  - Holiday management: skip attendance on marked holidays

  STAFF ATTENDANCE:
  - Manual entry or biometric device integration (import CSV from device)
  - QR code based check-in (generate staff QR → scan → record)
  - Monthly report with total working days, present, absent, late counts
  - Integration with leave module (approved leaves marked automatically)

  FRONTEND:
  - Attendance table with color-coded rows (green/red/yellow)
  - Calendar heatmap view per student (months × days grid)
  - Bulk attendance page for class teacher
  - Report filterable by class, section, date range, student
  - Export to Excel/PDF


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 8 — FEE MANAGEMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Models:
  - fee_categories (id, school_id, name e.g. "Tuition Fee", "Transport Fee",
                    description, is_active)
  - fee_structures (id, school_id, academic_year_id, class_id, 
                    fee_category_id, amount, frequency 
                    [monthly/quarterly/annual/one-time], due_day)
  - fee_discounts (id, school_id, name, type [percentage/fixed], value,
                   applicable_to [student/category/class])
  - student_fee_assignments (id, student_id, fee_structure_id, 
                              discount_id, custom_amount, academic_year_id)
  - fee_invoices (id, school_id, student_id, invoice_number, 
                  academic_year_id, invoice_date, due_date, 
                  status [unpaid/partial/paid/overdue/waived], total_amount,
                  paid_amount, balance_amount)
  - fee_invoice_items (id, invoice_id, fee_category_id, amount, discount_amt, fine_applied)
  - fee_payments (id, invoice_id, amount, payment_date,
                  payment_method [cash/cheque/online/card],
                  transaction_id, receipt_number, collected_by, remarks)
                  [NOTE: student derived from invoice → fee_invoices.student_id; no denorm here]
  - fine_configurations (id, school_id, name, type [fixed/percentage_per_day], 
                          value, applicable_after_days)

Features:
  - Configure fee structures per class per academic year
  - Assign fee structures to students with optional discounts/waivers
  - Auto-generate monthly/term invoices via Celery scheduled task
  - Collect payments: record full or partial payments
  - Auto-calculate fines for late payments
  - Fee receipt PDF auto-generated on payment (Jinja2 template)
  - Receipt emailed/WhatsApp-sent to parent (Celery task)
  - Dashboard: total fees expected vs collected vs outstanding
  - Due fees reminder: auto-send SMS/WhatsApp N days before due date
  - Fee defaulters list with bulk notification
  - Concession/scholarship management
  - Sibling discount configuration
  - Day-wise, class-wise, student-wise fee reports
  - Export to Excel/PDF
  - Online payment gateway integration hookpoint (Razorpay/Stripe/PayPal)

Parent Portal Fee View:
  - All invoices, payment history, download receipts


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 9 — EXAM MANAGEMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Models:
  - exam_types (id, school_id, name e.g. "Unit Test 1", "Mid-Term", 
                "Final Exam", academic_year_id, term_id, weight_percentage)
  - exams (id, school_id, exam_type_id, class_id, subject_id, 
           exam_date, start_time, end_time, total_marks, pass_marks, 
           venue, invigilator_id, is_published, academic_year_id)
  - admit_card_configs (id, exam_type_id, instructions, footer_text,
                        logo_url, signature_url)
  - student_marks (id, exam_id, student_id, marks_obtained, 
                   grade, is_absent, remarks, entered_by, entered_at,
                   is_verified)
  - grading_scales (id, school_id, name, ranges JSON 
                    e.g. [{min:90,max:100,grade:"A+",gpa:10.0}])
  - report_card_templates (id, school_id, template_html, layout_config JSON)

Features:
  - Create exam schedule per exam type per class
  - Exam timetable view: class-wise, date-wise
  - Admit card generation: batch PDF with student photo, roll no, 
    exam schedule, instructions per student
  - Marks entry portal for teachers (subject-wise, editable grid)
  - Marks verification workflow (teacher enters → admin verifies)
  - Auto-calculate total, average, percentage, rank, grade per student
  - Grade computation based on configurable grading scale
  - Class rank and section rank calculation
  - Report card (marksheet) PDF generation per student 
    (Jinja2 template, fully customizable layout)
  - Batch report card generation for entire class
  - Result publish/unpublish toggle (students see results only when published)
  - Comparative analysis charts: class average per subject, 
    top performers, subject-wise performance distribution
  - Pass/Fail determination with configurable rules 
    (must pass all subjects, or aggregate %, etc.)
  - Result SMS notification to parents on publish


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 10 — TRANSPORT MANAGEMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Models:
  - vehicles (id, school_id, vehicle_number, vehicle_type, model, 
              capacity, insurance_expiry, fitness_expiry, 
              pollution_expiry, driver_id, conductor_id, is_active)
  - routes (id, school_id, route_name, start_point, end_point, 
            total_km, vehicle_id, is_active)
  - stops (id, school_id, route_id, stop_name, stop_order, pickup_time,
           drop_time, latitude, longitude)
  - student_transport (id, student_id, route_id, stop_id, 
                       academic_year_id, fee_amount, is_active)
  - vehicle_maintenance (id, vehicle_id, maintenance_type, date, 
                         cost, description, next_due_date)
  - vehicle_fuel_log (id, vehicle_id, date, fuel_type, 
                      litres, cost_per_litre, odometer_reading, filled_by)

Features:
  - Vehicle fleet management with document expiry alerts
  - Route and stop management with km tracking
  - Assign students to routes/stops
  - Transport fee linked to fee module per route
  - Driver/conductor profile linked to staff
  - Vehicle maintenance log with upcoming service reminders
  - Fuel consumption tracking
  - Route-wise student list for driver (printable)
  - GPS tracking hookpoint (integrate with third-party GPS API)
  - Vehicle document expiry alert (insurance, fitness, PUC)
  - Daily vehicle log report


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 11 — INVENTORY MANAGEMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Models:
  - inventory_categories (id, school_id, name, description)
  - items (id, school_id, category_id, item_name, item_code, unit,
           minimum_stock_level, description, is_active)
  - stores (id, school_id, store_name, location, in_charge_id)
  - stock_entries (id, item_id, store_id, quantity, unit_price, 
                   total_price, entry_type [purchase/return/adjustment],
                   supplier, invoice_number, entry_date, entered_by)
  - stock_issues (id, item_id, store_id, issued_to_user_id, 
                  issued_to_dept, quantity, purpose, issued_date,
                  issued_by, return_date, is_returned)
  - suppliers (id, school_id, name, contact_person, phone, email, address)
  - purchase_orders (id, school_id, supplier_id, order_date, 
                     expected_delivery, status, total_amount, notes)
  - purchase_order_items (id, po_id, item_id, quantity, unit_price)

Features:
  - Item catalog with categories (stationery, lab equipment, 
    sports gear, furniture, electronics, etc.)
  - Stock-in: record purchases with supplier invoice
  - Stock-out: issue items to departments/staff/students
  - Real-time stock balance per item
  - Low stock alerts (Celery periodic task → notification)
  - Purchase order creation and supplier management
  - Stock valuation report (FIFO / Weighted Average)
  - Item-wise ledger (all transactions for an item)
  - Export stock register to Excel


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 12 — INCOME & EXPENSE (ACCOUNTING)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Models:
  - income_categories (id, school_id, name, description)
  - expense_categories (id, school_id, name, budget_amount, description)
  - income_records (id, school_id, category_id, amount, source, 
                    payment_method, reference_number, income_date,
                    academic_year_id, recorded_by, attachment_url, notes)
  - expense_records (id, school_id, category_id, amount, payee,
                     payment_method, reference_number, expense_date,
                     academic_year_id, approved_by, attachment_url, notes)
  - budget_heads (id, school_id, academic_year_id, category_id, 
                  type [income/expense], budgeted_amount)

Features:
  - Record non-fee income (donations, grants, canteen, etc.)
  - Record expenses by category (salary, utilities, maintenance, etc.)
  - Fee collection auto-reflects in income (linked to fee module)
  - Staff salary payment auto-reflects in expenses (linked to payroll)
  - Budget vs Actual comparison per category
  - Monthly / annual income-expense summary
  - Profit/Loss statement
  - Cash book: day-wise transaction ledger
  - Attach receipts/invoices as file uploads
  - Charts: income vs expense trend (bar/line), 
    expense pie chart by category
  - Export to Excel / PDF (accounting reports)


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 13 — LIBRARY MANAGEMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Models:
  - book_categories (id, school_id, name)
  - books (id, school_id, title, author, publisher, isbn, 
           category_id, edition, language, total_copies,
           shelf_location, cover_url, description,
           [NOTE: available_copies is computed = total_copies − active_issues; do NOT store as column]
           purchase_date, purchase_price)
  - library_members (id, school_id, member_id [auto], user_id,
                     member_type [student/staff], card_expiry,
                     max_books_allowed, is_active)
  - book_issues (id, school_id, book_id, member_id, issue_date, due_date,
                 return_date, fine_amount, fine_paid, issued_by,
                 status [issued/returned/overdue/lost])
  - library_fines (id, issue_id, amount, reason, is_paid, paid_date)

Features:
  - Book catalog with ISBN auto-lookup (Open Library API integration)
  - Multiple copies per book with individual tracking
  - Barcode/QR code generation per book copy
  - Library card management for students and staff
  - Issue book (check out) with configurable due period per member type
  - Return book with automatic fine calculation for overdue
  - Reserve/request book (if all copies issued)
  - Overdue notifications via SMS/WhatsApp (Celery)
  - Book search: title, author, ISBN, category, availability
  - Library reports: most borrowed books, overdue list, 
    member-wise issue history, stock register
  - Digital library hookpoint: link eBook URLs to book records


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 14 — COMMUNICATION & NOTIFICATIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Models:
  - notification_templates (id, school_id, name,
                             event_trigger ENUM [
                               STUDENT_ABSENT, FEE_DUE, FEE_PAID, FEE_OVERDUE,
                               RESULT_PUBLISHED, EXAM_SCHEDULED, HOMEWORK_ASSIGNED,
                               LEAVE_APPROVED, LEAVE_REJECTED, LIBRARY_OVERDUE,
                               LOW_ATTENDANCE_WARNING, ADMISSION_APPROVED,
                               TRANSPORT_DELAY, ANNOUNCEMENT_PUBLISHED, CUSTOM
                             ],
                             channels JSON [sms,whatsapp,email,push,in_app],
                             subject, body [supports {variable} placeholders],
                             is_active)
  - notifications (id, school_id, recipient_user_id, type, title, 
                   body, data JSON, is_read, read_at, 
                   created_at, channel)
  - bulk_messages (id, school_id, title, body, audience_filter JSON,
                   channels JSON, scheduled_at, sent_at, 
                   total_recipients, sent_count, failed_count,
                   status, created_by)
  - message_logs (id, bulk_message_id, recipient_id, channel, 
                  status [sent/failed/pending], provider_message_id,
                  sent_at, error_message)
  - announcements (id, school_id, title, body_html, target_audience,
                   publish_date, expiry_date, is_pinned, created_by)

Channels Implemented:
  1. In-App Notifications (WebSocket real-time + bell icon with count)
  2. Push Notifications (Firebase FCM — web & mobile)
  3. Email (SMTP/SendGrid via Celery)
  4. SMS (Twilio/MSG91 via Celery)
  5. WhatsApp (Meta Cloud API template messages via Celery)

Features:
  - Notification template builder with variable substitution 
    ({student_name}, {class}, {amount}, {date}, etc.)
  - Configure which events trigger which channels:
    e.g. Absent → SMS + WhatsApp to parent
         Fee due → Email + WhatsApp
         New result → Push + in-app
  - Compose and send bulk messages with audience filters:
    Target by: All, All Students, All Parents, Specific Class, 
    Specific Section, All Staff, Specific Department, Custom list
  - Schedule messages for future delivery (Celery beat)
  - Delivery status tracking per recipient per channel
  - Announcement board (notice board) with HTML editor
  - SMS/WhatsApp credit balance display and low-balance alert
  - Users manage notification preferences (opt-out of specific channels)

Frontend:
  - Bell icon in header → dropdown showing recent notifications
  - Mark as read / Mark all as read
  - Notification center page with filters
  - Bulk message composer (rich text + audience selector)
  - Announcement list with pin-to-top support


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 15 — HOMEWORK & LESSON PLANNING (BONUS)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Models:
  - homework (id, school_id, class_id, section_id, subject_id, teacher_id,
              title, description, due_date, attachment_url,
              publish_date, academic_year_id)
  - homework_submissions (id, school_id, homework_id, student_id, content,
                          file_url, submitted_at, marks_given, remarks)
  - lesson_plans (id, school_id, class_id, section_id, subject_id, teacher_id,
                  title, objectives, content, resources, date,
                  academic_year_id)

Features:
  - Teachers assign homework with optional file attachment
  - Students submit homework via portal
  - Teacher grades submissions
  - Lesson plan creation and archive per subject
  - Students/parents receive push notification on new homework


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 15B — PARENT-TEACHER MEETING (PTM) SCHEDULING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Models:
  - ptm_events (id, school_id, academic_year_id, title, date,
                slot_duration_minutes, start_time, end_time,
                class_id, section_id, created_by, is_active)
  - ptm_slots (id, ptm_event_id, teacher_id, slot_start, slot_end,
               is_booked, booked_by_parent_id, student_id, notes)
  - ptm_bookings (id, ptm_slot_id, parent_id, student_id,
                  booking_time, status [booked/cancelled/completed],
                  meeting_notes, created_at)

Features:
  - Admin/class teacher creates PTM event with configurable slots
    (e.g. 10-min slots, 9 AM – 1 PM)
  - Auto-generate time slots per teacher based on event config
  - Parents log in to portal and book one slot per teacher per PTM
  - Booking confirmation sent via SMS/WhatsApp/Email (Celery)
  - Reminder notification 1 day and 2 hours before slot
  - Teacher views their day's schedule (slot-by-slot appointment list)
  - Admin views PTM attendance: booked vs completed
  - Class teacher records brief meeting notes per slot after PTM

  Frontend:
  - Admin: PTM event creation with slot generation wizard
  - Parent portal: slot picker calendar view, book/cancel slot
  - Teacher dashboard: today's PTM schedule list


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 16 — CALENDAR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Models:
  - calendar_events (id, school_id, title, description, 
                     event_type [holiday/exam/meeting/
                     sports/cultural/other],
                     start_datetime, end_datetime, all_day, 
                     audience [all/students/staff/specific_class],
                     color_tag, location, created_by, academic_year_id)

Features:
  - FullCalendar integration: month / week / day / agenda views
  - Event types color-coded (holidays = red, exams = blue, etc.)
  - Admin creates events visible to relevant audience
  - Teachers/parents/students see only their relevant events
  - Exam schedule auto-populates from Exam module
  - Holiday list auto-populates from Attendance module
  - Add to Google Calendar / export as .ics file
  - Upcoming events widget on dashboard


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 17 — ID CARDS, ADMIT CARDS & TEMPLATE BUILDER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Template Types:
  - Student ID Card (front + back)
  - Staff ID Card (front + back)
  - Admit Card (hall ticket)
  - Fee Receipt
  - Report Card / Marksheet
  - Transfer Certificate
  - Bonafide Certificate
  - Character Certificate
  - Payslip

Template Builder (Frontend):
  - Visual drag-and-drop canvas (dnd-kit)
  - Elements: Text block, Image (photo/logo/signature), 
    Data field (dynamic), QR Code, Barcode, Shape, Divider
  - Data field picker: map to real database fields 
    (student.first_name, student.class.name, school.logo_url, etc.)
  - Style controls: font, size, color, alignment, border
  - Canvas size presets: ID card (CR80), A4, A5, custom
  - Preview with real student/staff data
  - Save template per school
  - Batch generation: select students/staff → generate all PDFs → 
    zip download
  - WeasyPrint renders Jinja2 HTML converted from template JSON


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 18 — AUDIT LOGS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Model:
  - audit_logs (id, school_id, user_id, user_name, role, 
                module, action [CREATE/UPDATE/DELETE/VIEW/EXPORT/LOGIN],
                record_id, record_type, old_values JSON, new_values JSON,
                ip_address, user_agent, timestamp)

Implementation:
  - FastAPI middleware auto-captures mutating requests (POST/PUT/PATCH/DELETE)
  - Service layer helper: log_audit(action, module, record, old, new)
  - Capture: login, logout, failed login attempts
  - Capture: permission changes (who gave what access to whom)
  - Capture: bulk operations (promotion, bulk attendance, bulk fee)
  - Capture: settings changes

Frontend /admin/audit-logs:
  - Filterable table: user, module, action, date range
  - Expandable row showing old_values vs new_values diff
  - Export filtered logs to Excel
  - Retention policy: configurable auto-delete after N months (Celery)


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 19 — SETTINGS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Models:
  - school_settings (id, school_id, key, value, category, data_type,
                     is_public, updated_by, updated_at)
  - school_profile (id, school_id, school_name, tagline, address, city,
                    state, country, pincode, phone, email, website,
                    logo_url, favicon_url, established_year, 
                    affiliation_board, affiliation_number,
                    principal_name, principal_signature_url,
                    school_seal_url, timezone, currency, 
                    date_format, academic_start_month)

Settings Categories:
  General:
    - School name, logo, contact info, address
    - Academic year start month, timezone, currency, date format
    
  Admission:
    - Admission number format and prefix
    - Auto-increment start number
    
  Attendance:
    - Working days (select Mon–Sat)
    - Morning/afternoon sessions toggle
    - Low attendance threshold (%)
    - Auto-notify parents: enable/disable per channel
    - Notification delay after attendance (minutes)
    
  Fees:
    - Fine enable/disable, fine per day rate
    - Payment gateway toggle and API keys (Razorpay etc.)
    - Receipt number prefix and format
    - Due date reminder days
    
  Communication:
    - SMS provider (Twilio/MSG91) + API credentials
    - WhatsApp (Meta API credentials, approved templates list)
    - Email (SMTP host, port, user, password)
    - FCM Server Key
    - Default sender name
    
  Library:
    - Max books per student/staff
    - Default loan period (days)
    - Fine per day for overdue
    
  Exam:
    - Grading scale selection
    - Pass percentage (default per subject)
    - Result SMS trigger on/off
    
  Security:
    - Password policy (min length, complexity, expiry)
    - Session timeout (minutes)
    - Max login attempts before lockout
    - Two-factor authentication enable/disable
    
  Integrations:
    - Payment gateway (Razorpay keys, webhook URL)
    - GPS tracking API
    - Biometric device sync
    
  Backup:
    - Scheduled database backup to S3
    - Backup frequency and retention


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 20 — DASHBOARD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

API: GET /dashboard/stats     → all KPI numbers in one call
     GET /dashboard/charts    → chart data by widget type

Widgets (role-adaptive — show only relevant widgets per role):

  KPI CARDS ROW:
  - Total Students | Total Staff | Total Classes | Total Sections
  - Present Today (students %) | Present Today (staff %)
  - Total Fees Collected This Month | Outstanding Fees
  - Total Income | Total Expense | Net Balance

  CHARTS:
  - Student Enrollment Trend: line chart, last 12 months
  - Attendance Overview: bar chart, last 7 days (% students present)
  - Fee Collection: area chart, monthly collected vs expected
  - Income vs Expense: bar chart, monthly comparison
  - Expense Breakdown: pie/donut chart by category
  - Class-wise Student Count: horizontal bar chart
  - Exam Performance: grouped bar chart, average % per subject per class
  - Gender Distribution: donut chart
  - Transport Route Occupancy: bar chart
  - New Admissions: bar chart, monthly

  PANELS:
  - Recent Fee Payments (last 5 with student name, amount, date)
  - Upcoming Events (next 5 from calendar)
  - Pending Leave Requests (for admin/principal)
  - Low Stock Alerts (inventory items below minimum)
  - Overdue Library Books count
  - Today's Birthdays (students + staff)
  - Recent Audit Activity (last 5 actions)
  - Announcements/Notice board (latest 3)
  - Quick Actions: Add Student | Collect Fee | Mark Attendance | 
                   Send Notification

  All charts use Recharts; data cached in Redis (5 min TTL)


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 21 — ADMIN SUPER PANEL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Super Admin (separate from School Admin) manages multiple schools:
  - Schools list: CRUD, enable/disable schools
  - Per-school subscription/plan management
  - Global feature flags per school
  - Impersonate school admin (for support)
  - Platform-wide audit logs
  - Database connection pool stats
  - Celery task queue monitoring (via Flower integration)
  - SMS/Email credit usage across schools
  - Billing and invoice management per school


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 22 — REPORTS MODULE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Centralized Reports Page with categories:
  Academic:
    - Class-wise student count report
    - Attendance register (monthly, class/section-wise)
    - Student attendance summary
    - Staff attendance summary
    - Exam result sheet (class-wise)
    - Student report cards (batch)
    - Admit cards (batch)
  Financial:
    - Fee collection register (date-wise, class-wise)
    - Fee defaulters list
    - Income & expense report
    - Payroll summary
    - Budget vs actual
  Administrative:
    - New admissions report
    - Student strength report
    - Staff list with designations
    - Transport route student list
    - Library issue register
    - Inventory stock register
  Communication:
    - Bulk message delivery report
    - Notification logs

  All reports:
    - Date range filter, module-specific filters
    - Preview in-browser
    - Export to PDF (WeasyPrint) and Excel (openpyxl)
    - Reports generated as async Celery tasks for large datasets
    - Download link sent via notification when ready


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 23 — PARENT PORTAL & MOBILE-FRIENDLY PWA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Parent Portal features (role: Parent):
  - View linked child(ren) profiles
  - Real-time attendance status (today's status + monthly calendar)
  - Fee ledger and online payment (gateway integration)
  - Exam results and report cards download
  - Homework and assignments list
  - Notice board / announcements
  - Timetable view
  - Library status (books issued by child)
  - Transport route and stop information
  - Direct messaging to class teacher
  - Notification preferences management

PWA:
  - Service worker for offline support
  - App manifest for installability
  - Push notification subscription via FCM
  - Responsive design (mobile-first Tailwind breakpoints)


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 24 — TESTING, SECURITY & PERFORMANCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SECURITY:
  - All endpoints require authentication except:
      /health, /auth/login, /auth/forgot-password, /auth/reset-password,
      /auth/send-otp, /auth/verify-otp,
      /api/v1/admissions/apply (public admission form, school-scoped)
  - permission_required(module, action) FastAPI dependency on every route
  - school_id scoped to JWT — no cross-school data leakage possible
  - SQL injection: prevented via SQLAlchemy ORM parameterized queries
  - XSS: Pydantic model validation + React JSX auto-escaping
  - CSRF: SameSite=Strict cookie for refresh token; Bearer token for access
  - Rate limiting: slowapi (100 req/min per IP on login endpoint)
  - File upload validation: MIME-type check, max size (10MB), 
    store outside webroot
  - HTTPS enforced via Nginx reverse proxy config
  - Sensitive fields (passwords, tokens) never returned in responses
  - PII redaction in audit logs (mask phone/email partially)
  - Secrets via environment variables only (no hardcoding)

TESTING:
  - Backend unit tests: service layer functions with mock DB
  - Integration tests: API endpoint tests with test database
  - Auth tests: JWT expiry, refresh, blacklist
  - Permission tests: role cannot access unauthorized modules
  - Frontend: React Testing Library for key components
  - E2E: Playwright scripts for critical flows 
    (login → attend → fee → report)
  - Test coverage target: >80%

PERFORMANCE:
  - Async SQLAlchemy queries throughout
  - Pagination on all list endpoints (page, page_size, total)
  - Redis cache for: dashboard stats, dropdown lists, school settings
  - DB indexes on: users (school_id, email), students (school_id, admission_number),
    student_enrollments (student_id, academic_year_id), student_enrollments (class_id, section_id),
    student_attendance (school_id, session_id), student_attendance (student_id, created_at),
    fee_invoices (student_id, status, due_date), fee_payments (invoice_id),
    audit_logs (school_id, timestamp), admission_forms (school_id, status)
  - N+1 query prevention using SQLAlchemy selectinload/joinedload
  - Large PDF/Excel generation via Celery async tasks
  - Frontend: React.lazy + Suspense for route-level code splitting
  - TanStack Query staleTime configuration per resource type
  - Virtualised lists (TanStack Virtual) for tables >500 rows


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 25 — DEPLOYMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Docker Compose Services:
  - postgres        : PostgreSQL 15
  - redis           : Redis 7
  - backend         : FastAPI (uvicorn --workers 4)
  - celery_worker   : Celery worker (concurrency=4)
  - celery_beat     : Celery periodic task scheduler
  - flower          : Celery monitoring UI
  - frontend_build  : React static build
  - nginx           : Reverse proxy + static file serving + SSL

Production Checklist:
  - SSL certificate (Let's Encrypt via Certbot)
  - Nginx: rate limiting, gzip, security headers 
    (HSTS, X-Frame-Options, CSP)
  - PostgreSQL: regular pg_dump backups to S3
  - Environment-specific .env files (dev, staging, prod)
  - CI/CD: GitHub Actions pipeline 
    (lint → test → build → docker push → deploy)
  - Log aggregation: structured JSON logs → ELK / CloudWatch
  - Health monitoring: Uptime Kuma / Better Uptime
  - Database connection pooling: pgBouncer in front of PostgreSQL


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GENERAL CODING STANDARDS TO FOLLOW THROUGHOUT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BACKEND:
  - Repository pattern: all DB queries in /repositories, never in routes
  - Service layer: all business logic in /services
  - Routes only: validate input, call service, return response
  - Consistent response envelope:
    { success: bool, data: any, message: str, pagination: {...} | null }
  - HTTP status codes: 200 OK, 201 Created, 400 Bad Request,
    401 Unauthorized, 403 Forbidden, 404 Not Found, 422 Validation, 500 Error
  - All datetime fields stored as UTC in PostgreSQL
  - All mutable tables include updated_at (auto-updated via SQLAlchemy onupdate=func.now())
  - Soft delete: set is_active=False + deleted_at (UTC timestamp) + deleted_by (user_id);
    never hard delete; all list queries filter WHERE is_active = TRUE by default
  - DB-level UNIQUE constraints (enforce in Alembic migrations):
      users.email UNIQUE per school
      students.admission_number UNIQUE per school
      staff.employee_id UNIQUE per school
      staff_payroll UNIQUE (staff_id, month, year)
      student_enrollments UNIQUE (student_id, academic_year_id)
      roles.slug UNIQUE per school
      academic_years: partial unique index UNIQUE (school_id) WHERE is_current = TRUE
  - snake_case for Python, camelCase in JSON responses (FastAPI response_model)
  - All money values stored as Integer (paise/cents), displayed as decimal
  - Docstrings on all service functions

FRONTEND:
  - Every API call in /api/*.ts, never inline in components
  - Custom hooks (useStudents, useFees, etc.) wrap TanStack Query calls
  - Error boundary at layout level
  - Toast notifications for all async action results (success/error)
  - Loading skeletons on all data-fetching components
  - All forms use React Hook Form + Zod schema
  - Consistent page layout: page header with title + breadcrumb + action buttons,
    filter bar, data table/content, pagination footer
  - Permission-gated rendering: <PermissionGuard module="fees" action="create">
  - All TypeScript: no `any` types except in legacy adapters
  - Dark mode support via Tailwind dark: classes
  - Accessibility: ARIA labels on interactive elements, keyboard navigation


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DEVELOPMENT ORDER (follow strictly)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Build in this exact sequence; each phase depends on the prior:

  1.  Infrastructure & Docker Compose
  2.  Database models (all models with Alembic migrations + UNIQUE constraints)
  3.  Authentication & JWT (including OTP flow)
  4.  Role & Permission system
  5.  School Settings, Academic Year & Online Admissions
  6.  Class & Section & Subject management
  7.  Staff management
  8.  Student management (with student_enrollments)
  9.  Attendance (student + staff)
  10. Fee management
  11. Exam management
  12. Library management
  13. Transport management
  14. Inventory management
  15. Income & Expense accounting
  16. Communication & Notifications engine
  17. Calendar
  18. Homework, Lesson Plans & PTM Scheduling
  19. ID Card / Admit Card Template Builder
  20. Reports module
  21. Audit Logs
  22. Dashboard with all charts
  23. Parent portal + PWA features
  24. Admin Super Panel
  25. Settings page
  26. Testing suite
  27. Production deployment configuration


When implementing each module, always:
  a) Create or update database model + Alembic migration
  b) Write Pydantic schemas (request + response)
  c) Write repository (DB queries)
  d) Write service (business logic)
  e) Write FastAPI route handlers
  f) Add audit log calls on mutating operations
  g) Add permission_required dependency to all routes
  h) Write pytest tests
  i) Create React TypeScript types
  j) Create API call functions
  k) Create custom hooks
  l) Build UI page with full CRUD, filters, pagination, export
  m) Add route to sidebar navigation
  n) Gate sidebar items and page elements by role permission

================================================================================
END OF PROMPT
================================================================================