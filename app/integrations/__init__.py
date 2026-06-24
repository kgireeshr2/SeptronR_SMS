"""Reusable outbound channel clients (WhatsApp, SMS, Email, Push).

These are plain, framework-agnostic senders. They take a resolved per-school config
dict and content, perform the network I/O synchronously, and return a uniform result:

    {"ok": bool, "provider_message_id": str | None, "raw": str, "error": str | None}

Synchronous on purpose so they work directly inside Celery workers; async callers
(e.g. the FastAPI webhook) invoke them via `asyncio.to_thread`.
"""
