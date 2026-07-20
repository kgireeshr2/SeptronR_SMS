# Feature Prompt 27 — Audit Logs

## Round: 4 of 4 — Advanced Features
## Prerequisites: Prompts 01–02 complete

---

## Objective

Implement immutable audit logging for all mutating operations: track who changed what, when, with before/after state. Provide searchable audit log UI for administrators.

---

## 1. Database Model (`backend/app/models/audit.py`)

```python
import uuid
from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB, INET
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin

class AuditLog(Base, TimestampMixin):
    """Immutable audit records — never updated or deleted."""
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    user_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # CREATE/UPDATE/DELETE/LOGIN/EXPORT
    module: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    changes: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # changes: {"before": {...}, "after": {...}} or null for CREATE
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # No updated_at, no soft delete — immutable record
```

---

## 2. Alembic Migration

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID REFERENCES schools(id) ON DELETE SET NULL,
    user_id UUID,
    user_email VARCHAR(255),
    action VARCHAR(50) NOT NULL,      -- CREATE/UPDATE/DELETE/LOGIN/EXPORT/APPROVE/REJECT
    module VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100),
    entity_id VARCHAR(100),
    description TEXT NOT NULL,
    changes JSONB,
    ip_address INET,
    user_agent VARCHAR(500),
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
    -- NO updated_at (immutable)
);

CREATE INDEX ix_audit_logs_school ON audit_logs(school_id, created_at DESC);
CREATE INDEX ix_audit_logs_user ON audit_logs(user_id, created_at DESC);
CREATE INDEX ix_audit_logs_module ON audit_logs(school_id, module, created_at DESC);
```

---

## 3. `log_audit()` Helper (`backend/app/utils/audit.py`)

```python
async def log_audit(
    db,
    action: str,
    module: str,
    description: str,
    school_id: UUID | None = None,
    user: User | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    changes: dict | None = None,
    request: Request | None = None,
):
    """
    Insert AuditLog record.
    Captures ip_address and user_agent from Request if provided.
    Called from service layer on every mutating operation.
    """
    ip = None
    ua = None
    if request:
        ip = request.client.host
        ua = request.headers.get("User-Agent")

    log = AuditLog(
        school_id=school_id,
        user_id=user.id if user else None,
        user_email=user.email if user else None,
        action=action,
        module=module,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id else None,
        description=description,
        changes=changes,
        ip_address=ip,
        user_agent=ua,
    )
    db.add(log)
    # Note: commit is handled by caller or via request-level commit
```

---

## 4. Usage Pattern

Every service function that mutates data:
```python
await log_audit(
    db=db,
    action="CREATE",
    module="students",
    description=f"Student {student.first_name} {student.last_name} created",
    school_id=school_id,
    user=current_user,
    entity_type="Student",
    entity_id=student.id,
    changes=None,
    request=request,
)
```

For updates, capture before/after:
```python
before = {"status": old_leave.status}
# ... make change ...
after = {"status": new_leave.status}
await log_audit(..., action="UPDATE", changes={"before": before, "after": after})
```

---

## 5. API Endpoints

```
GET    /audit-logs?module=&action=&user_id=&date_from=&date_to= → search audit logs [audit:view]
GET    /audit-logs/{id}                                          → single log detail  [audit:view]
```

Only super_admin and school_admin can access audit logs.

---

## 6. Frontend: Audit Log Page (`/audit-logs`)

- **Filters**: Module dropdown, Action (CREATE/UPDATE/DELETE), Date range, User search
- **Table**: Timestamp | User | Action | Module | Entity | Description
- Click row → expand to show changes (before/after JSON diff)
- Export filtered logs to CSV

---

## Verification Checklist

- [ ] `audit_logs` table has no `updated_at` column (immutable)
- [ ] `log_audit` called in every service function that creates/updates/deletes
- [ ] `changes` JSONB contains `{before, after}` for updates, `null` for creates
- [ ] IP address captured from request (supports proxy X-Forwarded-For)
- [ ] Audit log table indexed for fast pagination by (school_id, created_at DESC)
- [ ] Only admin roles can read audit logs
- [ ] Login events logged (action="LOGIN", module="auth")
- [ ] Export events logged (action="EXPORT", module matches report/export type)
