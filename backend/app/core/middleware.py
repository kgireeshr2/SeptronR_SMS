import time
import uuid
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger(__name__)


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
