# Feature Prompt 32 — Testing & Security Hardening

## Round: 4 of 4 — Advanced Features
## Prerequisites: All modules implemented

---

## Objective

Implement comprehensive test suite (unit, integration, performance), apply security hardening measures, and validate all modules end-to-end.

---

## 1. Testing Setup

### Backend Test Configuration (`backend/pytest.ini`)
```ini
[pytest]
asyncio_mode = auto
testpaths = tests
markers =
    unit: Unit tests
    integration: Integration tests requiring DB
    slow: Slow tests
```

### Test Dependencies (`requirements-dev.txt`)
```
pytest==8.x
pytest-asyncio==0.23.x
pytest-cov==4.x
httpx==0.27.x         # async test client
faker==24.x           # test data generation
factory-boy==3.3.x    # model factories
```

### Test Database Setup (`tests/conftest.py`)
```python
@pytest.fixture(scope="session")
async def engine():
    """Create test DB engine using postgresql+asyncpg://...test_db."""

@pytest.fixture
async def db(engine):
    """Per-test transaction with rollback."""

@pytest.fixture
async def client(db):
    """TestClient with test DB session injected."""

@pytest.fixture
async def admin_token(client):
    """JWT for school admin user."""

@pytest.fixture
async def teacher_token(client):
    """JWT for teacher user."""
```

---

## 2. Test Coverage Targets

| Module | Min Coverage |
|--------|-------------|
| auth | 95% |
| students | 90% |
| staff | 90% |
| fees | 90% |
| attendance | 90% |
| all others | 80% |

---

## 3. Required Test Cases

### Authentication Tests
```python
async def test_login_valid_credentials()
async def test_login_invalid_password_returns_401()
async def test_login_lockout_after_5_failures()
async def test_refresh_token_rotation()
async def test_logout_blacklists_token()
async def test_permission_required_blocks_unauthorized()
```

### Student Tests
```python
async def test_create_student_generates_admission_number()
async def test_admission_number_unique_per_school()
async def test_promote_students_creates_new_enrollment()
async def test_bulk_import_excel_creates_students()
async def test_student_export_returns_xlsx()
```

### Fee Tests
```python
async def test_generate_invoices_creates_per_enrolled_student()
async def test_record_payment_updates_invoice_status()
async def test_partial_payment_sets_status_partial()
async def test_fine_not_applied_within_grace_days()
async def test_fine_applied_after_grace_days()
async def test_razorpay_webhook_invalid_signature_rejected()
```

### Attendance Tests
```python
async def test_mark_attendance_creates_session()
async def test_duplicate_session_returns_existing_data()
async def test_holiday_date_blocked_for_marking()
async def test_monthly_report_excludes_sundays()
async def test_absent_notification_task_dispatched()
```

---

## 4. Security Hardening

### 4.1 Input Validation & Injection Prevention
```python
# All Pydantic models use strict types
# SQL: only parameterized queries via SQLAlchemy ORM
# File uploads: validate MIME type + size limit
# NEVER use string.format() with user input in SQL
```

### 4.2 Security Headers Middleware
```python
# backend/app/middleware/security.py
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response
```

### 4.3 Rate Limiting
```python
# Already using slowapi (from Prompt 02 auth)
# Add to sensitive endpoints:
@limiter.limit("10/minute")     # payment endpoints
@limiter.limit("5/minute")      # OTP endpoints
@limiter.limit("100/minute")    # general API endpoints
```

### 4.4 File Upload Security
```python
ALLOWED_MIME_TYPES = {
    "image/jpeg", "image/png", "image/webp",
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

async def validate_upload(file: UploadFile):
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(400, "File type not allowed")
    content = await file.read(MAX_FILE_SIZE + 1)
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(400, "File too large")
    await file.seek(0)
```

### 4.5 Secret Encryption
```python
# backend/app/utils/encryption.py
from cryptography.fernet import Fernet

def encrypt_setting(value: str) -> str:
    """Encrypt sensitive settings using Fernet symmetric key from SECRET_KEY."""

def decrypt_setting(encrypted: str) -> str:
    """Decrypt. Never log decrypted values."""
```

### 4.6 CORS Configuration
```python
# Restrict to known frontend origin in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # ["https://school.domain.com"]
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-School-Slug"],
)
```

---

## 5. Performance Testing

```python
# tests/test_performance.py
@pytest.mark.slow
async def test_student_list_1000_students_under_500ms():
    """Create 1000 students. GET /students with pagination must respond < 500ms."""

@pytest.mark.slow
async def test_monthly_attendance_report_under_1s():
    """Full month attendance for 500 students must generate < 1s."""
```

---

## 6. Running Tests

```bash
# All tests
pytest --cov=app --cov-report=html

# Only unit tests
pytest -m unit

# With verbose output
pytest -v tests/test_fees.py

# Coverage check (fail if below 80%)
pytest --cov=app --cov-fail-under=80
```

---

## Verification Checklist

- [ ] All authentication tests pass
- [ ] Coverage > 80% for all modules
- [ ] Security headers middleware active (check with curl -I)
- [ ] File upload rejects non-allowed MIME types
- [ ] Rate limiting blocks after threshold (test with wrk or ab)
- [ ] CORS only allows configured origin in production
- [ ] Encrypted settings cannot be read from DB without SECRET_KEY
- [ ] No raw SQL string formatting in codebase (`grep -r "% " app/` returns nothing)
- [ ] All foreign key constraints tested (orphan creation rejected)
