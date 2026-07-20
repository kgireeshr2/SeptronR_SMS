# SeptroSchool — Architecture Diagrams

---

## 1. System Overview (Infrastructure Layer)

```mermaid
graph TB
    subgraph CLIENT["Client Layer"]
        B["Browser / PWA\n(React + TypeScript)"]
        M["Mobile Browser\n(PWA Installable)"]
    end

    subgraph NGINX["Reverse Proxy"]
        N["Nginx\n• SSL Termination (Let's Encrypt)\n• Gzip Compression\n• Rate Limiting\n• Security Headers\n• Static File Serving"]
    end

    subgraph BACKEND["Backend Services (Docker Compose)"]
        API["FastAPI\n(uvicorn --workers 4)\nAsync HTTP + WebSocket"]
        CW["Celery Worker\n(concurrency=4)\nBackground Tasks"]
        CB["Celery Beat\nScheduled Jobs\n(cron-like)"]
        FL["Flower\nCelery Monitor UI"]
    end

    subgraph DATA["Data Layer"]
        PG[("PostgreSQL 15\nPrimary Database\n+ pgBouncer Pool")]
        RD[("Redis 7\n• Task Queue (Celery broker)\n• Result Backend\n• Cache (TTL 5 min)\n• Token Blacklist\n• OTP Store")]
    end

    subgraph STORAGE["File Storage"]
        S3["AWS S3 / MinIO\n• Student Photos\n• Staff Photos\n• Documents\n• Generated PDFs"]
    end

    subgraph EXTERNAL["External Services"]
        SMS["SMS Gateway\nTwilio / MSG91"]
        WA["WhatsApp\nMeta Cloud API"]
        EM["Email\nSMTP / SendGrid"]
        FCM["Push Notifications\nFirebase FCM"]
        PG2["Payment Gateway\nRazorpay / Stripe"]
        GPS["GPS Tracking\n3rd-party API"]
    end

    B & M --> N
    N -->|"HTTP /api/v1/*"| API
    N -->|"WS /ws/*"| API
    N -->|Static files| N
    API <-->|"Async queries"| PG
    API <-->|"Cache / Pub-Sub"| RD
    API -->|"Enqueue tasks"| RD
    CW <-->|"Dequeue tasks"| RD
    CW <-->|"DB writes"| PG
    CW -->|"Send SMS"| SMS
    CW -->|"Send WhatsApp"| WA
    CW -->|"Send Email"| EM
    CW -->|"Push notification"| FCM
    CW -->|"Upload files"| S3
    CB -->|"Scheduled tasks"| RD
    API <-->|"File upload/read"| S3
    API -->|"Payment webhook"| PG2
    API -->|"GPS data poll"| GPS
    FL -->|"Monitor"| CW & CB
```

---

## 2. Backend Application Layer Architecture

```mermaid
graph LR
    subgraph REQUEST["Incoming Request"]
        REQ["HTTP Request\n/api/v1/students"]
    end

    subgraph MIDDLEWARE["Middleware Stack (LIFO)"]
        MW1["GZip Middleware"]
        MW2["CORS Middleware"]
        MW3["Request Logger"]
        MW4["School Context\nExtractor\n(subdomain / JWT)"]
    end

    subgraph AUTH["Auth / Security Layer"]
        JWT["JWT Dependency\nget_current_user()"]
        PERM["Permission Dependency\npermission_required(\n  module, action\n)"]
    end

    subgraph ROUTES["API Routes\n/app/api/v1/"]
        R1["students.py"]
        R2["fees.py"]
        R3["attendance.py"]
        R4["exams.py"]
        R5["auth.py"]
        RN["... (one file\nper module)"]
    end

    subgraph SCHEMAS["Pydantic v2 Schemas\n/app/schemas/"]
        SC["Request validation\nResponse serialization\ncamelCase output"]
    end

    subgraph SERVICES["Service Layer\n/app/services/"]
        SV["Business Logic\n• Fee calculation\n• Rank computation\n• Promotion logic\n• PDF generation\n• Audit log calls"]
    end

    subgraph REPO["Repository Layer\n/app/repositories/"]
        RP["Database Queries\n• SQLAlchemy async\n• selectinload / joinedload\n• Pagination helpers\n• Soft-delete filters"]
    end

    subgraph TASKS["Celery Tasks\n/app/tasks/"]
        TK["Async Jobs\n• Send SMS/Email/WhatsApp\n• Generate PDF reports\n• Invoice generation\n• Low stock alerts\n• Audit log retention"]
    end

    subgraph DB["Data Layer"]
        PG[("PostgreSQL")]
        RD[("Redis")]
    end

    REQ --> MW1 --> MW2 --> MW3 --> MW4
    MW4 --> JWT --> PERM
    PERM --> ROUTES
    ROUTES --> SC
    SC --> SERVICES
    SERVICES --> REPO
    SERVICES --> TASKS
    REPO --> PG
    TASKS --> RD
    TASKS --> PG
```

---

## 3. Multi-Tenant Architecture

```mermaid
graph TB
    subgraph DNS["DNS / Routing"]
        S1["school-a.sms.com"]
        S2["school-b.sms.com"]
        S3["admin.sms.com"]
    end

    subgraph NGINX2["Nginx"]
        NX["Extracts subdomain\nPasses X-School-Slug header"]
    end

    subgraph FASTAPI["FastAPI Middleware"]
        CTX["SchoolContextMiddleware\n1. Read subdomain / JWT claim\n2. Resolve school_id from DB\n3. Set request.state.school_id"]
    end

    subgraph SCOPE["All Queries Scoped"]
        Q1["SELECT * FROM students\nWHERE school_id = :school_id"]
        Q2["SELECT * FROM staff\nWHERE school_id = :school_id"]
        Q3["SELECT * FROM fee_invoices\nWHERE school_id = :school_id"]
    end

    subgraph ROLES["Role Hierarchy"]
        SA["Super Admin\n(no school_id scope)\nManages ALL schools"]
        SCHA["School Admin\nscoped to own school_id"]
        PRIN["Principal / VP\nscoped to own school_id"]
        TCH["Teacher\nscoped to own school_id\n+ own sections only"]
        PRNT["Parent\nscoped to own children only"]
        STD["Student\nscoped to own records only"]
    end

    subgraph DB2["Single Shared Database"]
        TBL["All tables include school_id FK\nDB-level row isolation\n(no separate schemas)"]
    end

    S1 & S2 & S3 --> NX --> CTX
    CTX --> Q1 & Q2 & Q3
    Q1 & Q2 & Q3 --> TBL
    SA -->|"bypass school filter"| TBL
    SCHA & PRIN & TCH & PRNT & STD -->|"auto-scoped by middleware"| CTX
```

---

## 4. Authentication & Authorization Flow

```mermaid
sequenceDiagram
    actor User
    participant FE as React Frontend
    participant API as FastAPI /api/v1/auth
    participant RD as Redis
    participant DB as PostgreSQL

    Note over User,DB: USERNAME / PASSWORD LOGIN
    User->>FE: Enter credentials
    FE->>API: POST /auth/login {username, password}
    API->>DB: Fetch user by email/username
    DB-->>API: user record
    API->>API: bcrypt verify password
    API->>API: Generate access JWT (15 min) + refresh JWT (7 days)
    API-->>FE: {accessToken, refreshToken, user, permissions}
    FE->>FE: Store in Zustand (memory) + refreshToken in httpOnly cookie

    Note over User,DB: OTP / PHONE LOGIN (Parents)
    User->>FE: Enter phone number
    FE->>API: POST /auth/send-otp {phone}
    API->>RD: Store OTP (TTL 5 min, rate-limit 1/min per phone)
    API->>API: Send SMS via Twilio/MSG91 (Celery task)
    User->>FE: Enter 6-digit OTP
    FE->>API: POST /auth/verify-otp {phone, otp}
    API->>RD: Verify OTP + delete on success
    API-->>FE: {accessToken, refreshToken, user, permissions}

    Note over User,DB: TOKEN REFRESH
    FE->>API: POST /auth/refresh (cookie: refreshToken)
    API->>RD: Check token NOT in blacklist
    RD-->>API: OK
    API->>API: Issue new accessToken
    API-->>FE: {accessToken}

    Note over User,DB: PROTECTED REQUEST
    FE->>API: GET /api/v1/students [Authorization: Bearer <accessToken>]
    API->>API: Decode JWT → extract user_id, school_id, jti
    API->>DB: Load user roles + permissions
    API->>API: permission_required("students","view") ✓
    API-->>FE: student list

    Note over User,DB: LOGOUT
    FE->>API: POST /auth/logout
    API->>RD: Blacklist refresh token JTI (TTL = token expiry)
    API-->>FE: 200 OK
```

---

## 5. Database Entity Relationship (Core Tables)

```mermaid
erDiagram
    schools {
        uuid id PK
        string name
        string slug
        bool is_active
    }

    users {
        uuid id PK
        uuid school_id FK
        string username
        string email
        string phone
        string password_hash
        string otp_secret
        bool is_active
        bool is_verified
        timestamp last_login
        timestamp created_at
        timestamp updated_at
    }

    roles {
        uuid id PK
        uuid school_id FK
        string name
        string slug
        bool is_system
        bool is_active
    }

    user_roles {
        uuid user_id FK
        uuid role_id FK
    }

    permissions {
        uuid id PK
        string module
        string action
    }

    role_permissions {
        uuid role_id FK
        uuid permission_id FK
    }

    academic_years {
        uuid id PK
        uuid school_id FK
        string name
        date start_date
        date end_date
        bool is_current
        bool is_locked
    }

    classes {
        uuid id PK
        uuid school_id FK
        uuid academic_year_id FK
        string name
        int numeric_level
        bool is_active
    }

    sections {
        uuid id PK
        uuid class_id FK
        string name
        int capacity
        uuid class_teacher_id FK
        string room_number
        bool is_active
    }

    students {
        uuid id PK
        uuid school_id FK
        string admission_number UK
        uuid user_id FK
        string first_name
        string last_name
        date date_of_birth
        string gender
        string photo_url
        bool is_active
        timestamp created_at
        timestamp updated_at
    }

    student_enrollments {
        uuid id PK
        uuid student_id FK
        uuid academic_year_id FK
        uuid class_id FK
        uuid section_id FK
        int roll_number
        bool is_current
    }

    staff {
        uuid id PK
        uuid school_id FK
        string employee_id UK
        uuid user_id FK
        string first_name
        string last_name
        string department
        string designation
        bool is_active
    }

    fee_invoices {
        uuid id PK
        uuid school_id FK
        uuid student_id FK
        uuid academic_year_id FK
        string invoice_number
        date due_date
        string status
        int total_amount
        int paid_amount
        int balance_amount
    }

    fee_payments {
        uuid id PK
        uuid invoice_id FK
        int amount
        date payment_date
        string payment_method
        string receipt_number
        uuid collected_by FK
    }

    student_attendance {
        uuid id PK
        uuid school_id FK
        uuid session_id FK
        uuid student_id FK
        string status
        timestamp notified_at
    }

    exams {
        uuid id PK
        uuid school_id FK
        uuid exam_type_id FK
        uuid class_id FK
        uuid subject_id FK
        date exam_date
        int total_marks
        int pass_marks
        bool is_published
    }

    student_marks {
        uuid id PK
        uuid exam_id FK
        uuid student_id FK
        float marks_obtained
        string grade
        bool is_absent
        bool is_verified
    }

    audit_logs {
        uuid id PK
        uuid school_id FK
        uuid user_id FK
        string module
        string action
        uuid record_id
        json old_values
        json new_values
        string ip_address
        timestamp timestamp
    }

    schools ||--o{ users : "has"
    schools ||--o{ roles : "has"
    schools ||--o{ academic_years : "has"
    schools ||--o{ students : "enrolls"
    schools ||--o{ staff : "employs"
    users ||--o{ user_roles : "assigned"
    roles ||--o{ user_roles : "assigned to"
    roles ||--o{ role_permissions : "has"
    permissions ||--o{ role_permissions : "grants"
    students ||--o{ student_enrollments : "enrolled in"
    academic_years ||--o{ student_enrollments : "scopes"
    classes ||--o{ student_enrollments : "contains"
    sections ||--o{ student_enrollments : "contains"
    students ||--o{ fee_invoices : "billed"
    fee_invoices ||--o{ fee_payments : "paid via"
    students ||--o{ student_attendance : "tracked"
    students ||--o{ student_marks : "graded"
    exams ||--o{ student_marks : "records"
    schools ||--o{ audit_logs : "logged"
```

---

## 6. Frontend Application Architecture

```mermaid
graph TB
    subgraph ENTRY["Entry Point"]
        VITE["Vite Build\nmain.tsx"]
    end

    subgraph PROVIDERS["Provider Tree"]
        QC["TanStack Query\nQueryClientProvider\n(global error handler)"]
        RR["React Router v6\nBrowserRouter"]
        ZS["Zustand Stores\n(no Provider needed)"]
    end

    subgraph GUARDS["Route Guards"]
        PV["PrivateRoute\n• Check auth store\n• Redirect to /login if unauthenticated"]
        RG["RoleGuard\n• Check role → redirect to\n  correct dashboard"]
        PG["PermissionGuard\n• hasPermission(module, action)\n• Hide/show UI elements"]
    end

    subgraph LAYOUT["Shared Layout"]
        NAV["Top Navbar\n• Academic Year selector\n• Bell icon (notifications)\n• User avatar menu"]
        SB["Sidebar\n• Role-adaptive menu items\n• Permission-gated links"]
        EB["Error Boundary\n• Layout-level catch\n• Toast error fallback"]
    end

    subgraph PAGES["Page Modules (React.lazy)"]
        P1["Dashboard"]
        P2["Students"]
        P3["Staff"]
        P4["Attendance"]
        P5["Fees"]
        P6["Exams"]
        P7["Library"]
        P8["Transport"]
        P9["Inventory"]
        P10["Accounting"]
        P11["Communication"]
        P12["Reports"]
        P13["Settings"]
        P14["Audit Logs"]
        P15["Parent Portal"]
        P16["Student Portal"]
    end

    subgraph STATE["State Management"]
        ZSA["Auth Store (Zustand)\n• accessToken\n• refreshToken\n• currentUser\n• schoolInfo\n• permissions[]"]
        ZSN["Notification Store\n• unread count\n• recent notifications"]
        ZSY["AcademicYear Store\n• selectedYear\n• years[]"]
    end

    subgraph DATA_FETCH["Data Fetching (TanStack Query)"]
        HOOKS["Custom Hooks\nuseStudents()\nuseFees()\nuseAttendance()\n(etc. per module)"]
        AXIOS["Axios Instance\n• Attach Bearer token\n• Auto-refresh on 401\n• Response envelope unwrap"]
        APIFN["API Functions\n/src/api/*.ts\n(one file per module)"]
    end

    subgraph RT["Real-time"]
        WS["WebSocket\nwss://api/ws\n• Notification push\n• Bell count update"]
    end

    VITE --> QC --> RR --> GUARDS
    GUARDS --> LAYOUT
    LAYOUT --> PAGES
    PAGES --> HOOKS
    HOOKS --> APIFN --> AXIOS
    PAGES --> STATE
    WS --> ZSN
    ZSA --> AXIOS
```

---

## 7. Celery Background Job Architecture

```mermaid
graph LR
    subgraph TRIGGERS["Task Triggers"]
        T1["Attendance marked\n→ absent parent notify"]
        T2["Payment recorded\n→ receipt PDF + WhatsApp"]
        T3["Result published\n→ SMS to parents"]
        T4["Celery Beat (cron)\n→ daily/weekly jobs"]
        T5["Manual action\n→ bulk message send"]
        T6["Report requested\n→ PDF/Excel generation"]
    end

    subgraph BROKER["Redis (Broker)"]
        Q1["Queue: notifications\n(high priority)"]
        Q2["Queue: reports\n(low priority)"]
        Q3["Queue: emails\n(medium priority)"]
        Q4["Queue: scheduled\n(beat jobs)"]
    end

    subgraph WORKERS["Celery Workers"]
        W1["Worker 1-2\nNotifications queue"]
        W2["Worker 3\nReports queue"]
        W3["Worker 4\nEmails + scheduled"]
    end

    subgraph JOBS["Scheduled Jobs (Beat)"]
        J1["Daily 7 AM\nGenerate monthly invoices"]
        J2["Daily 8 AM\nFee due reminders (N days prior)"]
        J3["Daily 9 AM\nLibrary overdue alerts"]
        J4["Hourly\nLow stock alerts"]
        J5["Weekly\nPayroll reminders"]
        J6["Monthly\nAudit log retention cleanup"]
        J7["Monthly\nDB backup to S3"]
    end

    subgraph CHANNELS["Notification Channels"]
        CH1["SMS\nTwilio / MSG91"]
        CH2["WhatsApp\nMeta Cloud API"]
        CH3["Email\nSMTP / SendGrid"]
        CH4["FCM Push"]
        CH5["In-App\nWebSocket Pub/Sub via Redis"]
    end

    T1 & T2 & T3 & T5 --> Q1
    T6 --> Q2
    T5 --> Q3
    J1 & J2 & J3 & J4 & J5 & J6 & J7 --> Q4
    T4 --> Q4

    Q1 --> W1
    Q2 --> W2
    Q3 & Q4 --> W3

    W1 & W2 & W3 --> CH1 & CH2 & CH3 & CH4 & CH5
```

---

## 8. Request Lifecycle (End-to-End)

```mermaid
sequenceDiagram
    actor User
    participant FE as React Page
    participant AX as Axios Interceptor
    participant NG as Nginx
    participant MW as FastAPI Middleware
    participant AUTH as Auth Dependency
    participant ROUTE as Route Handler
    participant SVC as Service Layer
    participant REPO as Repository
    participant PG as PostgreSQL
    participant RD as Redis
    participant TK as Celery Task

    User->>FE: Click "Mark Attendance"
    FE->>FE: React Hook Form validate via Zod schema
    FE->>AX: POST /api/v1/attendance/sessions (payload)
    AX->>AX: Attach Authorization: Bearer <accessToken>
    AX->>NG: HTTPS Request
    NG->>NG: Rate limit check, gzip, security headers
    NG->>MW: Forward to FastAPI
    MW->>MW: GZip → CORS → RequestLogger → SchoolContext
    MW->>AUTH: get_current_user() verifies JWT
    AUTH->>RD: Check JTI not blacklisted
    RD-->>AUTH: OK
    AUTH->>AUTH: permission_required("attendance","create") ✓
    AUTH->>ROUTE: Inject current_user, school_id
    ROUTE->>ROUTE: Validate Pydantic schema
    ROUTE->>SVC: attendance_service.mark_session(data)
    SVC->>REPO: attendance_repo.create_session()
    REPO->>PG: INSERT attendance_sessions
    PG-->>REPO: session record
    REPO->>PG: BULK INSERT student_attendance rows
    PG-->>REPO: rows
    SVC->>SVC: log_audit("CREATE","attendance",...)
    SVC->>REPO: audit_repo.create(audit_log)
    REPO->>PG: INSERT audit_logs
    SVC->>TK: enqueue notify_absent_parents.delay(absent_ids)
    TK->>RD: Push to notifications queue
    SVC-->>ROUTE: session_id, stats
    ROUTE-->>AX: 201 {success:true, data:{...}, message:"Attendance saved"}
    AX->>AX: Unwrap response envelope
    AX-->>FE: session data
    FE->>FE: TanStack Query invalidate ["attendance"]
    FE->>User: Toast "Attendance saved" + table refreshes

    Note over TK,PG: Async (background)
    TK->>PG: Fetch absent student → parent contacts
    TK->>TK: Send SMS + WhatsApp per parent
    TK->>PG: UPDATE student_attendance.notified_at
```

---

## 9. Module Dependency Map

```mermaid
graph TD
    INFRA["Infrastructure\n(Docker, DB, Redis)"]
    AUTH["Auth & Users\n(JWT, OTP)"]
    ROLES["Roles &\nPermissions"]
    SETTINGS["School Settings\n& Academic Year"]
    ADMISSIONS["Online\nAdmissions"]
    CLASSES["Classes, Sections\n& Subjects"]
    STAFF["Staff\nManagement"]
    STUDENTS["Student\nManagement"]
    ENROLL["Student\nEnrollments"]
    ATTEND["Attendance"]
    FEES["Fee\nManagement"]
    EXAMS["Exam\nManagement"]
    LIBRARY["Library"]
    TRANSPORT["Transport"]
    INVENTORY["Inventory"]
    ACCOUNTING["Income &\nExpense"]
    COMMS["Communication\n& Notifications"]
    CALENDAR["Calendar"]
    HOMEWORK["Homework &\nLesson Plans"]
    PTM["PTM\nScheduling"]
    TEMPLATES["ID Card /\nTemplate Builder"]
    REPORTS["Reports\nModule"]
    AUDIT["Audit Logs"]
    DASHBOARD["Dashboard"]
    PARENT["Parent Portal\n+ PWA"]
    SUPER["Super Admin\nPanel"]
    DEPLOY["Deployment\n& CI/CD"]

    INFRA --> AUTH --> ROLES --> SETTINGS
    SETTINGS --> ADMISSIONS
    SETTINGS --> CLASSES
    ROLES --> STAFF
    ROLES --> STUDENTS
    CLASSES --> STAFF
    CLASSES --> STUDENTS
    ADMISSIONS --> STUDENTS
    STUDENTS --> ENROLL
    ENROLL --> ATTEND
    ENROLL --> FEES
    ENROLL --> EXAMS
    STAFF --> ATTEND
    STAFF --> FEES
    FEES --> ACCOUNTING
    STAFF --> ACCOUNTING
    CLASSES --> HOMEWORK
    STUDENTS --> LIBRARY
    STUDENTS --> TRANSPORT
    TRANSPORT --> FEES
    COMMS -.->|"used by all modules"| ATTEND
    COMMS -.-> FEES
    COMMS -.-> EXAMS
    COMMS -.-> LIBRARY
    EXAMS --> TEMPLATES
    STUDENTS --> TEMPLATES
    STAFF --> TEMPLATES
    AUDIT -.->|"cross-cuts all modules"| STUDENTS
    AUDIT -.-> FEES
    AUDIT -.-> SETTINGS
    ATTEND --> DASHBOARD
    FEES --> DASHBOARD
    EXAMS --> DASHBOARD
    INVENTORY --> DASHBOARD
    LIBRARY --> DASHBOARD
    ACCOUNTING --> DASHBOARD
    HOMEWORK --> PTM
    CLASSES --> PTM
    DASHBOARD --> PARENT
    FEES --> PARENT
    EXAMS --> PARENT
    ATTEND --> PARENT
    HOMEWORK --> PARENT
    TRANSPORT --> PARENT
    LIBRARY --> PARENT
    PTM --> PARENT
    FEES --> REPORTS
    ATTEND --> REPORTS
    EXAMS --> REPORTS
    STAFF --> REPORTS
    STUDENTS --> REPORTS
    DASHBOARD --> SUPER
    AUDIT --> SUPER
    INFRA --> DEPLOY
    AUTH --> DEPLOY
```

---

## 10. Docker Compose Service Topology

```mermaid
graph TB
    subgraph VOLUMES["Persistent Volumes"]
        VP[("postgres_data")]
        VR[("redis_data")]
        VS[("static_files\n/ media")]
    end

    subgraph COMPOSE["docker-compose.yml"]
        subgraph DB_LAYER["Data Services"]
            PG["postgres:15\nPort 5432\n+ pgBouncer :6432"]
            RD2["redis:7-alpine\nPort 6379"]
        end

        subgraph APP_LAYER["Application Services"]
            BE["backend\n(FastAPI)\nPort 8000\nDepends: postgres, redis"]
            CW2["celery_worker\n(same image as backend)\nconcurrency=4\nDepends: postgres, redis"]
            CB2["celery_beat\nScheduler\nDepends: redis"]
            FL2["flower\nPort 5555\nDepends: redis"]
        end

        subgraph STATIC_LAYER["Frontend"]
            FE2["frontend_build\n(Vite build → /dist)\nnginx serves static files"]
        end

        subgraph PROXY_LAYER["Entry Point"]
            NG2["nginx:alpine\nPort 80 → 443\n• Proxy /api → backend:8000\n• Proxy /ws  → backend:8000\n• Serve /dist static files\n• SSL via certbot volume"]
        end
    end

    subgraph ENV["Environment Files"]
        EV[".env.dev\n.env.staging\n.env.prod\n(never committed to Git)"]
    end

    PG --- VP
    RD2 --- VR
    BE --- VS
    BE --> PG & RD2
    CW2 --> PG & RD2
    CB2 --> RD2
    FL2 --> RD2
    NG2 -->|"reverse proxy"| BE
    NG2 -->|"static serving"| FE2
    EV -.->|"loaded by"| BE & CW2 & CB2
```

---

*Generated for: SeptroSchool (School ERP)*
*Stack: FastAPI · PostgreSQL · Redis · Celery · React 18 · TypeScript · Tailwind CSS*
