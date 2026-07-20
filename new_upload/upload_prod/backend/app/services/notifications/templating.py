"""Render notification templates with a context dict ({student_name}, {amount}, ...)."""
from __future__ import annotations

from typing import Any, Dict

from jinja2 import Environment

# Undefined vars render as empty string (so a half-filled context never crashes a send).
_env = Environment(autoescape=False)


def render(template_str: str, context: Dict[str, Any]) -> str:
    if not template_str:
        return ""
    try:
        return _env.from_string(template_str).render(**(context or {}))
    except Exception:
        # Never let a bad template block delivery — fall back to the raw string.
        return template_str
