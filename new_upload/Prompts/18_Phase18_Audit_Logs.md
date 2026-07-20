# PHASE 18 — AUDIT LOGS

## Pre-Requisite
Phases 1–17 complete. All modules implemented.

## Objective
Comprehensive audit trail: every create, update, delete, login, role change, and sensitive action logged. Queryable audit log viewer for admins with filters and export.

---

## 18.1 Database Table (Verify Exists)

```sql
-- Section 21 (⚠️ Actual field names from schema — do NOT invent extras)
audit_logs (
    id UUID PK,
    school_id UUID FK→schools (nullable),  -- null for super admin actions
    user_id UUID (nullable),               -- who performed the action
    user_name VARCHAR(200),                -- snapshot: user's name at time of action
    role_snapshot VARCHAR(100),            -- snapshot: role name at time of action
    module VARCHAR(100),                   -- e.g. "students", "fees", "payroll"
    action VARCHAR(50),                    -- CREATE|UPDATE|DELETE|LOGIN|LOGOUT|EXPORT|APPROVE|REJECT|VIEW_SENSITIVE
    record_type VARCHAR(100),              -- model name: Student|Staff|FeeInvoice|Role etc.
    record_id UUID,                        -- PK of affected record (UUID, nullable)
    record_description TEXT,               -- human-readable: "Deleted student John Doe (ADM-001)"
    old_values JSONB,                      -- snapshot before change (UPDATE/DELETE)
    new_values JSONB,                      -- snapshot after change (CREATE/UPDATE)
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
)
PARTITION BY RANGE (created_at);          -- ⚠️ Table is PARTITIONED; create quarterly/monthly partitions in Alembic

-- Required indexes (create on each partition or parent):
-- (school_id, created_at DESC)
-- (user_id)
-- (record_type, record_id)
-- (action)
-- (module)
```

---

## 18.2 Audit Middleware (`backend/app/utils/audit.py`)

```python
from contextvars import ContextVar
from sqlalchemy.ext.asyncio import AsyncSession

# Context variable to store audit context in current request
audit_context: ContextVar[dict] = ContextVar('audit_context', default={})

async def log_audit(
    db: AsyncSession,
    action: str,
    module: str,
    record_type: str,
    record_id: Optional[str] = None,
    record_description: Optional[str] = None,
    old_values: Optional[dict] = None,
    new_values: Optional[dict] = None,
    school_id: Optional[str] = None,
):
    ctx = audit_context.get()
    entry = AuditLog(
        school_id=school_id or ctx.get('school_id'),
        user_id=ctx.get('user_id'),
        user_name=ctx.get('user_name'),
        role_snapshot=ctx.get('role_snapshot'),
        module=module,
        action=action,
        record_type=record_type,
        record_id=record_id,
        record_description=record_description,
        old_values=old_values,
        new_values=new_values,
        ip_address=ctx.get('ip_address'),
        user_agent=ctx.get('user_agent'),
    )
    db.add(entry)
    # NOTE: do NOT await flush/commit here; it will be committed with the main transaction
```

### Middleware to set context:
```python
@app.middleware("http")
async def set_audit_context(request: Request, call_next):
    token = audit_context.set({
        'school_id': request.state.school_id if hasattr(request.state, 'school_id') else None,
        'user_id': str(request.state.user.id) if hasattr(request.state, 'user') else None,
        'user_name': request.state.user.full_name if hasattr(request.state, 'user') else None,
        'role_snapshot': request.state.user_role if hasattr(request.state, 'user_role') else None,
        'ip_address': request.client.host,
        'user_agent': request.headers.get('user-agent'),
    })
    response = await call_next(request)
    audit_context.reset(token)
    return response
```

---

## 18.3 Integration Points (Call `log_audit` in these services)

| Service | Actions to Audit |
|---------|-----------------|
| auth_service | LOGIN, LOGOUT, PASSWORD_RESET, ROLE_ASSIGNED |
| student_service | CREATE, UPDATE, DELETE, PROMOTE, ISSUE_TC |
| staff_service | CREATE, UPDATE, DELETE, TERMINATE |
| fee_service | COLLECT, CANCEL, WAIVE |
| admission_service | APPROVE, REJECT |
| role_service | CREATE, UPDATE, DELETE, ASSIGN_PERMISSIONS |
| user_service | UPDATE, DEACTIVATE, ACTIVATE |
| payroll_service | GENERATE, APPROVE, MARK_PAID |
| exam_service | MARKS_ENTERED, RESULTS_PUBLISHED |
| settings_service | UPDATE (treat as sensitive) |
| Any GET with `export` | EXPORT action |

---

## 18.4 API Endpoints

```
GET /api/v1/audit-logs                   → list [audit:view]
    Query params: user_id, module, record_type, action, from_date, to_date, search, page, page_size
GET /api/v1/audit-logs/{id}              → detail with full old_values/new_values
GET /api/v1/audit-logs/export            → Excel export [audit:export]
GET /api/v1/audit-logs/stats             → action counts by type, top users, module breakdown
```

---

## 18.5 Frontend Page (`/admin/audit-logs`)

Permission: `audit:view`

**Filters:**
- Date range, User (search by name), Module (dropdown), Record Type (dropdown), Action (dropdown)

**Table columns:**
- Timestamp, User, Role, Module, Action, Record Type, Record ID, Description, IP Address

**Detail Drawer:**
- Click row → slide-in panel showing:
  - Full `record_description`
  - `old_values` JSON diff view (before/after highlighted)
  - `new_values` JSON viewer
  - IP, User Agent

**Stats Panel:**
- Today's activity count
- Most active users (by user_name)
- Most common module
- Most common record_type

### `frontend/src/api/auditLogs.ts`
```typescript
export const auditLogsApi = {
  list: (params: AuditLogParams) => api.get('/audit-logs', { params }),
  get: (id: string) => api.get(`/audit-logs/${id}`),
  export: (params: AuditLogParams) =>
    api.get('/audit-logs/export', { params, responseType: 'blob' }),
  stats: () => api.get('/audit-logs/stats'),
};
```

---

## 18.6 Audit Log Schema: old_values / new_values Convention

- For CREATE: `old_values=null`, `new_values={...created_fields_excluding_sensitive}`
- For UPDATE: `old_values={...changed_fields_before}`, `new_values={...changed_fields_after}`
- For DELETE: `old_values={...deleted_record}`, `new_values=null`
- Never store passwords, tokens, or raw sensitive values in old_values/new_values
- Strip: `password_hash`, `otp_code`, `bank_account_no` (show last 4 only)

---

## 18.7 Tests

```python
async def test_audit_log_created_on_student_create(): ...
async def test_audit_log_on_login(): ...
async def test_audit_log_on_role_assignment(): ...
async def test_sensitive_fields_stripped_from_audit(): ...   # no password_hash in new_values
async def test_audit_log_list_filter_by_action(): ...
async def test_audit_log_filter_by_date_range(): ...
```

---

## 18.8 Deliverables Checklist

- [ ] `audit_logs` table + AuditLog model
- [ ] `log_audit()` utility function using context var
- [ ] Audit context middleware sets user/ip/request_id
- [ ] `log_audit()` called in all specified services
- [ ] Audit log list API with all filters
- [ ] Audit log detail with old/new data
- [ ] Old/new data diff viewer in frontend
- [ ] Excel export of audit logs
- [ ] Sensitive field stripping before storage
- [ ] Audit stats endpoint
