import time
import uuid
import logging
import asyncio
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Path  →  module name mapping
# ---------------------------------------------------------------------------
_SEGMENT_TO_MODULE: dict[str, str] = {
    "students": "students",
    "admissions": "admissions",
    "staff": "staff",
    "users": "users",
    "roles": "roles",
    "classes": "classes",
    "sections": "sections",
    "subjects": "subjects",
    "timetable": "classes",
    "academic-years": "academic_years",
    "attendance": "attendance",
    "fee-structures": "fees",
    "fee-plan": "fees",
    "fee-invoices": "fees",
    "fee-payments": "fees",
    "fees": "fees",
    "exams": "exams",
    "exam-types": "exams",
    "student-marks": "exams",
    "homework": "homework",
    "transport": "transport",
    "library": "library",
    "inventory": "inventory",
    "vendors": "inventory",
    "accounting": "accounting",
    "income-categories": "accounting",
    "income-records": "accounting",
    "expense-categories": "accounting",
    "expense-records": "accounting",
    "payroll": "accounting",
    "calendar": "calendar",
    "communications": "communications",
    "templates": "templates",
    "settings": "settings",
    "schools": "schools",
    "reports": "reports",
    "leaves": "staff",
    "leave-types": "staff",
    "departments": "staff",
    "designations": "staff",
    "permissions": "roles",
    "dashboard": "dashboard",
    "notifications": "communications",
    "ptm": "communications",
}

_SKIP_PATHS = {"/api/v1/auth/refresh", "/api/v1/auth/token"}
_SKIP_PREFIXES = ("/docs", "/redoc", "/openapi", "/static", "/health")


def _infer_module_action(method: str, path: str) -> tuple[str, str] | None:
    """Return (module, action) or None to skip."""
    # Strip query string and /api/v1 prefix
    parts = [p for p in path.split("?")[0].split("/") if p]
    # skip e.g. ['api', 'v1', '<segment>', ...]
    try:
        idx = parts.index("v1")
        parts = parts[idx + 1:]
    except ValueError:
        pass
    if not parts:
        return None

    first_segment = parts[0].lower()

    # Special-case auth
    if first_segment == "auth":
        action_seg = parts[1].lower() if len(parts) > 1 else method.lower()
        return "auth", action_seg

    module = _SEGMENT_TO_MODULE.get(first_segment, first_segment.replace("-", "_"))
    method_to_action = {
        "POST": "create",
        "PUT": "update",
        "PATCH": "update",
        "DELETE": "delete",
        "GET": "read",
    }
    action = method_to_action.get(method.upper(), method.lower())
    return module, action


_SENSITIVE_READ_MODULES = {
    "students", "staff", "fees", "fee_invoices", "fee_payments",
    "exams", "student_marks", "payroll", "audit", "reports",
    "accounting", "income_records", "expense_records",
}


class AuditMiddleware(BaseHTTPMiddleware):
    """Automatically write an audit log entry for every mutating API request
    and sensitive read (GET) requests."""

    async def dispatch(self, request: Request, call_next):
        # Pre-read login body before call_next consumes the stream
        login_username: str | None = None
        if request.method == "POST" and request.url.path.endswith("/auth/login"):
            try:
                import json as _json
                body_bytes = await request.body()  # Starlette caches this
                login_username = _json.loads(body_bytes).get("username") or _json.loads(body_bytes).get("email")
            except Exception:
                pass

        response = await call_next(request)

        path = request.url.path

        # Must be an /api/v1/* route
        if "/api/v1/" not in path:
            return response
        if path in _SKIP_PATHS or path.startswith(_SKIP_PREFIXES):
            return response

        method = request.method

        # For GET: only log reads of sensitive modules
        if method == "GET":
            result = _infer_module_action(method, path)
            if result is None:
                return response
            module, _ = result
            if module not in _SENSITIVE_READ_MODULES:
                return response
        elif method not in ("POST", "PUT", "PATCH", "DELETE"):
            return response

        # Only log successful requests (2xx)
        if response.status_code >= 400:
            return response

        result = _infer_module_action(request.method, path)
        if result is None:
            return response
        module, action = result

        # Extract auth context (best-effort — never block the response)
        token_data: dict = {}
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                from app.core.security import decode_token
                token_data = decode_token(auth_header[7:])
            except Exception:
                pass

        school_id = request.headers.get("X-School-Id") or token_data.get("school_id")
        user_id = token_data.get("sub")
        user_name = token_data.get("name") or token_data.get("email")

        # For login requests without a token, try to resolve school from username in body
        if path.endswith("/auth/login") and not school_id and login_username:
            try:
                school_id, user_id, user_name = await _lookup_user_school(login_username)
                logger.info("AuditMiddleware login lookup: username=%s school_id=%s user_name=%s", login_username, school_id, user_name)
            except Exception as exc:
                logger.warning("AuditMiddleware login lookup failed: %s", exc)
        ip = request.client.host if request.client else None
        ua = request.headers.get("user-agent")
        status_code = response.status_code

        # Extract record_id from path (last UUID-looking segment)
        record_id: str | None = None
        import re
        uuid_re = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)
        for seg in path.split("/"):
            if uuid_re.match(seg):
                record_id = seg

        # Path suffix as record_type hint (e.g. /pay, /cancel)
        path_parts = [p for p in path.split("/") if p and not uuid_re.match(p)]
        record_type = path_parts[-1].replace("-", "_") if path_parts else None

        # Fire-and-forget background task so we never delay the response
        asyncio.ensure_future(
            _write_audit_bg(
                school_id=school_id,
                user_id=user_id,
                user_name=user_name,
                module=module,
                action=action,
                record_type=record_type,
                record_id=record_id,
                ip_address=ip,
                user_agent=ua,
            )
        )

        return response


async def _lookup_user_school(username: str):
    """Quick DB lookup to get school_id/user_id/user_name for a login username."""
    try:
        from app.db.session import async_session_factory
        from sqlalchemy import text
        async with async_session_factory() as db:
            r = await db.execute(
                text("SELECT id, school_id, first_name || ' ' || last_name AS name FROM users WHERE (username = :u OR email = :u) AND deleted_at IS NULL LIMIT 1"),
                {"u": username},
            )
            row = r.mappings().first()
            if row:
                return str(row["school_id"]) if row["school_id"] else None, str(row["id"]), row["name"]
    except Exception:
        pass
    return None, None, None


async def _write_audit_bg(
    *,
    school_id,
    user_id,
    user_name,
    module,
    action,
    record_type,
    record_id,
    ip_address,
    user_agent,
):
    """Background task: open a fresh DB session and write one audit log row."""
    try:
        from app.db.session import async_session_factory
        import app.repositories.audit_repository as audit_repo
        async with async_session_factory() as db:
            async with db.begin():
                await audit_repo.write_log(
                    db,
                    school_id=school_id,
                    user_id=user_id,
                    user_name=user_name,
                    role_snapshot=None,
                    module=module,
                    action=action,
                    record_type=record_type,
                    record_id=record_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
    except Exception as exc:  # never crash the server
        logger.warning("AuditMiddleware write failed: %s", exc)
    else:
        logger.debug("AuditMiddleware wrote: module=%s action=%s school_id=%s user=%s", module, action, school_id, user_name)


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    """Log every request with method, path, status code and duration."""

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        request_id = str(uuid.uuid4())[:8]
        logger.info(f"[{request_id}] {request.method} {request.url.path}")
        response = await call_next(request)
        duration = (time.perf_counter() - start) * 1000
        logger.info(f"[{request_id}] → {response.status_code} ({duration:.1f}ms)")
        return response


class SchoolContextMiddleware(BaseHTTPMiddleware):
    """
    Extracts school context from:
      1. X-School-Slug header (set by Nginx from subdomain)
      2. JWT claim 'school_id' (set after token decode in auth dependency)

    Sets request.state.school_id and request.state.school_slug.
    """

    async def dispatch(self, request: Request, call_next):
        school_slug = request.headers.get("X-School-Slug", "").strip().lower()
        school_id = request.headers.get("X-School-Id", "").strip()
        request.state.school_slug = school_slug
        request.state.school_id = school_id or None
        return await call_next(request)
