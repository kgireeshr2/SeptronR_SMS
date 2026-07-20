-- =============================================================================
-- SEPTROSCHOOL (School ERP)
-- Complete PostgreSQL Database Schema
-- PostgreSQL 15+  |  UUID primary keys  |  All timestamps UTC
-- =============================================================================
-- TABLE OF CONTENTS
--  SECTION  1 : Extensions & Utility Functions
--  SECTION  2 : Foundation  — schools, school_profile, school_settings
--  SECTION  3 : Auth        — users, password_reset_tokens
--  SECTION  4 : RBAC        — roles, permissions, role_permissions, user_roles
--  SECTION  5 : Academic    — academic_years, academic_terms
--  SECTION  6 : Admissions  — admission_form_configs, admission_forms
--  SECTION  7 : Classes     — classes, sections, subjects, class_subjects, timetable
--  SECTION  8 : Staff       — departments, designations, staff, staff_documents,
--                             leave_types, staff_leaves, staff_leave_balances,
--                             staff_payroll, staff_attendance
--  SECTION  9 : Students    — students, student_enrollments, student_parents,
--                             student_documents, student_promotions, student_transfers
--  SECTION 10 : Attendance  — holidays, attendance_sessions, student_attendance
--  SECTION 11 : Fees        — fee_categories, fee_structures, fee_discounts,
--                             student_fee_assignments, fee_invoices, fee_invoice_items,
--                             fee_payments, fine_configurations
--  SECTION 12 : Exams       — exam_types, exams, admit_card_configs, student_marks,
--                             grading_scales, report_card_templates
--  SECTION 13 : Library     — book_categories, books, library_members,
--                             book_issues, library_fines
--  SECTION 14 : Transport   — vehicles, routes, stops, student_transport,
--                             vehicle_maintenance, vehicle_fuel_log
--  SECTION 15 : Inventory   — inventory_categories, items, stores,
--                             stock_entries, stock_issues,
--                             suppliers, purchase_orders, purchase_order_items
--  SECTION 16 : Accounting  — income_categories, expense_categories,
--                             income_records, expense_records, budget_heads
--  SECTION 17 : Comms       — notification_templates, notifications,
--                             bulk_messages, message_logs, announcements
--  SECTION 18 : Homework    — homework, homework_submissions, lesson_plans
--  SECTION 19 : PTM         — ptm_events, ptm_slots, ptm_bookings
--  SECTION 20 : Calendar    — calendar_events
--  SECTION 21 : Templates   — document_templates
--  SECTION 22 : Audit       — audit_logs
--  SECTION 23 : INDEXES
--  SECTION 24 : SEED DATA   (permissions, roles, default settings, super admin)
-- =============================================================================

-- =============================================================================
-- SECTION 1: EXTENSIONS & UTILITY FUNCTIONS
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION trigger_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW() AT TIME ZONE 'UTC';
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Helper macro to attach the trigger to any table
-- Usage: SELECT attach_updated_at_trigger('table_name');
CREATE OR REPLACE FUNCTION attach_updated_at_trigger(tbl TEXT)
RETURNS VOID AS $$
BEGIN
  EXECUTE format(
    'CREATE TRIGGER trg_%s_updated_at
     BEFORE UPDATE ON %I
     FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at()',
    tbl, tbl
  );
END;
$$ LANGUAGE plpgsql;


-- =============================================================================
-- SECTION 2: FOUNDATION
-- =============================================================================

CREATE TABLE schools (
    id                  UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    name                VARCHAR(200) NOT NULL,
    slug                VARCHAR(100) NOT NULL UNIQUE,   -- subdomain key e.g. "greenwood"
    is_active           BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
SELECT attach_updated_at_trigger('schools');

CREATE TABLE school_profile (
    id                      UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id               UUID        NOT NULL UNIQUE REFERENCES schools(id) ON DELETE CASCADE,
    school_name             VARCHAR(200) NOT NULL,
    tagline                 VARCHAR(300),
    address                 TEXT,
    city                    VARCHAR(100),
    state                   VARCHAR(100),
    country                 VARCHAR(100) DEFAULT 'India',
    pincode                 VARCHAR(20),
    phone                   VARCHAR(20),
    email                   VARCHAR(200),
    website                 VARCHAR(300),
    logo_url                TEXT,
    favicon_url             TEXT,
    established_year        SMALLINT,
    affiliation_board       VARCHAR(100),      -- e.g. CBSE, ICSE, State Board
    affiliation_number      VARCHAR(100),
    principal_name          VARCHAR(200),
    principal_signature_url TEXT,
    school_seal_url         TEXT,
    timezone                VARCHAR(60)  DEFAULT 'Asia/Kolkata',
    currency                VARCHAR(10)  DEFAULT 'INR',
    date_format             VARCHAR(20)  DEFAULT 'DD/MM/YYYY',
    academic_start_month    SMALLINT     DEFAULT 4,  -- April = 4
    updated_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
SELECT attach_updated_at_trigger('school_profile');

-- Key-value settings store (flexible, typed)
CREATE TABLE school_settings (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id   UUID        NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    category    VARCHAR(50) NOT NULL,   -- general|admission|attendance|fees|comm|library|exam|security|integrations|backup
    key         VARCHAR(100) NOT NULL,
    value       TEXT,                   -- stored as string; app parses by data_type
    data_type   VARCHAR(20) NOT NULL DEFAULT 'string',   -- string|integer|boolean|json
    is_public   BOOLEAN     NOT NULL DEFAULT FALSE,
    updated_by  UUID,                   -- FK to users (set after users table created)
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (school_id, key)
);
SELECT attach_updated_at_trigger('school_settings');


-- =============================================================================
-- SECTION 3: AUTH — USERS
-- =============================================================================

CREATE TABLE users (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id       UUID        REFERENCES schools(id) ON DELETE CASCADE,
                                -- NULL only for Super Admin (platform-level)
    username        VARCHAR(100),
    email           VARCHAR(200),
    phone           VARCHAR(20),
    password_hash   TEXT,
    otp_secret      VARCHAR(64),        -- TOTP seed for 2FA / OTP login
    is_active       BOOLEAN     NOT NULL DEFAULT TRUE,
    is_verified     BOOLEAN     NOT NULL DEFAULT FALSE,
    avatar_url      TEXT,
    last_login      TIMESTAMPTZ,
    is_super_admin  BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID        REFERENCES users(id),
    CONSTRAINT uq_user_email_per_school   UNIQUE (school_id, email),
    CONSTRAINT uq_user_username_per_school UNIQUE (school_id, username),
    CONSTRAINT chk_user_contact CHECK (
        email IS NOT NULL OR phone IS NOT NULL
    )
);
SELECT attach_updated_at_trigger('users');

CREATE TABLE password_reset_tokens (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash  TEXT        NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ NOT NULL,
    used_at     TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- =============================================================================
-- SECTION 4: RBAC — ROLES & PERMISSIONS
-- =============================================================================

CREATE TABLE roles (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id   UUID        REFERENCES schools(id) ON DELETE CASCADE,
                            -- NULL = platform-wide role (Super Admin)
    name        VARCHAR(100) NOT NULL,
    slug        VARCHAR(100) NOT NULL,
    description TEXT,
    is_system   BOOLEAN     NOT NULL DEFAULT FALSE,  -- system roles cannot be deleted
    is_active   BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (school_id, slug)
);
SELECT attach_updated_at_trigger('roles');

CREATE TABLE permissions (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    module      VARCHAR(60) NOT NULL,   -- students|staff|fees|attendance|exams|...
    action      VARCHAR(30) NOT NULL,   -- view|create|update|delete|export|approve|manage
    description TEXT,
    UNIQUE (module, action)
);

CREATE TABLE role_permissions (
    role_id         UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id   UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE user_roles (
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id     UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    assigned_by UUID REFERENCES users(id),
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, role_id)
);

-- Back-fill FK deferred earlier
ALTER TABLE school_settings
    ADD CONSTRAINT fk_settings_updated_by
    FOREIGN KEY (updated_by) REFERENCES users(id);


-- =============================================================================
-- SECTION 5: ACADEMIC YEAR & TERMS
-- =============================================================================

CREATE TABLE academic_years (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id   UUID        NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name        VARCHAR(20) NOT NULL,   -- e.g. "2025-2026"
    start_date  DATE        NOT NULL,
    end_date    DATE        NOT NULL,
    is_current  BOOLEAN     NOT NULL DEFAULT FALSE,
    is_locked   BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_year_dates CHECK (end_date > start_date)
);
SELECT attach_updated_at_trigger('academic_years');

-- Only one active year per school (partial unique index)
CREATE UNIQUE INDEX uq_one_current_year
    ON academic_years (school_id)
    WHERE is_current = TRUE;

CREATE TABLE academic_terms (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id       UUID        NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    academic_year_id UUID       NOT NULL REFERENCES academic_years(id) ON DELETE CASCADE,
    name            VARCHAR(50) NOT NULL,  -- "Term 1" | "Semester 1"
    start_date      DATE        NOT NULL,
    end_date        DATE        NOT NULL,
    is_current      BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_term_dates CHECK (end_date > start_date)
);
SELECT attach_updated_at_trigger('academic_terms');

CREATE UNIQUE INDEX uq_one_current_term
    ON academic_terms (academic_year_id)
    WHERE is_current = TRUE;


-- =============================================================================
-- SECTION 6: ONLINE ADMISSIONS
-- =============================================================================

CREATE TABLE admission_form_configs (
    id                  UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id           UUID        NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    academic_year_id    UUID        NOT NULL REFERENCES academic_years(id),
    fields_config       JSONB       NOT NULL DEFAULT '[]',  -- [{field,label,required,type}]
    required_documents  JSONB       NOT NULL DEFAULT '[]',  -- [{doc_type,label,required}]
    open_date           DATE,
    close_date          DATE,
    is_active           BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
SELECT attach_updated_at_trigger('admission_form_configs');

CREATE TYPE admission_status AS ENUM (
    'draft', 'submitted', 'under_review', 'approved', 'rejected', 'waitlisted'
);

CREATE TABLE admission_forms (
    id                      UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id               UUID            NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    academic_year_id        UUID            NOT NULL REFERENCES academic_years(id),
    reference_number        VARCHAR(30)     NOT NULL,
    applicant_name          VARCHAR(200)    NOT NULL,
    date_of_birth           DATE            NOT NULL,
    gender                  VARCHAR(10)     NOT NULL,
    applying_for_class_id   UUID,           -- FK set after classes table
    parent_name             VARCHAR(200),
    parent_phone            VARCHAR(20),
    parent_email            VARCHAR(200),
    address                 TEXT,
    previous_school         VARCHAR(200),
    documents               JSONB           DEFAULT '[]',    -- [{doc_type, file_url}]
    status                  admission_status NOT NULL DEFAULT 'draft',
    assigned_admission_number VARCHAR(50),
    submitted_at            TIMESTAMPTZ,
    reviewed_by             UUID            REFERENCES users(id),
    reviewed_at             TIMESTAMPTZ,
    remarks                 TEXT,
    created_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_admission_ref_per_school UNIQUE (school_id, reference_number)
);
SELECT attach_updated_at_trigger('admission_forms');


-- =============================================================================
-- SECTION 7: CLASSES, SECTIONS, SUBJECTS & TIMETABLE
-- =============================================================================

CREATE TABLE classes (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id       UUID        NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    academic_year_id UUID       NOT NULL REFERENCES academic_years(id),
    name            VARCHAR(50) NOT NULL,   -- "Grade 1" | "Class 10"
    numeric_level   SMALLINT    NOT NULL,   -- 1–12; used for sorting / promotion
    is_active       BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (school_id, academic_year_id, numeric_level)
);
SELECT attach_updated_at_trigger('classes');

-- Admission form FK deferred
ALTER TABLE admission_forms
    ADD CONSTRAINT fk_admission_class
    FOREIGN KEY (applying_for_class_id) REFERENCES classes(id);

CREATE TABLE sections (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    class_id        UUID        NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    name            VARCHAR(20) NOT NULL,   -- "A" | "B" | "Rose"
    capacity        SMALLINT    NOT NULL DEFAULT 40,
    class_teacher_id UUID       REFERENCES users(id),
    room_number     VARCHAR(20),
    is_active       BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (class_id, name)
);
SELECT attach_updated_at_trigger('sections');

-- Subjects are school-level (not tied to a class)
CREATE TABLE subjects (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id   UUID        NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name        VARCHAR(100) NOT NULL,
    code        VARCHAR(20),
    is_elective BOOLEAN     NOT NULL DEFAULT FALSE,
    full_marks  SMALLINT    NOT NULL DEFAULT 100,
    pass_marks  SMALLINT    NOT NULL DEFAULT 35,
    is_active   BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (school_id, code)
);
SELECT attach_updated_at_trigger('subjects');

-- Maps subjects to classes and assigns a teacher
CREATE TABLE class_subjects (
    id          UUID    PRIMARY KEY DEFAULT uuid_generate_v4(),
    class_id    UUID    NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    subject_id  UUID    NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    teacher_id  UUID    REFERENCES users(id),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (class_id, subject_id)
);

CREATE TABLE timetable (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id       UUID        NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    section_id      UUID        NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
    subject_id      UUID        NOT NULL REFERENCES subjects(id),
    teacher_id      UUID        REFERENCES users(id),
    academic_year_id UUID       NOT NULL REFERENCES academic_years(id),
    day_of_week     SMALLINT    NOT NULL CHECK (day_of_week BETWEEN 1 AND 7),  -- 1=Mon
    period_number   SMALLINT    NOT NULL,
    start_time      TIME        NOT NULL,
    end_time        TIME        NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_timetable_times CHECK (end_time > start_time),
    UNIQUE (section_id, academic_year_id, day_of_week, period_number)
);
SELECT attach_updated_at_trigger('timetable');


-- =============================================================================
-- SECTION 8: STAFF
-- =============================================================================

CREATE TABLE departments (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id   UUID        NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name        VARCHAR(100) NOT NULL,
    hod_id      UUID,       -- FK to staff (circular; added below)
    is_active   BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (school_id, name)
);
SELECT attach_updated_at_trigger('departments');

CREATE TABLE designations (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id   UUID        NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name        VARCHAR(100) NOT NULL,
    is_active   BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (school_id, name)
);
SELECT attach_updated_at_trigger('designations');

CREATE TYPE employment_type AS ENUM ('permanent', 'contract', 'part_time', 'probation');
CREATE TYPE salary_type AS ENUM ('monthly', 'hourly', 'daily');

CREATE TABLE staff (
    id                  UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id           UUID            NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    employee_id         VARCHAR(30)     NOT NULL,   -- auto-generated e.g. EMP-001
    user_id             UUID            NOT NULL UNIQUE REFERENCES users(id),
    first_name          VARCHAR(100)    NOT NULL,
    last_name           VARCHAR(100)    NOT NULL,
    date_of_birth       DATE,
    gender              VARCHAR(10),
    photo_url           TEXT,
    department_id       UUID            REFERENCES departments(id),
    designation_id      UUID            REFERENCES designations(id),
    date_of_joining     DATE,
    employment_type     employment_type NOT NULL DEFAULT 'permanent',
    is_active           BOOLEAN         NOT NULL DEFAULT TRUE,
    salary_type         salary_type     NOT NULL DEFAULT 'monthly',
    monthly_salary      INTEGER         NOT NULL DEFAULT 0,  -- stored in paise/cents
    bank_account_no     VARCHAR(30),
    bank_name           VARCHAR(100),
    ifsc_code           VARCHAR(20),
    address             TEXT,
    emergency_contact   JSONB,   -- {name, phone, relation}
    qualifications      JSONB    DEFAULT '[]',  -- [{degree, institute, year}]
    experience_years    NUMERIC(4,1),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at          TIMESTAMPTZ,
    deleted_by          UUID REFERENCES users(id),
    CONSTRAINT uq_employee_id_per_school UNIQUE (school_id, employee_id)
);
SELECT attach_updated_at_trigger('staff');

-- Resolve circular FK on departments
ALTER TABLE departments
    ADD CONSTRAINT fk_dept_hod FOREIGN KEY (hod_id) REFERENCES staff(id);

CREATE TABLE staff_documents (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id   UUID        NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    staff_id    UUID        NOT NULL REFERENCES staff(id) ON DELETE CASCADE,
    doc_type    VARCHAR(60) NOT NULL,   -- Aadhaar|PAN|Resume|Degree|Experience
    file_url    TEXT        NOT NULL,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE leave_types (
    id                  UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id           UUID        NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name                VARCHAR(60) NOT NULL,
    max_days_per_year   SMALLINT    NOT NULL DEFAULT 0,
    is_paid             BOOLEAN     NOT NULL DEFAULT TRUE,
    is_active           BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (school_id, name)
);

CREATE TYPE leave_status AS ENUM ('pending', 'approved', 'rejected', 'cancelled');

CREATE TABLE staff_leaves (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id       UUID        NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    staff_id        UUID        NOT NULL REFERENCES staff(id) ON DELETE CASCADE,
    leave_type_id   UUID        NOT NULL REFERENCES leave_types(id),
    from_date       DATE        NOT NULL,
    to_date         DATE        NOT NULL,
    total_days      NUMERIC(4,1) NOT NULL,
    reason          TEXT,
    status          leave_status NOT NULL DEFAULT 'pending',
    approved_by     UUID        REFERENCES users(id),
    approved_at     TIMESTAMPTZ,
    remarks         TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_leave_dates CHECK (to_date >= from_date)
);
SELECT attach_updated_at_trigger('staff_leaves');

-- Leave balance tracker — updated whenever a leave is approved/cancelled/reset
CREATE TABLE staff_leave_balances (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id       UUID        NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    staff_id        UUID        NOT NULL REFERENCES staff(id) ON DELETE CASCADE,
    leave_type_id   UUID        NOT NULL REFERENCES leave_types(id),
    academic_year_id UUID       NOT NULL REFERENCES academic_years(id),
    entitled_days   NUMERIC(4,1) NOT NULL DEFAULT 0,
    used_days       NUMERIC(4,1) NOT NULL DEFAULT 0,
    remaining_days  NUMERIC(4,1) GENERATED ALWAYS AS (entitled_days - used_days) STORED,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (staff_id, leave_type_id, academic_year_id)
);
SELECT attach_updated_at_trigger('staff_leave_balances');

CREATE TYPE payment_method AS ENUM ('cash', 'cheque', 'online', 'card', 'neft', 'upi');

CREATE TABLE staff_payroll (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id       UUID        NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    staff_id        UUID        NOT NULL REFERENCES staff(id) ON DELETE CASCADE,
    academic_year_id UUID       NOT NULL REFERENCES academic_years(id),
    month           SMALLINT    NOT NULL CHECK (month BETWEEN 1 AND 12),
    year            SMALLINT    NOT NULL,
    basic_salary    INTEGER     NOT NULL DEFAULT 0,   -- paise
    allowances      JSONB       NOT NULL DEFAULT '{}',  -- {hra:..., da:..., other:...}
    deductions      JSONB       NOT NULL DEFAULT '{}',  -- {pf:..., esi:..., tds:..., other:...}
    gross_salary    INTEGER     NOT NULL DEFAULT 0,
    net_salary      INTEGER     NOT NULL DEFAULT 0,
    payment_date    DATE,
    payment_method  payment_method,
    is_paid         BOOLEAN     NOT NULL DEFAULT FALSE,
    receipt_url     TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (staff_id, month, year)
);
SELECT attach_updated_at_trigger('staff_payroll');

CREATE TYPE attendance_source AS ENUM ('manual', 'biometric', 'qr');
CREATE TYPE staff_attendance_status AS ENUM ('present', 'absent', 'late', 'half_day', 'on_leave', 'holiday');

CREATE TABLE staff_attendance (
    id          UUID                    PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id   UUID                    NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    staff_id    UUID                    NOT NULL REFERENCES staff(id) ON DELETE CASCADE,
    date        DATE                    NOT NULL,
    check_in    TIMESTAMPTZ,
    check_out   TIMESTAMPTZ,
    status      staff_attendance_status NOT NULL DEFAULT 'present',
    remarks     TEXT,
    source      attendance_source       NOT NULL DEFAULT 'manual',
    created_at  TIMESTAMPTZ             NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ             NOT NULL DEFAULT NOW(),
    UNIQUE (staff_id, date)
);
SELECT attach_updated_at_trigger('staff_attendance');


-- =============================================================================
-- SECTION 9: STUDENTS
-- =============================================================================

CREATE TABLE students (
    id                  UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id           UUID        NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    admission_number    VARCHAR(30) NOT NULL,
    user_id             UUID        UNIQUE REFERENCES users(id),
    first_name          VARCHAR(100) NOT NULL,
    last_name           VARCHAR(100) NOT NULL,
    date_of_birth       DATE        NOT NULL,
    gender              VARCHAR(10) NOT NULL,
    blood_group         VARCHAR(5),
    religion            VARCHAR(50),
    category            VARCHAR(30),  -- General|OBC|SC|ST|EWS
    nationality         VARCHAR(60)   DEFAULT 'Indian',
    photo_url           TEXT,
    admission_date      DATE          NOT NULL,
    is_active           BOOLEAN       NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    deleted_at          TIMESTAMPTZ,
    deleted_by          UUID          REFERENCES users(id),
    CONSTRAINT uq_admission_number_per_school UNIQUE (school_id, admission_number)
);
SELECT attach_updated_at_trigger('students');

-- Per-year class/section assignment (replaces direct FK on students)
CREATE TABLE student_enrollments (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id       UUID        NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    student_id      UUID        NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    academic_year_id UUID       NOT NULL REFERENCES academic_years(id),
    class_id        UUID        NOT NULL REFERENCES classes(id),
    section_id      UUID        NOT NULL REFERENCES sections(id),
    roll_number     VARCHAR(20),   -- alphanumeric roll numbers supported e.g. A-01
    is_current      BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (student_id, academic_year_id)
);
SELECT attach_updated_at_trigger('student_enrollments');

CREATE TYPE parent_relation AS ENUM ('father', 'mother', 'guardian', 'sibling', 'other');

CREATE TABLE student_parents (
    id                  UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id           UUID            NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    student_id          UUID            NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    user_id             UUID            REFERENCES users(id),
    relation            parent_relation NOT NULL DEFAULT 'father',
    name                VARCHAR(200)    NOT NULL,
    phone               VARCHAR(20),
    email               VARCHAR(200),
    occupation          VARCHAR(100),
    address             TEXT,
    is_primary_contact  BOOLEAN         NOT NULL DEFAULT FALSE,
    can_access_portal   BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);
SELECT attach_updated_at_trigger('student_parents');

CREATE TABLE student_documents (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id   UUID        NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    student_id  UUID        NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    doc_type    VARCHAR(60) NOT NULL,  -- BirthCertificate|Aadhaar|Marksheet|TC|Photo
    file_url    TEXT        NOT NULL,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE student_promotions (
    id              UUID    PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id       UUID    NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    student_id      UUID    NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    from_class_id   UUID    NOT NULL REFERENCES classes(id),
    to_class_id     UUID    NOT NULL REFERENCES classes(id),
    from_year_id    UUID    NOT NULL REFERENCES academic_years(id),
    to_year_id      UUID    NOT NULL REFERENCES academic_years(id),
    promoted_by     UUID    NOT NULL REFERENCES users(id),
    promoted_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE student_transfers (
    id                          UUID    PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id                   UUID    NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    student_id                  UUID    NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    transfer_certificate_no     VARCHAR(50) NOT NULL,
    leaving_date                DATE        NOT NULL,
    reason                      TEXT,
    issued_by                   UUID        REFERENCES users(id),
    issued_at                   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_tc_number_per_school UNIQUE (school_id, transfer_certificate_no)
);


-- =============================================================================
-- SECTION 10: ATTENDANCE
-- =============================================================================

CREATE TYPE holiday_type AS ENUM ('national', 'state', 'school', 'religious', 'other');

CREATE TABLE holidays (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id       UUID        NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    academic_year_id UUID       NOT NULL REFERENCES academic_years(id),
    name            VARCHAR(200) NOT NULL,
    date            DATE        NOT NULL,
    holiday_type    holiday_type NOT NULL DEFAULT 'school',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (school_id, date)
);

CREATE TYPE session_type AS ENUM ('morning', 'afternoon', 'full_day');

CREATE TABLE attendance_sessions (
    id              UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id       UUID            NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    session_type    session_type    NOT NULL DEFAULT 'full_day',
    date            DATE            NOT NULL,
    class_id        UUID            NOT NULL REFERENCES classes(id),
    section_id      UUID            NOT NULL REFERENCES sections(id),
    taken_by        UUID            NOT NULL REFERENCES users(id),
    is_finalized    BOOLEAN         NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    UNIQUE (section_id, date, session_type)
);

CREATE TYPE student_attendance_status AS ENUM (
    'present', 'absent', 'late', 'half_day', 'leave', 'holiday'
);

CREATE TABLE student_attendance (
    id              UUID                        PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id       UUID                        NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    session_id      UUID                        NOT NULL REFERENCES attendance_sessions(id) ON DELETE CASCADE,
    student_id      UUID                        NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    status          student_attendance_status   NOT NULL DEFAULT 'present',
    remarks         TEXT,
    notified_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ                 NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ                 NOT NULL DEFAULT NOW(),
    UNIQUE (session_id, student_id)
);
SELECT attach_updated_at_trigger('student_attendance');


-- =============================================================================
-- SECTION 11: FEES
-- =============================================================================

CREATE TABLE fee_categories (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id   UUID        NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name        VARCHAR(100) NOT NULL,  -- "Tuition Fee" | "Transport Fee"
    description TEXT,
    is_active   BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (school_id, name)
);
SELECT attach_updated_at_trigger('fee_categories');

CREATE TYPE fee_frequency AS ENUM ('monthly', 'quarterly', 'annual', 'one_time', 'semi_annual');

CREATE TABLE fee_structures (
    id              UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id       UUID            NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    academic_year_id UUID           NOT NULL REFERENCES academic_years(id),
    class_id        UUID            NOT NULL REFERENCES classes(id),
    fee_category_id UUID            NOT NULL REFERENCES fee_categories(id),
    amount          INTEGER         NOT NULL DEFAULT 0,  -- paise
    frequency       fee_frequency   NOT NULL DEFAULT 'monthly',
    due_day         SMALLINT        CHECK (due_day BETWEEN 1 AND 31),
    is_active       BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    UNIQUE (school_id, academic_year_id, class_id, fee_category_id)
);
SELECT attach_updated_at_trigger('fee_structures');

CREATE TYPE discount_type AS ENUM ('percentage', 'fixed');
CREATE TYPE discount_applicable_to AS ENUM ('student', 'category', 'class');

CREATE TABLE fee_discounts (
    id              UUID                    PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id       UUID                    NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name            VARCHAR(100)            NOT NULL,
    type            discount_type           NOT NULL DEFAULT 'percentage',
    value           NUMERIC(10,2)           NOT NULL,
    applicable_to   discount_applicable_to  NOT NULL DEFAULT 'student',
    is_active       BOOLEAN                 NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ             NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ             NOT NULL DEFAULT NOW()
);
SELECT attach_updated_at_trigger('fee_discounts');

CREATE TABLE student_fee_assignments (
    id                  UUID    PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id           UUID    NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    student_id          UUID    NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    fee_structure_id    UUID    NOT NULL REFERENCES fee_structures(id),
    discount_id         UUID    REFERENCES fee_discounts(id),
    custom_amount       INTEGER,   -- overrides structure amount if set (paise)
    academic_year_id    UUID    NOT NULL REFERENCES academic_years(id),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (student_id, fee_structure_id, academic_year_id)
);
SELECT attach_updated_at_trigger('student_fee_assignments');

CREATE TYPE invoice_status AS ENUM ('unpaid', 'partial', 'paid', 'overdue', 'waived', 'cancelled');

CREATE TABLE fee_invoices (
    id              UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id       UUID            NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    student_id      UUID            NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    academic_year_id UUID           NOT NULL REFERENCES academic_years(id),
    invoice_number  VARCHAR(50)     NOT NULL,
    invoice_date    DATE            NOT NULL DEFAULT CURRENT_DATE,
    due_date        DATE            NOT NULL,
    status          invoice_status  NOT NULL DEFAULT 'unpaid',
    total_amount    INTEGER         NOT NULL DEFAULT 0,   -- paise
    paid_amount     INTEGER         NOT NULL DEFAULT 0,
    balance_amount  INTEGER         GENERATED ALWAYS AS (total_amount - paid_amount) STORED,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    UNIQUE (school_id, invoice_number)
);
SELECT attach_updated_at_trigger('fee_invoices');

CREATE TABLE fee_invoice_items (
    id              UUID    PRIMARY KEY DEFAULT uuid_generate_v4(),
    invoice_id      UUID    NOT NULL REFERENCES fee_invoices(id) ON DELETE CASCADE,
    fee_category_id UUID    NOT NULL REFERENCES fee_categories(id),
    amount          INTEGER NOT NULL DEFAULT 0,   -- paise
    discount_amt    INTEGER NOT NULL DEFAULT 0,
    fine_applied    INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE fee_payments (
    id                  UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id           UUID            NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    invoice_id          UUID            NOT NULL REFERENCES fee_invoices(id) ON DELETE CASCADE,
    amount              INTEGER         NOT NULL,   -- paise
    payment_date        DATE            NOT NULL DEFAULT CURRENT_DATE,
    payment_method      payment_method  NOT NULL,
    transaction_id      VARCHAR(100),
    receipt_number      VARCHAR(50)     NOT NULL,
    collected_by        UUID            NOT NULL REFERENCES users(id),
    remarks             TEXT,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    UNIQUE (school_id, receipt_number)
);

CREATE TYPE fine_calc_type AS ENUM ('fixed', 'percentage_per_day');

CREATE TABLE fine_configurations (
    id                  UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id           UUID            NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name                VARCHAR(100)    NOT NULL,
    type                fine_calc_type  NOT NULL DEFAULT 'fixed',
    value               NUMERIC(10,2)   NOT NULL DEFAULT 0,
    applicable_after_days SMALLINT      NOT NULL DEFAULT 0,
    is_active           BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);
SELECT attach_updated_at_trigger('fine_configurations');


-- =============================================================================
-- SECTION 12: EXAMS
-- =============================================================================

CREATE TABLE exam_types (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id       UUID        NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    academic_year_id UUID       NOT NULL REFERENCES academic_years(id),
    term_id         UUID        REFERENCES academic_terms(id),
    name            VARCHAR(100) NOT NULL,   -- "Unit Test 1" | "Mid-Term" | "Final"
    weight_percentage NUMERIC(5,2) NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE exams (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id       UUID        NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    academic_year_id UUID       NOT NULL REFERENCES academic_years(id),
    exam_type_id    UUID        NOT NULL REFERENCES exam_types(id),
    class_id        UUID        NOT NULL REFERENCES classes(id),
    subject_id      UUID        NOT NULL REFERENCES subjects(id),
    exam_date       DATE        NOT NULL,
    start_time      TIME,
    end_time        TIME,
    total_marks     SMALLINT    NOT NULL DEFAULT 100,
    pass_marks      SMALLINT    NOT NULL DEFAULT 35,
    venue           VARCHAR(100),
    invigilator_id  UUID        REFERENCES users(id),
    is_published    BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
SELECT attach_updated_at_trigger('exams');

CREATE TABLE admit_card_configs (
    id              UUID    PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id       UUID    NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    exam_type_id    UUID    NOT NULL UNIQUE REFERENCES exam_types(id),
    instructions    TEXT,
    footer_text     TEXT,
    logo_url        TEXT,
    signature_url   TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
SELECT attach_updated_at_trigger('admit_card_configs');

CREATE TABLE student_marks (
    id              UUID    PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id       UUID    NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    exam_id         UUID    NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
    student_id      UUID    NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    marks_obtained  NUMERIC(6,2),
    grade           VARCHAR(5),
    is_absent       BOOLEAN NOT NULL DEFAULT FALSE,
    remarks         TEXT,
    entered_by      UUID    REFERENCES users(id),
    entered_at      TIMESTAMPTZ,
    verified_by     UUID    REFERENCES users(id),
    verified_at     TIMESTAMPTZ,
    is_verified     BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (exam_id, student_id)
);
SELECT attach_updated_at_trigger('student_marks');

CREATE TABLE grading_scales (
    id          UUID    PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id   UUID    NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name        VARCHAR(100) NOT NULL,
    -- [{min_pct, max_pct, grade, gpa, description}]
    ranges      JSONB   NOT NULL DEFAULT '[]',
    is_default  BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE report_card_templates (
    id              UUID    PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id       UUID    NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name            VARCHAR(100) NOT NULL,
    template_html   TEXT,
    layout_config   JSONB   DEFAULT '{}',
    is_default      BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
SELECT attach_updated_at_trigger('report_card_templates');


-- =============================================================================
-- SECTION 13: LIBRARY
-- =============================================================================

CREATE TABLE book_categories (
    id          UUID    PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id   UUID    NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name        VARCHAR(100) NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (school_id, name)
);

CREATE TABLE books (
    id              UUID    PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id       UUID    NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    title           VARCHAR(300) NOT NULL,
    author          VARCHAR(300),
    publisher       VARCHAR(200),
    isbn            VARCHAR(20),
    category_id     UUID    REFERENCES book_categories(id),
    edition         VARCHAR(50),
    language        VARCHAR(50) DEFAULT 'English',
    total_copies    SMALLINT NOT NULL DEFAULT 1,
    -- available_copies is COMPUTED at query time: total_copies - active issues
    shelf_location  VARCHAR(50),
    cover_url       TEXT,
    description     TEXT,
    purchase_date   DATE,
    purchase_price  INTEGER,   -- paise
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (school_id, isbn)
);
SELECT attach_updated_at_trigger('books');

CREATE TYPE member_type AS ENUM ('student', 'staff');

CREATE TABLE library_members (
    id                  UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id           UUID        NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    member_id           VARCHAR(20) NOT NULL,   -- auto-generated LIB-001
    user_id             UUID        NOT NULL REFERENCES users(id),
    member_type         member_type NOT NULL DEFAULT 'student',
    card_expiry         DATE,
    max_books_allowed   SMALLINT    NOT NULL DEFAULT 3,
    is_active           BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (school_id, member_id)
);

CREATE TYPE book_issue_status AS ENUM ('issued', 'returned', 'overdue', 'lost');

CREATE TABLE book_issues (
    id              UUID                PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id       UUID                NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    book_id         UUID                NOT NULL REFERENCES books(id),
    member_id       UUID                NOT NULL REFERENCES library_members(id),
    issue_date      DATE                NOT NULL DEFAULT CURRENT_DATE,
    due_date        DATE                NOT NULL,
    return_date     DATE,
    fine_amount     INTEGER             NOT NULL DEFAULT 0,   -- paise
    fine_paid       BOOLEAN             NOT NULL DEFAULT FALSE,
    issued_by       UUID                REFERENCES users(id),
    status          book_issue_status   NOT NULL DEFAULT 'issued',
    created_at      TIMESTAMPTZ         NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ         NOT NULL DEFAULT NOW()
);
SELECT attach_updated_at_trigger('book_issues');

CREATE TABLE library_fines (
    id          UUID    PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id   UUID    NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    issue_id    UUID    NOT NULL REFERENCES book_issues(id),
    amount      INTEGER NOT NULL,   -- paise
    reason      TEXT,
    is_paid     BOOLEAN NOT NULL DEFAULT FALSE,
    paid_date   DATE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- =============================================================================
-- SECTION 14: TRANSPORT
-- =============================================================================

CREATE TABLE vehicles (
    id                  UUID    PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id           UUID    NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    vehicle_number      VARCHAR(20) NOT NULL,
    vehicle_type        VARCHAR(30),   -- Bus|Van|Mini-Bus
    model               VARCHAR(100),
    capacity            SMALLINT NOT NULL DEFAULT 40,
    insurance_expiry    DATE,
    fitness_expiry      DATE,
    pollution_expiry    DATE,
    driver_id           UUID    REFERENCES staff(id) ON DELETE SET NULL,
    conductor_id        UUID    REFERENCES staff(id) ON DELETE SET NULL,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (school_id, vehicle_number)
);
SELECT attach_updated_at_trigger('vehicles');

CREATE TABLE routes (
    id          UUID    PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id   UUID    NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    route_name  VARCHAR(100) NOT NULL,
    start_point VARCHAR(200),
    end_point   VARCHAR(200),
    total_km    NUMERIC(6,2),
    vehicle_id  UUID    REFERENCES vehicles(id),
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
SELECT attach_updated_at_trigger('routes');

CREATE TABLE stops (
    id          UUID    PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id   UUID    NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    route_id    UUID    NOT NULL REFERENCES routes(id) ON DELETE CASCADE,
    stop_name   VARCHAR(200) NOT NULL,
    stop_order  SMALLINT NOT NULL,
    pickup_time TIME,
    drop_time   TIME,
    latitude    NUMERIC(9,6),
    longitude   NUMERIC(9,6),
    UNIQUE (route_id, stop_order)
);

CREATE TABLE student_transport (
    id              UUID    PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id       UUID    NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    student_id      UUID    NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    route_id        UUID    NOT NULL REFERENCES routes(id),
    stop_id         UUID    NOT NULL REFERENCES stops(id),
    academic_year_id UUID   NOT NULL REFERENCES academic_years(id),
    fee_amount      INTEGER NOT NULL DEFAULT 0,   -- paise
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (student_id, academic_year_id)
);

CREATE TYPE maintenance_type AS ENUM (
    'oil_change', 'tyre', 'brake', 'engine', 'body', 'service', 'other'
);

CREATE TABLE vehicle_maintenance (
    id                  UUID                PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id           UUID                NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    vehicle_id          UUID                NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
    maintenance_type    maintenance_type    NOT NULL DEFAULT 'service',
    date                DATE                NOT NULL,
    cost                INTEGER             NOT NULL DEFAULT 0,   -- paise
    description         TEXT,
    next_due_date       DATE,
    created_at          TIMESTAMPTZ         NOT NULL DEFAULT NOW()
);

CREATE TABLE vehicle_fuel_log (
    id                  UUID    PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id           UUID    NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    vehicle_id          UUID    NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
    date                DATE    NOT NULL,
    fuel_type           VARCHAR(20) NOT NULL DEFAULT 'diesel',
    litres              NUMERIC(8,2) NOT NULL,
    cost_per_litre      INTEGER NOT NULL,   -- paise
    odometer_reading    INTEGER,
    filled_by           UUID    REFERENCES staff(id),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- =============================================================================
-- SECTION 15: INVENTORY
-- =============================================================================

CREATE TABLE inventory_categories (
    id          UUID    PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id   UUID    NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name        VARCHAR(100) NOT NULL,
    description TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (school_id, name)
);

CREATE TABLE items (
    id                  UUID    PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id           UUID    NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    category_id         UUID    NOT NULL REFERENCES inventory_categories(id),
    item_name           VARCHAR(200) NOT NULL,
    item_code           VARCHAR(50),
    unit                VARCHAR(20) NOT NULL DEFAULT 'pcs',   -- pcs|kg|ltr|box
    minimum_stock_level INTEGER NOT NULL DEFAULT 0,
    description         TEXT,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (school_id, item_code)
);
SELECT attach_updated_at_trigger('items');

CREATE TABLE stores (
    id          UUID    PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id   UUID    NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    store_name  VARCHAR(100) NOT NULL,
    location    VARCHAR(200),
    in_charge_id UUID   REFERENCES staff(id),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (school_id, store_name)
);

CREATE TYPE stock_entry_type AS ENUM ('purchase', 'return', 'adjustment', 'opening');

CREATE TABLE stock_entries (
    id              UUID                PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id       UUID                NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    item_id         UUID                NOT NULL REFERENCES items(id),
    store_id        UUID                NOT NULL REFERENCES stores(id),
    quantity        NUMERIC(10,2)       NOT NULL,
    unit_price      INTEGER             NOT NULL DEFAULT 0,   -- paise
    total_price     NUMERIC(12,2)       GENERATED ALWAYS AS (quantity * unit_price) STORED,  -- avoid integer cast; stored in paise-equivalent
    entry_type      stock_entry_type    NOT NULL DEFAULT 'purchase',
    supplier        VARCHAR(200),
    invoice_number  VARCHAR(100),
    entry_date      DATE                NOT NULL DEFAULT CURRENT_DATE,
    entered_by      UUID                REFERENCES users(id),
    created_at      TIMESTAMPTZ         NOT NULL DEFAULT NOW()
);

CREATE TABLE stock_issues (
    id                  UUID    PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id           UUID    NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    item_id             UUID    NOT NULL REFERENCES items(id),
    store_id            UUID    NOT NULL REFERENCES stores(id),
    issued_to_user_id   UUID    REFERENCES users(id),
    issued_to_dept      VARCHAR(100),
    quantity            NUMERIC(10,2) NOT NULL,
    purpose             TEXT,
    issued_date         DATE    NOT NULL DEFAULT CURRENT_DATE,
    issued_by           UUID    REFERENCES users(id),
    return_date         DATE,
    is_returned         BOOLEAN NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE suppliers (
    id              UUID    PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id       UUID    NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name            VARCHAR(200) NOT NULL,
    contact_person  VARCHAR(200),
    phone           VARCHAR(20),
    email           VARCHAR(200),
    address         TEXT,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TYPE po_status AS ENUM ('draft', 'sent', 'partial_received', 'received', 'cancelled');

CREATE TABLE purchase_orders (
    id                  UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id           UUID        NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    supplier_id         UUID        NOT NULL REFERENCES suppliers(id),
    order_date          DATE        NOT NULL DEFAULT CURRENT_DATE,
    expected_delivery   DATE,
    status              po_status   NOT NULL DEFAULT 'draft',
    total_amount        INTEGER     NOT NULL DEFAULT 0,   -- paise
    notes               TEXT,
    created_by          UUID        REFERENCES users(id),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
SELECT attach_updated_at_trigger('purchase_orders');

CREATE TABLE purchase_order_items (
    id          UUID    PRIMARY KEY DEFAULT uuid_generate_v4(),
    po_id       UUID    NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
    item_id     UUID    NOT NULL REFERENCES items(id),
    quantity            NUMERIC(10,2)   NOT NULL,
    unit_price          INTEGER         NOT NULL DEFAULT 0,   -- paise
    received_quantity   NUMERIC(10,2)   NOT NULL DEFAULT 0,   -- for partial_received tracking
    received_at         TIMESTAMPTZ
);


-- =============================================================================
-- SECTION 16: INCOME & EXPENSE (ACCOUNTING)
-- =============================================================================

CREATE TABLE income_categories (
    id          UUID    PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id   UUID    NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name        VARCHAR(100) NOT NULL,
    description TEXT,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (school_id, name)
);

CREATE TABLE expense_categories (
    id              UUID    PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id       UUID    NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name            VARCHAR(100) NOT NULL,
    budget_amount   INTEGER NOT NULL DEFAULT 0,   -- paise
    description     TEXT,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (school_id, name)
);

CREATE TABLE income_records (
    id                  UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id           UUID            NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    academic_year_id    UUID            NOT NULL REFERENCES academic_years(id),
    category_id         UUID            NOT NULL REFERENCES income_categories(id),
    amount              INTEGER         NOT NULL,   -- paise
    source              VARCHAR(200),
    payment_method      payment_method  NOT NULL DEFAULT 'cash',
    reference_number    VARCHAR(100),
    income_date         DATE            NOT NULL DEFAULT CURRENT_DATE,
    recorded_by         UUID            NOT NULL REFERENCES users(id),
    attachment_url      TEXT,
    notes               TEXT,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE TABLE expense_records (
    id                  UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id           UUID            NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    academic_year_id    UUID            NOT NULL REFERENCES academic_years(id),
    category_id         UUID            NOT NULL REFERENCES expense_categories(id),
    amount              INTEGER         NOT NULL,   -- paise
    payee               VARCHAR(200),
    payment_method      payment_method  NOT NULL DEFAULT 'cash',
    reference_number    VARCHAR(100),
    expense_date        DATE            NOT NULL DEFAULT CURRENT_DATE,
    approved_by         UUID            REFERENCES users(id),
    attachment_url      TEXT,
    notes               TEXT,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE TYPE budget_type AS ENUM ('income', 'expense');

CREATE TABLE budget_heads (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id       UUID        NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    academic_year_id UUID       NOT NULL REFERENCES academic_years(id),
    category_id     UUID        NOT NULL,   -- income_categories.id OR expense_categories.id
                                            -- (polymorphic; FK enforced at application level)
    type            budget_type NOT NULL,
    budgeted_amount INTEGER     NOT NULL DEFAULT 0,   -- paise
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- =============================================================================
-- SECTION 17: COMMUNICATION & NOTIFICATIONS
-- =============================================================================

CREATE TYPE notification_trigger AS ENUM (
    'STUDENT_ABSENT', 'FEE_DUE', 'FEE_PAID', 'FEE_OVERDUE',
    'RESULT_PUBLISHED', 'EXAM_SCHEDULED', 'HOMEWORK_ASSIGNED',
    'LEAVE_APPROVED', 'LEAVE_REJECTED', 'LIBRARY_OVERDUE',
    'LOW_ATTENDANCE_WARNING', 'ADMISSION_APPROVED',
    'TRANSPORT_DELAY', 'ANNOUNCEMENT_PUBLISHED',
    'PTM_BOOKED', 'PTM_REMINDER', 'CUSTOM'
);

CREATE TABLE notification_templates (
    id              UUID                    PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id       UUID                    NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name            VARCHAR(100)            NOT NULL,
    event_trigger   notification_trigger    NOT NULL,
    -- {sms, whatsapp, email, push, in_app} → true/false
    channels        JSONB                   NOT NULL DEFAULT '{"in_app": true}',
    subject         VARCHAR(300),
    body            TEXT        NOT NULL,   -- supports {student_name}, {class}, {amount}, {date}
    is_active       BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (school_id, event_trigger)
);
SELECT attach_updated_at_trigger('notification_templates');

CREATE TYPE notification_channel AS ENUM ('sms', 'whatsapp', 'email', 'push', 'in_app');

CREATE TABLE notifications (
    id                  UUID                    PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id           UUID                    NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    recipient_user_id   UUID                    NOT NULL REFERENCES users(id),
    type                notification_trigger,
    title               VARCHAR(300)            NOT NULL,
    body                TEXT                    NOT NULL,
    data                JSONB                   DEFAULT '{}',
    channel             notification_channel    NOT NULL DEFAULT 'in_app',
    is_read             BOOLEAN                 NOT NULL DEFAULT FALSE,
    read_at             TIMESTAMPTZ,
    created_at          TIMESTAMPTZ             NOT NULL DEFAULT NOW()
);

CREATE TYPE bulk_message_status AS ENUM ('draft', 'scheduled', 'sending', 'sent', 'failed');

CREATE TABLE bulk_messages (
    id                  UUID                PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id           UUID                NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    title               VARCHAR(300)        NOT NULL,
    body                TEXT                NOT NULL,
    audience_filter     JSONB               NOT NULL DEFAULT '{}',
    channels            JSONB               NOT NULL DEFAULT '{"in_app": true}',
    scheduled_at        TIMESTAMPTZ,
    sent_at             TIMESTAMPTZ,
    total_recipients    INTEGER             NOT NULL DEFAULT 0,
    sent_count          INTEGER             NOT NULL DEFAULT 0,
    failed_count        INTEGER             NOT NULL DEFAULT 0,
    status              bulk_message_status NOT NULL DEFAULT 'draft',
    created_by          UUID                NOT NULL REFERENCES users(id),
    created_at          TIMESTAMPTZ         NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ         NOT NULL DEFAULT NOW()
);
SELECT attach_updated_at_trigger('bulk_messages');

CREATE TYPE message_delivery_status AS ENUM ('pending', 'sent', 'failed', 'delivered');

CREATE TABLE message_logs (
    id                  UUID                    PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id           UUID                    NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    bulk_message_id     UUID                    NOT NULL REFERENCES bulk_messages(id) ON DELETE CASCADE,
    recipient_id        UUID                    NOT NULL REFERENCES users(id),
    channel             notification_channel    NOT NULL,
    status              message_delivery_status NOT NULL DEFAULT 'pending',
    provider_message_id VARCHAR(200),
    sent_at             TIMESTAMPTZ,
    error_message       TEXT,
    created_at          TIMESTAMPTZ             NOT NULL DEFAULT NOW()
);

CREATE TABLE announcements (
    id              UUID    PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id       UUID    NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    title           VARCHAR(300) NOT NULL,
    body_html       TEXT    NOT NULL,
    target_audience VARCHAR(50) NOT NULL DEFAULT 'all'
        CHECK (target_audience IN ('all','students','staff','parents','specific_class')),
    audience_filter JSONB   DEFAULT '{}',
    publish_date    DATE    NOT NULL DEFAULT CURRENT_DATE,
    expiry_date     DATE,
    is_pinned       BOOLEAN NOT NULL DEFAULT FALSE,
    created_by      UUID    NOT NULL REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
SELECT attach_updated_at_trigger('announcements');


-- =============================================================================
-- SECTION 18: HOMEWORK & LESSON PLANS
-- =============================================================================

CREATE TABLE homework (
    id              UUID    PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id       UUID    NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    academic_year_id UUID   NOT NULL REFERENCES academic_years(id),
    class_id        UUID    NOT NULL REFERENCES classes(id),
    section_id      UUID    NOT NULL REFERENCES sections(id),
    subject_id      UUID    NOT NULL REFERENCES subjects(id),
    teacher_id      UUID    NOT NULL REFERENCES users(id),
    title           VARCHAR(300) NOT NULL,
    description     TEXT,
    due_date        DATE    NOT NULL,
    attachment_url  TEXT,
    publish_date    DATE    NOT NULL DEFAULT CURRENT_DATE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
SELECT attach_updated_at_trigger('homework');

CREATE TABLE homework_submissions (
    id          UUID    PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id   UUID    NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    homework_id UUID    NOT NULL REFERENCES homework(id) ON DELETE CASCADE,
    student_id  UUID    NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    content     TEXT,
    file_url    TEXT,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    marks_given NUMERIC(5,2),
    remarks     TEXT,
    UNIQUE (homework_id, student_id)
);

CREATE TABLE lesson_plans (
    id              UUID    PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id       UUID    NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    academic_year_id UUID   NOT NULL REFERENCES academic_years(id),
    class_id        UUID    NOT NULL REFERENCES classes(id),
    section_id      UUID    NOT NULL REFERENCES sections(id),
    subject_id      UUID    NOT NULL REFERENCES subjects(id),
    teacher_id      UUID    NOT NULL REFERENCES users(id),
    title           VARCHAR(300) NOT NULL,
    objectives      TEXT,
    content         TEXT,
    resources       TEXT,
    date            DATE    NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
SELECT attach_updated_at_trigger('lesson_plans');


-- =============================================================================
-- SECTION 19: PARENT-TEACHER MEETING (PTM)
-- =============================================================================

CREATE TABLE ptm_events (
    id                      UUID    PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id               UUID    NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    academic_year_id        UUID    NOT NULL REFERENCES academic_years(id),
    title                   VARCHAR(200) NOT NULL,
    date                    DATE    NOT NULL,
    slot_duration_minutes   SMALLINT NOT NULL DEFAULT 10,
    start_time              TIME    NOT NULL,
    end_time                TIME    NOT NULL,
    class_id                UUID    REFERENCES classes(id),     -- NULL = school-wide
    section_id              UUID    REFERENCES sections(id),    -- NULL = all sections
    created_by              UUID    NOT NULL REFERENCES users(id),
    is_active               BOOLEAN NOT NULL DEFAULT TRUE,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE ptm_slots (
    id              UUID    PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id       UUID    NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    ptm_event_id    UUID    NOT NULL REFERENCES ptm_events(id) ON DELETE CASCADE,
    teacher_id      UUID    NOT NULL REFERENCES users(id),
    slot_start      TIMESTAMPTZ NOT NULL,
    slot_end        TIMESTAMPTZ NOT NULL,
    is_booked       BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_ptm_slot UNIQUE (ptm_event_id, teacher_id, slot_start)
);

CREATE TYPE booking_status AS ENUM ('booked', 'cancelled', 'completed');

CREATE TABLE ptm_bookings (
    id              UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id       UUID            NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    ptm_slot_id     UUID            NOT NULL UNIQUE REFERENCES ptm_slots(id),
    parent_id       UUID            NOT NULL REFERENCES users(id),
    student_id      UUID            NOT NULL REFERENCES students(id),
    booking_time    TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    status          booking_status  NOT NULL DEFAULT 'booked',
    meeting_notes   TEXT,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);


-- =============================================================================
-- SECTION 20: CALENDAR
-- =============================================================================

CREATE TYPE calendar_event_type AS ENUM (
    'holiday', 'exam', 'meeting', 'sports', 'cultural', 'trip', 'other'
);

CREATE TABLE calendar_events (
    id              UUID                PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id       UUID                NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    academic_year_id UUID               NOT NULL REFERENCES academic_years(id),
    title           VARCHAR(300)        NOT NULL,
    description     TEXT,
    event_type      calendar_event_type NOT NULL DEFAULT 'other',
    start_datetime  TIMESTAMPTZ         NOT NULL,
    end_datetime    TIMESTAMPTZ,
    all_day         BOOLEAN             NOT NULL DEFAULT FALSE,
    -- all | students | staff | specific_class
    audience        VARCHAR(30)         NOT NULL DEFAULT 'all',
    audience_filter JSONB               DEFAULT '{}',
    color_tag       VARCHAR(10)         DEFAULT '#3B82F6',
    location        VARCHAR(300),
    created_by      UUID                NOT NULL REFERENCES users(id),
    created_at      TIMESTAMPTZ         NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ         NOT NULL DEFAULT NOW()
);
SELECT attach_updated_at_trigger('calendar_events');


-- =============================================================================
-- SECTION 21: DOCUMENT TEMPLATES (ID CARDS, REPORT CARDS, CERTIFICATES)
-- =============================================================================

CREATE TYPE template_type AS ENUM (
    'student_id_front', 'student_id_back',
    'staff_id_front', 'staff_id_back',
    'admit_card', 'fee_receipt', 'report_card',
    'transfer_certificate', 'bonafide_certificate',
    'character_certificate', 'payslip', 'custom'
);

CREATE TABLE document_templates (
    id              UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id       UUID            NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name            VARCHAR(100)    NOT NULL,
    template_type   template_type   NOT NULL,
    canvas_width_mm NUMERIC(6,2)    NOT NULL DEFAULT 85.6,   -- CR80 card default
    canvas_height_mm NUMERIC(6,2)   NOT NULL DEFAULT 54.0,
    layout_json     JSONB           NOT NULL DEFAULT '{}',   -- dnd-kit canvas state
    template_html   TEXT,           -- compiled Jinja2 HTML for WeasyPrint
    is_default      BOOLEAN         NOT NULL DEFAULT FALSE,
    created_by      UUID            NOT NULL REFERENCES users(id),
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);
SELECT attach_updated_at_trigger('document_templates');


-- =============================================================================
-- SECTION 22: AUDIT LOGS
-- =============================================================================

CREATE TYPE audit_action AS ENUM (
    'CREATE', 'UPDATE', 'DELETE', 'VIEW', 'EXPORT',
    'LOGIN', 'LOGOUT', 'LOGIN_FAILED', 'APPROVE', 'REJECT'
);

CREATE TABLE audit_logs (
    id              UUID            NOT NULL DEFAULT uuid_generate_v4(),
    school_id       UUID            REFERENCES schools(id),
    user_id         UUID            REFERENCES users(id),
    user_name       VARCHAR(200),   -- denormalized snapshot
    role_snapshot   VARCHAR(100),
    module          VARCHAR(60)     NOT NULL,
    action          audit_action    NOT NULL,
    record_id       UUID,
    record_type     VARCHAR(60),
    old_values      JSONB,
    new_values      JSONB,
    ip_address      INET,
    user_agent      TEXT,
    timestamp       TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id, timestamp)
)
-- Partition by month for performance at scale
PARTITION BY RANGE (timestamp);

-- Create default partition (covers all data until explicit partitions are added)
CREATE TABLE audit_logs_default PARTITION OF audit_logs DEFAULT;

-- Example monthly partitions (add via Celery/cron at start of each month):
-- CREATE TABLE audit_logs_2026_03 PARTITION OF audit_logs
--     FOR VALUES FROM ('2026-03-01') TO ('2026-04-01');


-- =============================================================================
-- SECTION 23: INDEXES
-- =============================================================================

-- ── schools ──────────────────────────────────────────────────────────────────
CREATE INDEX idx_schools_slug           ON schools (slug);

-- ── users ────────────────────────────────────────────────────────────────────
CREATE INDEX idx_users_school_id        ON users (school_id);
CREATE INDEX idx_users_email            ON users (school_id, email);
CREATE INDEX idx_users_phone            ON users (school_id, phone);
CREATE INDEX idx_users_active           ON users (school_id, is_active);
-- Enforce unique phone per school only when phone is provided (allows NULL for web-only users)
CREATE UNIQUE INDEX uq_users_phone_per_school
    ON users (school_id, phone)
    WHERE phone IS NOT NULL;

-- ── roles / permissions ──────────────────────────────────────────────────────
CREATE INDEX idx_user_roles_user        ON user_roles (user_id);
CREATE INDEX idx_user_roles_role        ON user_roles (role_id);
CREATE INDEX idx_role_perms_role        ON role_permissions (role_id);

-- ── academic_years ───────────────────────────────────────────────────────────
CREATE INDEX idx_academic_years_school  ON academic_years (school_id, is_current);

-- ── admissions ───────────────────────────────────────────────────────────────
CREATE INDEX idx_admission_forms_school_status  ON admission_forms (school_id, status);
CREATE INDEX idx_admission_forms_year           ON admission_forms (academic_year_id);

-- ── classes / sections / subjects ────────────────────────────────────────────
CREATE INDEX idx_classes_school_year    ON classes (school_id, academic_year_id);
CREATE INDEX idx_sections_class         ON sections (class_id);
CREATE INDEX idx_subjects_school        ON subjects (school_id);
CREATE INDEX idx_class_subjects_class   ON class_subjects (class_id);
CREATE INDEX idx_timetable_section_year ON timetable (section_id, academic_year_id);
CREATE INDEX idx_timetable_teacher      ON timetable (teacher_id);

-- ── staff ────────────────────────────────────────────────────────────────────
CREATE INDEX idx_staff_school_active    ON staff (school_id, is_active);
CREATE INDEX idx_staff_user             ON staff (user_id);
CREATE INDEX idx_staff_dept             ON staff (department_id);
CREATE INDEX idx_staff_leaves_staff     ON staff_leaves (staff_id, status);
CREATE INDEX idx_leave_balances_staff   ON staff_leave_balances (staff_id, academic_year_id);
CREATE INDEX idx_staff_payroll_staff    ON staff_payroll (staff_id, year, month);
CREATE INDEX idx_staff_attendance_date  ON staff_attendance (school_id, date);
CREATE INDEX idx_staff_attendance_staff ON staff_attendance (staff_id, date);

-- ── students ─────────────────────────────────────────────────────────────────
CREATE INDEX idx_students_school_active  ON students (school_id, is_active);
CREATE INDEX idx_students_admission_no   ON students (school_id, admission_number);
CREATE INDEX idx_student_enroll_student  ON student_enrollments (student_id, is_current);
CREATE INDEX idx_student_enroll_section  ON student_enrollments (section_id, academic_year_id);
CREATE INDEX idx_student_enroll_class    ON student_enrollments (class_id, academic_year_id);
CREATE INDEX idx_student_parents_student ON student_parents (student_id);
CREATE INDEX idx_student_parents_user    ON student_parents (user_id);

-- ── attendance ───────────────────────────────────────────────────────────────
CREATE INDEX idx_att_sessions_date      ON attendance_sessions (school_id, date, section_id);
CREATE INDEX idx_student_att_session    ON student_attendance (school_id, session_id);
CREATE INDEX idx_student_att_student    ON student_attendance (student_id, created_at DESC);
CREATE INDEX idx_holidays_school_date   ON holidays (school_id, date);

-- ── fees ─────────────────────────────────────────────────────────────────────
CREATE INDEX idx_fee_structures_class   ON fee_structures (school_id, academic_year_id, class_id);
CREATE INDEX idx_invoices_student       ON fee_invoices (student_id, status);
CREATE INDEX idx_invoices_due_date      ON fee_invoices (school_id, due_date, status);
CREATE INDEX idx_invoices_school_year   ON fee_invoices (school_id, academic_year_id);
CREATE INDEX idx_payments_invoice       ON fee_payments (invoice_id);
CREATE INDEX idx_payments_date          ON fee_payments (school_id, payment_date);

-- ── exams & marks ────────────────────────────────────────────────────────────
CREATE INDEX idx_exams_school_year      ON exams (school_id, academic_year_id);
CREATE INDEX idx_exams_class            ON exams (class_id, exam_type_id);
CREATE INDEX idx_student_marks_exam     ON student_marks (exam_id);
CREATE INDEX idx_student_marks_student  ON student_marks (student_id);
CREATE INDEX idx_student_marks_verified ON student_marks (exam_id, is_verified);

-- ── library ──────────────────────────────────────────────────────────────────
CREATE INDEX idx_books_school           ON books (school_id, is_active);
CREATE INDEX idx_books_isbn             ON books (school_id, isbn);
CREATE INDEX idx_book_issues_member     ON book_issues (member_id, status);
CREATE INDEX idx_book_issues_due        ON book_issues (school_id, due_date, status);
CREATE INDEX idx_library_members_user   ON library_members (school_id, user_id);

-- ── transport ────────────────────────────────────────────────────────────────
CREATE INDEX idx_vehicles_school        ON vehicles (school_id, is_active);
CREATE INDEX idx_routes_school          ON routes (school_id, is_active);
CREATE INDEX idx_stops_route            ON stops (route_id, stop_order);
CREATE INDEX idx_student_transport_yr   ON student_transport (school_id, academic_year_id);

-- ── inventory ────────────────────────────────────────────────────────────────
CREATE INDEX idx_items_school           ON items (school_id, is_active);
CREATE INDEX idx_stock_entries_item     ON stock_entries (item_id, entry_date DESC);
CREATE INDEX idx_stock_issues_item      ON stock_issues (item_id, issued_date DESC);
CREATE INDEX idx_po_school_status       ON purchase_orders (school_id, status);

-- ── accounting ───────────────────────────────────────────────────────────────
CREATE INDEX idx_income_school_year     ON income_records (school_id, academic_year_id, income_date);
CREATE INDEX idx_expense_school_year    ON expense_records (school_id, academic_year_id, expense_date);

-- ── notifications ────────────────────────────────────────────────────────────
CREATE INDEX idx_notifications_user     ON notifications (recipient_user_id, is_read, created_at DESC);
CREATE INDEX idx_notifications_school   ON notifications (school_id, created_at DESC);
CREATE INDEX idx_message_logs_bulk      ON message_logs (bulk_message_id, status);

-- ── homework ─────────────────────────────────────────────────────────────────
CREATE INDEX idx_homework_section_yr    ON homework (section_id, academic_year_id, due_date);
CREATE INDEX idx_hw_submissions_hw      ON homework_submissions (homework_id);
CREATE INDEX idx_hw_submissions_student ON homework_submissions (student_id);

-- ── calendar ─────────────────────────────────────────────────────────────────
CREATE INDEX idx_cal_events_school_yr   ON calendar_events (school_id, academic_year_id, start_datetime);

-- ── ptm ──────────────────────────────────────────────────────────────────────
CREATE INDEX idx_ptm_events_school_yr   ON ptm_events (school_id, academic_year_id, date);
CREATE INDEX idx_ptm_slots_event        ON ptm_slots (ptm_event_id, teacher_id);
CREATE INDEX idx_ptm_slots_booked       ON ptm_slots (ptm_event_id, is_booked);
CREATE INDEX idx_ptm_bookings_parent    ON ptm_bookings (parent_id, status);
CREATE INDEX idx_ptm_bookings_student   ON ptm_bookings (student_id);

-- ── audit logs ───────────────────────────────────────────────────────────────
CREATE INDEX idx_audit_school_ts        ON audit_logs (school_id, timestamp DESC);
CREATE INDEX idx_audit_user_ts          ON audit_logs (user_id, timestamp DESC);
CREATE INDEX idx_audit_module_action    ON audit_logs (module, action, timestamp DESC);


-- =============================================================================
-- SECTION 24: SEED DATA
-- =============================================================================

-- ─────────────────────────────────────────────────────────────────────────────
-- 24.1  PERMISSIONS  (full registry — one row per module × action combination)
-- ─────────────────────────────────────────────────────────────────────────────

INSERT INTO permissions (module, action, description) VALUES
-- Dashboard
('dashboard',    'view',   'View dashboard and KPIs'),

-- Schools (Super Admin only)
('schools',      'view',   'View all schools'),
('schools',      'create', 'Create a new school tenant'),
('schools',      'update', 'Update school details'),
('schools',      'delete', 'Disable a school'),
('schools',      'manage', 'Full school platform management'),

-- Users
('users',        'view',   'View user list'),
('users',        'create', 'Create a user account'),
('users',        'update', 'Update user profile'),
('users',        'delete', 'Deactivate a user'),
('users',        'export', 'Export user list'),

-- Roles & Permissions
('roles',        'view',   'View roles'),
('roles',        'create', 'Create a role'),
('roles',        'update', 'Update role and permissions'),
('roles',        'delete', 'Delete a role'),
('roles',        'manage', 'Manage permission matrix'),

-- Academic Years
('academic_years','view',  'View academic years'),
('academic_years','create','Create academic year'),
('academic_years','update','Update academic year'),
('academic_years','delete','Delete academic year'),
('academic_years','manage','Set current year, lock year'),

-- Online Admissions
('admissions',   'view',   'View admission applications'),
('admissions',   'create', 'Submit admission form (public)'),
('admissions',   'update', 'Update application'),
('admissions',   'approve','Approve or reject applications'),
('admissions',   'export', 'Export admission data'),

-- Classes & Sections
('classes',      'view',   'View classes and sections'),
('classes',      'create', 'Create class or section'),
('classes',      'update', 'Update class or section'),
('classes',      'delete', 'Delete class or section'),
('classes',      'manage', 'Assign class teachers, subjects'),

-- Subjects
('subjects',     'view',   'View subjects'),
('subjects',     'create', 'Create subject'),
('subjects',     'update', 'Update subject'),
('subjects',     'delete', 'Delete subject'),

-- Timetable
('timetable',    'view',   'View timetable'),
('timetable',    'create', 'Create timetable entries'),
('timetable',    'update', 'Update timetable'),
('timetable',    'delete', 'Delete timetable entries'),
('timetable',    'export', 'Export timetable PDF'),

-- Staff
('staff',        'view',   'View staff list and profiles'),
('staff',        'create', 'Add new staff'),
('staff',        'update', 'Update staff profile'),
('staff',        'delete', 'Deactivate staff'),
('staff',        'export', 'Export staff data'),
('staff',        'manage', 'Manage departments, designations'),

-- Leave Management
('leaves',       'view',   'View leave requests'),
('leaves',       'create', 'Apply for leave'),
('leaves',       'update', 'Update leave request'),
('leaves',       'approve','Approve or reject leaves'),
('leaves',       'export', 'Export leave report'),

-- Payroll
('payroll',      'view',   'View payroll records'),
('payroll',      'create', 'Create payroll entries'),
('payroll',      'update', 'Update payroll'),
('payroll',      'approve','Mark salary as paid'),
('payroll',      'export', 'Export payroll / payslip'),

-- Students
('students',     'view',   'View student list and profiles'),
('students',     'create', 'Enroll a new student'),
('students',     'update', 'Update student profile'),
('students',     'delete', 'Deactivate student'),
('students',     'export', 'Export student data'),
('students',     'manage', 'Promote, transfer students'),

-- Attendance
('attendance',   'view',   'View attendance records'),
('attendance',   'create', 'Mark attendance'),
('attendance',   'update', 'Edit attendance record'),
('attendance',   'export', 'Export attendance reports'),

-- Fees
('fees',         'view',   'View fee records'),
('fees',         'create', 'Create fee structure / invoice'),
('fees',         'update', 'Update fee records'),
('fees',         'delete', 'Waive or cancel invoice'),
('fees',         'approve','Collect / approve payment'),
('fees',         'export', 'Export fee reports'),

-- Exams
('exams',        'view',   'View exam schedule and results'),
('exams',        'create', 'Create exam'),
('exams',        'update', 'Update exam'),
('exams',        'delete', 'Delete exam'),
('exams',        'approve','Verify marks, publish results'),
('exams',        'export', 'Export result sheets / report cards'),

-- Library
('library',      'view',   'View library records'),
('library',      'create', 'Add books, issue books'),
('library',      'update', 'Update book / issue records'),
('library',      'delete', 'Remove books'),
('library',      'export', 'Export library reports'),

-- Transport
('transport',    'view',   'View transport records'),
('transport',    'create', 'Add vehicles, routes, stops'),
('transport',    'update', 'Update transport records'),
('transport',    'delete', 'Remove transport records'),
('transport',    'export', 'Export transport reports'),

-- Inventory
('inventory',    'view',   'View inventory'),
('inventory',    'create', 'Add items, stock entries'),
('inventory',    'update', 'Update inventory'),
('inventory',    'delete', 'Remove inventory items'),
('inventory',    'approve','Approve purchase orders'),
('inventory',    'export', 'Export stock register'),

-- Accounting
('accounting',   'view',   'View income and expense records'),
('accounting',   'create', 'Record income or expense'),
('accounting',   'update', 'Update financial records'),
('accounting',   'delete', 'Delete financial records'),
('accounting',   'export', 'Export accounting reports'),

-- Communication
('communication','view',   'View notifications and announcements'),
('communication','create', 'Create notifications and announcements'),
('communication','update', 'Edit notification templates'),
('communication','delete', 'Delete announcements'),
('communication','manage', 'Send bulk messages'),

-- Calendar
('calendar',     'view',   'View calendar events'),
('calendar',     'create', 'Create calendar events'),
('calendar',     'update', 'Update calendar events'),
('calendar',     'delete', 'Delete calendar events'),

-- Homework
('homework',     'view',   'View homework'),
('homework',     'create', 'Assign homework'),
('homework',     'update', 'Update homework'),
('homework',     'delete', 'Delete homework'),

-- PTM
('ptm',          'view',   'View PTM events and bookings'),
('ptm',          'create', 'Create PTM events'),
('ptm',          'update', 'Update PTM events'),
('ptm',          'delete', 'Cancel PTM events'),
('ptm',          'approve','Mark PTM meetings completed'),

-- Reports
('reports',      'view',   'View reports'),
('reports',      'export', 'Export reports to PDF/Excel'),

-- Audit Logs
('audit_logs',   'view',   'View audit logs'),
('audit_logs',   'export', 'Export audit logs'),

-- Settings
('settings',     'view',   'View school settings'),
('settings',     'update', 'Update school settings'),
('settings',     'manage', 'Manage integrations and security');


-- ─────────────────────────────────────────────────────────────────────────────
-- 24.2  PLATFORM-LEVEL ROLES  (school_id = NULL → Super Admin only)
-- ─────────────────────────────────────────────────────────────────────────────

INSERT INTO roles (id, school_id, name, slug, description, is_system, is_active) VALUES
(uuid_generate_v4(), NULL, 'Super Admin', 'super_admin',
 'Platform-level administrator with full access to all schools', TRUE, TRUE);

-- Grant all permissions to Super Admin
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM   roles r
CROSS  JOIN permissions p
WHERE  r.slug = 'super_admin';


-- ─────────────────────────────────────────────────────────────────────────────
-- 24.3  SCHOOL-LEVEL SYSTEM ROLES TEMPLATE
--       These are cloned into each school when it is created.
--       Represented here as a reference; the application's school-onboarding
--       service inserts them with the correct school_id.
--       The seed below uses a placeholder school_id = '00000000-0000-0000-0000-000000000001'
--       as documentation only — replace in actual onboarding.
-- ─────────────────────────────────────────────────────────────────────────────

-- Role definitions (stored as reference data in a separate lookup, not real rows)
-- APPLICATION CODE should call seed_school_roles(school_id) on school creation.
-- Each school gets these system roles:
--
--   slug                | Typical permissions
--   --------------------|--------------------------------------------------
--   school_admin        | All modules: manage
--   principal           | All modules: view/export + attendance:create + exams:approve
--   vice_principal      | Same as principal
--   teacher             | timetable:view, attendance:create, homework:create/update,
--                       | exams:create/update, students:view
--   class_teacher       | teacher + students:manage (own section)
--   accountant          | fees:*, payroll:*, accounting:*, reports:export
--   librarian           | library:*, reports:view
--   transport_manager   | transport:*, reports:view
--   inventory_manager   | inventory:*, reports:view
--   receptionist        | students:view/create, admissions:view/approve,
--                       | communication:create
--   parent              | dashboard:view, students:view (own children),
--                       | attendance:view, fees:view, exams:view,
--                       | homework:view, library:view, transport:view,
--                       | ptm:view/create, communication:view
--   student             | dashboard:view, attendance:view, exams:view,
--                       | homework:view/update, timetable:view,
--                       | communication:view


-- ─────────────────────────────────────────────────────────────────────────────
-- 24.4  DEFAULT PERMISSION SETS PER ROLE  (inserts for reference school)
--       For brevity, the School Admin role receives ALL permissions.
--       All others receive a curated subset as described above.
--       The application expands this logic per school on onboarding.
-- ─────────────────────────────────────────────────────────────────────────────

-- Leave_types seed (commonly used across all schools)
-- Inserted by the app during school onboarding with correct school_id:
--   Casual Leave      — 12 days/year, paid
--   Sick Leave        — 12 days/year, paid
--   Earned Leave      — 15 days/year, paid
--   Maternity Leave   — 180 days, paid
--   Paternity Leave   — 15 days, paid
--   Unpaid Leave      — unlimited, unpaid
--   Compensatory Off  — as earned, paid


-- ─────────────────────────────────────────────────────────────────────────────
-- 24.5  DEFAULT SCHOOL SETTINGS
--       Inserted by application on school creation with correct school_id.
--       Listed here for documentation.
-- ─────────────────────────────────────────────────────────────────────────────

-- category     | key                           | default_value  | data_type
-- -------------|-------------------------------|----------------|----------
-- general      | academic_start_month          | 4              | integer
-- general      | timezone                      | Asia/Kolkata   | string
-- general      | currency                      | INR            | string
-- general      | date_format                   | DD/MM/YYYY     | string
-- admission    | admission_number_prefix        | STU            | string
-- admission    | admission_number_start         | 1001           | integer
-- admission    | admission_number_format        | {PREFIX}-{YEAR}-{SEQ:04d} | string
-- attendance   | working_days                  | [1,2,3,4,5]    | json
-- attendance   | sessions_enabled              | full_day       | string
-- attendance   | low_attendance_threshold_pct  | 75             | integer
-- attendance   | absent_notify_delay_minutes   | 30             | integer
-- attendance   | notify_parents_sms            | true           | boolean
-- attendance   | notify_parents_whatsapp       | true           | boolean
-- fees         | fine_enabled                  | true           | boolean
-- fees         | fine_per_day_paise            | 0              | integer
-- fees         | receipt_number_prefix         | RCP            | string
-- fees         | due_reminder_days_before      | 3              | integer
-- library      | max_books_student             | 3              | integer
-- library      | max_books_staff               | 5              | integer
-- library      | default_loan_days             | 14             | integer
-- library      | fine_per_day_overdue_paise    | 100            | integer  (₹1/day)
-- exam         | default_pass_percentage       | 35             | integer
-- exam         | result_sms_on_publish         | true           | boolean
-- security     | password_min_length           | 8              | integer
-- security     | session_timeout_minutes       | 60             | integer
-- security     | max_login_attempts            | 5              | integer
-- security     | lockout_duration_minutes      | 15             | integer
-- security     | tfa_enabled                   | false          | boolean


-- ─────────────────────────────────────────────────────────────────────────────
-- 24.6  NOTIFICATION TEMPLATES  (default set for every school)
--       school_id replaced with actual value on school onboarding.
-- ─────────────────────────────────────────────────────────────────────────────

-- event_trigger            | subject                       | body (variables in {})
-- -------------------------|-------------------------------|-------------------
-- STUDENT_ABSENT           | Attendance Alert              | Dear {parent_name}, your ward {student_name} of {class} {section} was marked ABSENT on {date}. Please contact the school if this is incorrect.
-- FEE_DUE                  | Fee Due Reminder              | Dear {parent_name}, fee of ₹{amount} for {student_name} is due on {due_date}. Please pay to avoid late fine. Invoice: {invoice_number}.
-- FEE_PAID                 | Fee Payment Confirmed         | Dear {parent_name}, payment of ₹{amount} received for {student_name} on {date}. Receipt No: {receipt_number}. Thank you.
-- FEE_OVERDUE              | Fee Overdue Notice            | Dear {parent_name}, fee of ₹{amount} for {student_name} is overdue since {due_date}. A fine of ₹{fine_amount} has been applied. Please clear dues immediately.
-- RESULT_PUBLISHED         | Exam Results Published        | Dear {parent_name}, results for {exam_name} of {student_name} have been published. Log in to the parent portal to view.
-- EXAM_SCHEDULED           | Exam Schedule Notice          | Dear {parent_name}, {student_name}'s {exam_name} exams are scheduled from {start_date} to {end_date}. Please collect the admit card from school.
-- HOMEWORK_ASSIGNED        | New Homework Assigned         | {student_name}, {subject} homework has been assigned by {teacher_name}. Due date: {due_date}. Log in to view details.
-- LEAVE_APPROVED           | Leave Request Approved        | Dear {staff_name}, your leave request from {from_date} to {to_date} has been APPROVED by {approver_name}.
-- LEAVE_REJECTED           | Leave Request Rejected        | Dear {staff_name}, your leave request from {from_date} to {to_date} has been REJECTED. Reason: {reason}.
-- LIBRARY_OVERDUE          | Library Book Overdue          | Dear {member_name}, the book "{book_title}" was due on {due_date}. A fine of ₹{fine_amount} is accruing. Please return it immediately.
-- LOW_ATTENDANCE_WARNING   | Low Attendance Warning        | Dear {parent_name}, {student_name}'s attendance has fallen to {attendance_pct}%, which is below the required {threshold_pct}%. Please ensure regular attendance.
-- ADMISSION_APPROVED       | Admission Approved            | Dear {applicant_name}, congratulations! Your admission application (Ref: {reference_number}) has been approved. Admission No: {admission_number}. Please report to school on {joining_date}.
-- PTM_BOOKED               | PTM Slot Confirmed            | Dear {parent_name}, your PTM slot with {teacher_name} on {date} at {time} has been confirmed. Please be on time.
-- PTM_REMINDER             | PTM Reminder                  | Dear {parent_name}, reminder: your PTM appointment with {teacher_name} is tomorrow at {time}. Venue: {venue}.
-- ANNOUNCEMENT_PUBLISHED   | New Announcement              | {title}: {summary}. Log in to the portal to read the full announcement.


-- ─────────────────────────────────────────────────────────────────────────────
-- 24.7  SUPER ADMIN USER (change password immediately after first login)
-- ─────────────────────────────────────────────────────────────────────────────

INSERT INTO users (
    id, school_id, username, email, phone,
    password_hash, is_active, is_verified, is_super_admin
) VALUES (
    uuid_generate_v4(),
    NULL,
    'superadmin',
    'admin@sms.local',
    NULL,
    -- bcrypt hash of 'Admin@1234' — CHANGE ON FIRST LOGIN
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQyCKzQVeqmCpNM7dWPkLHNOi',
    TRUE,
    TRUE,
    TRUE
);

-- Assign Super Admin role to this user
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id
FROM   users u
CROSS  JOIN roles r
WHERE  u.username = 'superadmin'
  AND  r.slug     = 'super_admin'
  AND  r.school_id IS NULL;


-- ─────────────────────────────────────────────────────────────────────────────
-- 24.8  DEFAULT GRADING SCALE (CBSE-style 10-point; cloned per school)
-- ─────────────────────────────────────────────────────────────────────────────
-- Inserted by application with correct school_id on school creation.
-- JSON structure:
-- [
--   {"min_pct":  0, "max_pct": 32, "grade": "F",   "gpa": 0.0, "description": "Fail"},
--   {"min_pct": 33, "max_pct": 44, "grade": "E",   "gpa": 2.0, "description": "Below Average"},
--   {"min_pct": 45, "max_pct": 54, "grade": "D",   "gpa": 4.0, "description": "Average"},
--   {"min_pct": 55, "max_pct": 64, "grade": "C",   "gpa": 6.0, "description": "Above Average"},
--   {"min_pct": 65, "max_pct": 74, "grade": "B",   "gpa": 7.0, "description": "Good"},
--   {"min_pct": 75, "max_pct": 84, "grade": "B+",  "gpa": 8.0, "description": "Very Good"},
--   {"min_pct": 85, "max_pct": 90, "grade": "A",   "gpa": 9.0, "description": "Excellent"},
--   {"min_pct": 91, "max_pct":100, "grade": "A+",  "gpa":10.0, "description": "Outstanding"}
-- ]


-- ─────────────────────────────────────────────────────────────────────────────
-- 24.9  INVENTORY CATEGORIES (default; cloned per school)
-- ─────────────────────────────────────────────────────────────────────────────
-- Inserted by application with correct school_id on school creation:
--   Stationery | Lab Equipment | Sports Equipment | Furniture |
--   Electronics | Cleaning Supplies | Library Books | Uniform | Others


-- ─────────────────────────────────────────────────────────────────────────────
-- 24.10  INCOME & EXPENSE CATEGORIES (default; cloned per school)
-- ─────────────────────────────────────────────────────────────────────────────
-- INCOME:  Fee Collection | Government Grant | Donation | Canteen | Event |
--          Transport Fees | Other Income
-- EXPENSE: Staff Salaries | Utilities | Maintenance | Stationery |
--          Lab Expenses | Sports | Events | Rent | Marketing | Miscellaneous


-- ─────────────────────────────────────────────────────────────────────────────
-- 24.11  HOLIDAY TYPES (enum — already embedded in DDL)
-- ─────────────────────────────────────────────────────────────────────────────
-- national | state | school | religious | other


-- ─────────────────────────────────────────────────────────────────────────────
-- END OF SCHEMA
-- ─────────────────────────────────────────────────────────────────────────────
-- Table count : ~67 tables  (added: staff_leave_balances)
-- Index count : ~70 indexes  (added: phone uniqueness, ptm, leave_balances)
-- Enum types  : 22
-- Seed rows   : permissions (~100), super admin (1 user + role assignment)
-- Fixes applied (v2):
--   • academic_terms  — added CHECK (end_date > start_date)
--   • admission_forms — reference_number UNIQUE now school-scoped
--   • student_transfers — transfer_certificate_no UNIQUE now school-scoped
--   • ptm_slots       — added UNIQUE (ptm_event_id, teacher_id, slot_start)
--   • stock_entries   — total_price GENERATED column fixed (NUMERIC, no ROUND cast error)
--   • vehicles        — driver_id / conductor_id FK now ON DELETE SET NULL
--   • student_enrollments — roll_number VARCHAR(20) (was SMALLINT; supports alphanumeric)
--   • departments/designations     — added updated_at + trigger
--   • fee_categories/fee_discounts  — added updated_at + trigger
--   • student_fee_assignments       — added updated_at + trigger
--   • fine_configurations           — added updated_at + trigger
--   • staff_attendance              — added updated_at + trigger
--   • student_attendance            — added updated_at + trigger
--   • student_marks  — added verified_at timestamp column
--   • purchase_order_items — added received_quantity + received_at for partial delivery
--   • announcements  — target_audience now has CHECK constraint (enum-like safety)
--   • budget_heads    — documented polymorphic category_id (app-level enforcement)
--   • staff_leave_balances — new table for leave balance tracking (Phase 6)
--   • users           — added partial UNIQUE index on (school_id, phone) WHERE NOT NULL
--   • ptm indexes     — added 5 targeted PTM performance indexes
-- =============================================================================
