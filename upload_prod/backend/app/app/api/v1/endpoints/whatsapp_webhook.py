"""
WhatsApp Meta Cloud API Webhook
=================================
Handles incoming messages from WhatsApp and sends responses using
the Meta Graph API (Cloud API).

Environment variables required:
  META_WHATSAPP_TOKEN          - Meta Cloud API permanent access token
  META_PHONE_NUMBER_ID         - WhatsApp phone number ID from Meta Business
  META_WHATSAPP_VERIFY_TOKEN   - Any secret string you set in Meta webhook config

Flow:
  1. GET  /chat/whatsapp/webhook  → Webhook verification by Meta
  2. POST /chat/whatsapp/webhook  → Incoming messages from users
     • Looks up user by phone number
     • Loads/creates conversation session (keyed by WA phone number)
     • Calls FlowEngine.handle()
     • Serializes BotResponse → WhatsApp interactive list or plain text
     • Sends via httpx to Meta Graph API

WhatsApp number lookup:
  The incoming `from` phone number (e.g. "919876543210") is matched
  against `users.phone` (normalized — strip leading zeros, country code).
"""
from __future__ import annotations

import logging
import os
import re
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import PlainTextResponse
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.auth import User
from app.models.chat_session import ConversationSession
from app.services.chat_flow_engine import BotResponse, FlowEngine
from app.core.config import settings
from pydantic import BaseModel

logger = logging.getLogger(__name__)

whatsapp_router = APIRouter(prefix="/chat/whatsapp", tags=["WhatsApp"])

# ── Config ────────────────────────────────────────────────────────────────────
WA_TOKEN = settings.META_WHATSAPP_TOKEN or os.getenv("WHATSAPP_TOKEN", "")
WA_PHONE_ID = settings.META_PHONE_NUMBER_ID or os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
WA_VERIFY_TOKEN = settings.META_WHATSAPP_VERIFY_TOKEN
WA_API_URL = "https://graph.facebook.com/v18.0/{phone_id}/messages"

_engine = FlowEngine()


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _normalize_phone(phone: str) -> str:
    """Strip all non-digits, strip leading country code 91 for India."""
    digits = re.sub(r"\D", "", phone or "")
    # WhatsApp sends full international format, store without country code
    if digits.startswith("91") and len(digits) == 12:
        return digits[2:]
    return digits


async def _lookup_user_by_phone(phone: str, db: AsyncSession) -> Optional[User]:
    normalized = _normalize_phone(phone)
    # Try exact, then stripped
    result = await db.execute(
        select(User).where(
            (User.phone == phone) |
            (User.phone == normalized) |
            (User.phone == f"+{phone}")
        ).where(User.is_active == True)  # noqa: E712
    )
    return result.scalar_one_or_none()


async def _get_or_create_wa_session(
    wa_from: str,
    user: User,
    db: AsyncSession,
) -> ConversationSession:
    # Session ID is keyed by WA phone number for easy lookup
    sid = f"wa_{wa_from}"
    result = await db.execute(
        select(ConversationSession).where(ConversationSession.id == sid)
    )
    session = result.scalar_one_or_none()
    if session is None or session.is_expired:
        session = ConversationSession(
            id=sid,
            user_id=str(user.id),
            school_id=str(user.school_id) if user.school_id else None,
            channel="whatsapp",
        )
        db.add(session)
        await db.flush()
    return session


async def _send_wa_message(to: str, payload: Dict[str, Any]) -> None:
    """POST to Meta Cloud API. Silently logs errors."""
    if not WA_TOKEN or not WA_PHONE_ID:
        logger.warning("WhatsApp credentials not configured; skipping send.")
        return
    url = WA_API_URL.format(phone_id=WA_PHONE_ID)
    headers = {
        "Authorization": f"Bearer {WA_TOKEN}",
        "Content-Type": "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code >= 400:
                logger.error(
                    "WA send FAILED — status=%s phone_id=%s token_prefix=%s error=%s",
                    resp.status_code, WA_PHONE_ID, WA_TOKEN[:20] if WA_TOKEN else "EMPTY", resp.text[:500]
                )
            else:
                logger.info("WA message sent OK to %s — msg_id=%s", to, resp.json().get("messages", [{}])[0].get("id", "?"))
    except Exception as exc:
        logger.exception("Failed to send WhatsApp message: %s", exc)


# ─── Response Serializer ─────────────────────────────────────────────────────

def _wa_text(to: str, text: str) -> Dict:
    # WhatsApp text is plain — strip markdown bold/italic
    plain = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    plain = re.sub(r"_(.+?)_", r"\1", plain)
    return {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": plain[:4096]},
    }


def _wa_interactive_list(to: str, body_text: str, options: List[Dict]) -> Dict:
    """Meta interactive list message. Max 10 rows per section, title max 24 chars."""
    rows = [
        {
            "id": o["id"][:200],
            "title": o["label"][:24],
            "description": (o.get("description") or "")[:72],
        }
        for o in options[:10]
    ]
    # Strip markdown from body
    plain_body = re.sub(r"\*\*(.+?)\*\*", r"\1", body_text)[:1024]
    return {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": "School Assistant"},
            "body": {"text": plain_body},
            "footer": {"text": "Reply with the option ID or type 'menu' to restart"},
            "action": {
                "button": "Select",
                "sections": [{"title": "Options", "rows": rows}],
            },
        },
    }


def _wa_buttons(to: str, body_text: str, options: List[Dict]) -> Dict:
    """Meta interactive buttons. Max 3 buttons."""
    buttons = [
        {"type": "reply", "reply": {"id": o["id"][:256], "title": o["label"][:20]}}
        for o in options[:3]
    ]
    plain = re.sub(r"\*\*(.+?)\*\*", r"\1", body_text)[:1024]
    return {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": plain},
            "action": {"buttons": buttons},
        },
    }


def _serialize_bot_response(to: str, resp: BotResponse) -> List[Dict]:
    """Convert BotResponse → list of WA API payload dicts (may be multiple messages)."""
    messages: List[Dict] = []

    # 1. Main text (always send)
    if resp.options:
        if len(resp.options) <= 3:
            messages.append(_wa_buttons(to, resp.text, [o.model_dump() for o in resp.options]))
        else:
            messages.append(_wa_interactive_list(to, resp.text, [o.model_dump() for o in resp.options]))
    else:
        messages.append(_wa_text(to, resp.text))

    # 2. Attendance table → numbered list text message
    if resp.attendance_rows:
        lines = ["Mark attendance — reply with comma-separated numbers of *ABSENT* students:"]
        for i, row in enumerate(resp.attendance_rows, 1):
            lines.append(f"{i}. {row.name} ({row.roll_number})")
        lines.append("\nExample: 3,7,12  (blank = all present)")
        lines.append("Or reply: save (all present)")
        messages.append(_wa_text(to, "\n".join(lines)))

    # 3. Table cards → formatted text
    for card in resp.cards:
        if card.get("type") == "table":
            headers = card.get("headers", [])
            rows = card.get("rows", [])
            lines = [f"📊 *{card.get('title', 'Data')}*"]
            lines.append("  ".join(h[:10] for h in headers[:4]))
            lines.append("─" * 30)
            for row in rows[:15]:
                lines.append("  ".join(str(c)[:12] for c in row[:4]))
            if len(rows) > 15:
                lines.append(f"... and {len(rows)-15} more rows")
            messages.append(_wa_text(to, "\n".join(lines)))
        elif card.get("type") == "stats":
            stats = card.get("stats", [])
            lines = ["📊 " + "   |   ".join(f"{s['label']}: {s['value']}" for s in stats[:4])]
            messages.append(_wa_text(to, "\n".join(lines)))

    # 4. Actions as tappable buttons (path → flow ID) instead of plain text
    if resp.actions:
        _PATH_FLOW = {
            "/attendance":       "attendance_view",
            "/attendance-today": "attendance_today",
            "/fees":             "fee",
            "/leaves":           "leave",
            "/exams":            "marks",
            "/students":         "student_details",
            "/accounting":       "accounting",
            "/super-admin":      "sa_schools",
        }
        # Build options from actions, mapping path → flow ID as the button ID
        action_options = []
        for a in resp.actions[:3]:
            path = a.get("path", "")
            flow_id = _PATH_FLOW.get(path)
            if not flow_id:
                # Try prefix match
                for k, v in _PATH_FLOW.items():
                    if path.startswith(k):
                        flow_id = v
                        break
            btn_id = flow_id or a["label"].lower().replace(" ", "_")
            action_options.append({"id": btn_id, "label": a["label"], "description": ""})
        if action_options and not resp.options:
            if len(action_options) <= 3:
                messages.append(_wa_buttons(to, "Open in chat:", action_options))
            else:
                messages.append(_wa_interactive_list(to, "Open in chat:", action_options))

    # 5. Suggestions as numbered list if session_ended
    if resp.session_ended:
        messages.append(_wa_text(to, "Type *menu* or *hi* to start again."))

    return messages


# ─── Webhook Endpoints ────────────────────────────────────────────────────────

@whatsapp_router.get("/webhook", response_class=PlainTextResponse)
async def wa_verify(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
):
    """Meta webhook verification endpoint (GET). Called once during setup."""
    logger.info(
        "WA verify attempt — mode=%s token_match=%s challenge=%s",
        hub_mode,
        hub_verify_token == WA_VERIFY_TOKEN,
        hub_challenge,
    )
    if hub_mode == "subscribe" and hub_verify_token == WA_VERIFY_TOKEN:
        logger.info("WhatsApp webhook verified successfully.")
        # Meta requires the challenge returned as plain text, not JSON
        return PlainTextResponse(content=str(hub_challenge or "OK"), status_code=200)
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verification failed — token mismatch")


@whatsapp_router.post("/webhook")
async def wa_incoming(request: Request, db: AsyncSession = Depends(get_db)):
    """Receive messages from WhatsApp.

    Meta sends:  entry[].changes[].value.messages[] with:
      - type: "text" → text.body
      - type: "interactive" with interactive.type "list_reply" | "button_reply"
    """
    try:
        body = await request.json()
    except Exception:
        return {"status": "ok"}  # Always return 200 to Meta

    try:
        entry = body.get("entry", [{}])[0]
        change = entry.get("changes", [{}])[0]
        value = change.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return {"status": "ok"}

        wa_msg = messages[0]
        wa_from: str = wa_msg.get("from", "")
        msg_type = wa_msg.get("type", "")

        # Extract message text or interactive reply ID
        if msg_type == "text":
            user_text = wa_msg.get("text", {}).get("body", "").strip()
        elif msg_type == "interactive":
            interactive = wa_msg.get("interactive", {})
            i_type = interactive.get("type", "")
            if i_type == "list_reply":
                user_text = interactive.get("list_reply", {}).get("id", "")
            elif i_type == "button_reply":
                user_text = interactive.get("button_reply", {}).get("id", "")
            else:
                user_text = ""
        else:
            return {"status": "ok"}  # Ignore other message types (images, docs, etc.)

        if not user_text or not wa_from:
            return {"status": "ok"}

        # Look up user by phone number
        user = await _lookup_user_by_phone(wa_from, db)
        if not user:
            # Unknown number — send onboarding message
            await _send_wa_message(wa_from, _wa_text(
                wa_from,
                "👋 Hi! Your number is not linked to an account in this school system.\n"
                "Please contact your school administrator to link your WhatsApp number.",
            ))
            return {"status": "ok"}

        # Handle attendance flow: user may reply "1,5,7" for absent students
        session = await _get_or_create_wa_session(wa_from, user, db)

        # Parse comma-separated absent numbers for attendance flows
        payload = None
        if session.current_step == "save" and session.current_flow in (
            "student_attendance", "staff_attendance"
        ):
            # Check if message looks like attendance answer: "1,2,3" or "save" or "all present"
            absent_text = user_text.strip().lower()
            if absent_text in ("save", "done", "all present", "0", "none"):
                ctx = session.context
                all_ids = ctx.get("all_student_ids", [])
                payload = {"present_ids": all_ids, "absent_ids": []}
            elif re.match(r"^[\d,\s]+$", absent_text):
                # Parse absent numbers
                ctx = session.context
                all_rows = ctx.get("all_attendance_rows", [])  # [{id, index}]
                absent_nums = {int(n) for n in re.findall(r"\d+", absent_text)}
                present_ids = [r["student_id"] for i, r in enumerate(all_rows, 1) if i not in absent_nums]
                absent_ids = [r["student_id"] for i, r in enumerate(all_rows, 1) if i in absent_nums]
                payload = {"present_ids": present_ids, "absent_ids": absent_ids}

        school_id = str(user.school_id) if user.school_id else ""

        response = await _engine.handle(
            session=session,
            message=user_text,
            payload=payload,
            user=user,
            db=db,
            school_id=school_id,
        )

        # Store attendance rows in context so we can parse "1,2,3" on next message
        if response.attendance_rows and session.current_step == "save":
            session.patch_context({
                "all_attendance_rows": [r.model_dump() for r in response.attendance_rows],
                "all_student_ids": [r.student_id for r in response.attendance_rows],
            })

        await db.commit()

        # Send response messages via Meta API
        wa_payloads = _serialize_bot_response(wa_from, response)
        for wp in wa_payloads:
            await _send_wa_message(wa_from, wp)

    except Exception as exc:
        logger.exception("WhatsApp webhook error: %s", exc)

    return {"status": "ok"}


# ─── Simulator / Test Endpoint ────────────────────────────────────────────────

class WaTestRequest(BaseModel):
    message: str
    phone: str = ""          # phone to look up a different user (optional; defaults to current user)
    reset_session: bool = False
    payload: Optional[Dict[str, Any]] = None  # e.g. {"present_ids": [...], "absent_ids": [...]}


class WaTestResponse(BaseModel):
    text: str
    options: List[Dict] = []
    attendance_rows: List[Dict] = []
    cards: List[Dict] = []
    actions: List[Dict] = []
    suggestions: List[str] = []
    breadcrumb: str = ""
    session_ended: bool = False
    wa_payloads: List[Dict] = []   # Serialised WhatsApp API payloads (for inspection)


@whatsapp_router.post("/test", response_model=WaTestResponse, summary="Simulate WhatsApp chat (no Meta credentials needed)")
async def wa_simulate(
    body: WaTestRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Test the WhatsApp chatbot flow without real WhatsApp credentials.

    Runs the same FlowEngine as the real webhook, keyed by the user's phone
    or an optional override phone.  Returns both the structured BotResponse and
    the serialised WA payloads so you can see exactly what WhatsApp would render.
    """
    # Resolve user — optional phone override
    user: Optional[User] = None
    phone = (body.phone or "").strip()
    if phone:
        user = await _lookup_user_by_phone(phone, db)
        if not user:
            raise HTTPException(status_code=404, detail=f"No active user found for phone '{phone}'")
    else:
        user = current_user

    wa_from = _normalize_phone(user.phone or "") or str(user.id)[:20]
    sim_key = f"wa_sim_{wa_from}"

    # Optionally wipe session so we can restart the flow
    if body.reset_session:
        from sqlalchemy import delete
        await db.execute(
            delete(ConversationSession).where(ConversationSession.id == sim_key)
        )
        await db.flush()

    # Re-use session helper (same logic as real webhook)
    session = await _get_or_create_wa_session(sim_key, user, db)

    school_id = str(user.school_id) if user.school_id else ""

    response = await _engine.handle(
        session=session,
        message=body.message.strip() or "hi",
        payload=body.payload,
        user=user,
        db=db,
        school_id=school_id,
    )

    await db.commit()

    wa_payloads = _serialize_bot_response(wa_from, response)

    return WaTestResponse(
        text=response.text,
        options=[o.model_dump() for o in response.options],
        attendance_rows=[r.model_dump() for r in response.attendance_rows],
        cards=response.cards,
        actions=response.actions,
        suggestions=response.suggestions,
        breadcrumb=response.breadcrumb or "",
        session_ended=response.session_ended,
        wa_payloads=wa_payloads,
    )


# ─── Config Status ───────────────────────────────────────────────────────────

@whatsapp_router.get("/config-status", summary="Check WhatsApp API credential status")
async def wa_config_status(
    current_user: User = Depends(get_current_user),
):
    """Returns whether Meta WhatsApp credentials are configured in the environment."""
    api_base = settings.BACKEND_URL.rstrip("/")
    return {
        "token_configured": bool(WA_TOKEN),
        "phone_id_configured": bool(WA_PHONE_ID),
        "verify_token": WA_VERIFY_TOKEN,
        "webhook_url": f"{api_base}/api/v1/chat/whatsapp/webhook",
        "api_version": "v18.0",
        "ready_for_real_wa": bool(WA_TOKEN and WA_PHONE_ID),
    }


@whatsapp_router.get("/verify-test", summary="Simulate Meta webhook verification locally (no Meta needed)")
async def wa_verify_test(
    current_user: User = Depends(get_current_user),
):
    """Simulates what Meta sends during webhook setup — returns success if verify token is correct."""
    import httpx
    api_base = settings.BACKEND_URL.rstrip("/")
    test_challenge = "1234567890"
    url = f"{api_base}/api/v1/chat/whatsapp/webhook"
    params = {
        "hub.mode": "subscribe",
        "hub.challenge": test_challenge,
        "hub.verify_token": WA_VERIFY_TOKEN,
    }
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(url, params=params)
        if resp.status_code == 200 and resp.text.strip() == test_challenge:
            return {"status": "✅ Webhook verification works!", "challenge_echoed": resp.text.strip(), "verify_token_used": WA_VERIFY_TOKEN}
        return {"status": "❌ Verification failed", "http_status": resp.status_code, "body": resp.text[:200]}
    except Exception as exc:
        return {"status": "❌ Could not reach webhook URL", "error": str(exc), "url": url}


# ─── Send Real Test Message ───────────────────────────────────────────────────

class WaSendTestRequest(BaseModel):
    phone: str                   # full international format e.g. 919876543210
    message: str = "Hello from School SMS! This is a test message."


@whatsapp_router.post("/send-test-message", summary="Send a real WhatsApp text message (requires Meta credentials)")
async def wa_send_test_message(
    body: WaSendTestRequest,
    current_user: User = Depends(get_current_user),
):
    """Send a plain text WhatsApp message to any phone number.

    Requires META_WHATSAPP_TOKEN and META_PHONE_NUMBER_ID to be set in .env.
    Phone should be in full international format without '+' (e.g. 919876543210).
    """
    if not WA_TOKEN or not WA_PHONE_ID:
        raise HTTPException(
            status_code=424,
            detail="WhatsApp credentials not configured. Set META_WHATSAPP_TOKEN and META_PHONE_NUMBER_ID in your .env file.",
        )

    phone = re.sub(r"\D", "", body.phone)
    if not phone:
        raise HTTPException(status_code=400, detail="Invalid phone number")

    payload = _wa_text(phone, body.message)

    url = WA_API_URL.format(phone_id=WA_PHONE_ID)
    headers = {
        "Authorization": f"Bearer {WA_TOKEN}",
        "Content-Type": "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code >= 400:
                raise HTTPException(
                    status_code=resp.status_code,
                    detail=f"Meta API error: {resp.text[:400]}",
                )
            return {"status": "sent", "to": phone, "meta_response": resp.json()}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@whatsapp_router.get("/debug-credentials", summary="Check WhatsApp credentials are loaded (no auth required)")
async def wa_debug_credentials():
    """Quick check to see what credentials are loaded. Does NOT send a message."""
    return {
        "phone_id": WA_PHONE_ID or "❌ EMPTY",
        "token_set": bool(WA_TOKEN),
        "token_prefix": WA_TOKEN[:20] + "..." if WA_TOKEN else "❌ EMPTY",
        "verify_token": WA_VERIFY_TOKEN or "❌ EMPTY",
        "api_url": WA_API_URL.format(phone_id=WA_PHONE_ID or "<NOT_SET>"),
    }

