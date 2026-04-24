"""
School AI Agent — Chat Assistant
─────────────────────────────────
• If LLM_PROVIDER="groq" or "openai" in .env → uses real LLM with tool-calling
• Otherwise → sophisticated rule-based agent with rich DB queries
Both paths share the same tool registry that queries the school's live database.
"""
from __future__ import annotations

import re
import json
import logging
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_school_id, get_current_user
from app.db.session import get_db
from app.models.auth import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat Assistant"])


# ─── Schemas ─────────────────────────────────────────────────────────────────

class ConversationMessage(BaseModel):
    role: str        # "user" | "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[ConversationMessage] = []

class ChatResponse(BaseModel):
    answer: str
    type: str            # "data" | "faq" | "action" | "clarify" | "fallback"
    cards: List[Dict[str, Any]] = []      # rich data cards / mini-tables
    actions: List[Dict[str, str]] = []    # [{label, path}]
    suggestions: List[str] = []

class FAQItem(BaseModel):
    question: str
    answer: str
    category: str


# ══════════════════════════════════════════════════════════════════════════════
# DB HELPERS
# ══════════════════════════════════════════════════════════════════════════════

async def _q(db: AsyncSession, sql: str, params: dict) -> List[dict]:
    result = await db.execute(text(sql), params)
    cols = list(result.keys())
    return [dict(zip(cols, row)) for row in result.fetchall()]

async def _scalar(db: AsyncSession, sql: str, params: dict) -> Any:
    result = await db.execute(text(sql), params)
    row = result.fetchone()
    return row[0] if row and row[0] is not None else 0


# ══════════════════════════════════════════════════════════════════════════════
# TOOL IMPLEMENTATIONS  — each queries live school DB
# ══════════════════════════════════════════════════════════════════════════════

async def tool_student_summary(db, school_id, class_name=None, section=None):
    p: dict = {"school_id": school_id}
    where = "s.school_id = :school_id AND s.is_active = 1"
    if class_name:
        p["class_name"] = f"%{class_name}%"
        where += " AND LOWER(c.name) LIKE LOWER(:class_name)"
    if section:
        p["section"] = f"%{section}%"
        where += " AND LOWER(cs.name) LIKE LOWER(:section)"
    rows = await _q(db, f"""
        SELECT c.name as class_name, cs.name as section_name,
               COUNT(*) as student_count,
               SUM(CASE WHEN s.gender='male' THEN 1 ELSE 0 END) as boys,
               SUM(CASE WHEN s.gender='female' THEN 1 ELSE 0 END) as girls
        FROM students s
        JOIN class_sections cs ON s.section_id = cs.id
        JOIN classes c ON cs.class_id = c.id
        WHERE {where}
        GROUP BY c.name, cs.name ORDER BY c.name, cs.name
    """, p)
    return {"total": sum(r["student_count"] for r in rows), "breakdown": rows}


async def tool_attendance_today(db, school_id, class_name=None):
    p: dict = {"school_id": school_id}
    cf = ""
    if class_name:
        p["class_name"] = f"%{class_name}%"
        cf = "AND LOWER(c.name) LIKE LOWER(:class_name)"
    rows = await _q(db, f"""
        SELECT sa.status, COUNT(*) as cnt
        FROM student_attendance sa
        JOIN attendance_sessions ats ON sa.session_id=ats.id
        LEFT JOIN students s ON sa.student_id=s.id
        LEFT JOIN class_sections cs ON s.section_id=cs.id
        LEFT JOIN classes c ON cs.class_id=c.id
        WHERE sa.school_id=:school_id AND ats.date=CAST(NOW() AS DATE) {cf}
        GROUP BY sa.status
    """, p)
    sm = {r["status"]: r["cnt"] for r in rows}
    present, absent, late = sm.get("present", 0), sm.get("absent", 0), sm.get("late", 0)
    total = present + absent + late
    absent_list = await _q(db, f"""
        SELECT s.first_name||' '||s.last_name as name,
               c.name as class_name, cs.name as section
        FROM student_attendance sa
        JOIN attendance_sessions ats ON sa.session_id=ats.id
        JOIN students s ON sa.student_id=s.id
        JOIN class_sections cs ON s.section_id=cs.id
        JOIN classes c ON cs.class_id=c.id
        WHERE sa.school_id=:school_id AND ats.date=CAST(NOW() AS DATE LIMIT 15)
          AND sa.status='absent' {cf}
        ORDER BY c.name, s.first_name
    """, p)
    return {
        "date": str(date.today()), "present": present, "absent": absent,
        "late": late, "total": total,
        "rate": round(present/total*100) if total else None,
        "absent_students": absent_list,
    }


async def tool_fee_summary(db, school_id, period="month"):
    p: dict = {"school_id": school_id}
    if period == "today":
        df = "CAST(payment_date AS DATE)=CAST(NOW() AS DATE)"
        label = "Today"
    elif period == "year":
        df = "EXTRACT(YEAR FROM payment_date)=EXTRACT(YEAR FROM NOW())"
        label = "This Year"
    else:
        df = """DATE_TRUNC('month', payment_date)
                =DATE_TRUNC('month', NOW())"""
        label = "This Month"
    collected = await _scalar(db, f"SELECT COALESCE(SUM(amount),0) FROM fee_payments WHERE school_id=:school_id AND {df}", p)
    txns = await _scalar(db, f"SELECT COUNT(*) FROM fee_payments WHERE school_id=:school_id AND {df}", p)
    pend_amt = await _scalar(db, "SELECT COALESCE(SUM(balance_amount),0) FROM fee_invoices WHERE school_id=:school_id AND status NOT IN('paid','cancelled')", p)
    pend_cnt = await _scalar(db, "SELECT COUNT(*) FROM fee_invoices WHERE school_id=:school_id AND status NOT IN('paid','cancelled')", p)
    modes = await _q(db, f"""
        SELECT payment_mode, COUNT(*) as cnt, COALESCE(SUM(amount),0) as total
        FROM fee_payments WHERE school_id=:school_id AND {df}
        GROUP BY payment_mode ORDER BY total DESC
    """, p)
    return {"period": label, "collected": int(collected), "transactions": int(txns),
            "pending_amount": int(pend_amt), "pending_invoices": int(pend_cnt), "by_mode": modes}


async def tool_fee_defaulters(db, school_id, min_amount=0, class_name=None):
    p: dict = {"school_id": school_id, "min_amount": min_amount}
    cf = ""
    if class_name:
        p["class_name"] = f"%{class_name}%"
        cf = "AND LOWER(c.name) LIKE LOWER(:class_name)"
    rows = await _q(db, f"""
        SELECT s.first_name||' '||s.last_name as student_name,
               c.name as class_name, cs.name as section,
               COALESCE(SUM(fi.balance_amount),0) as pending
        FROM fee_invoices fi
        JOIN students s ON fi.student_id=s.id
        JOIN class_sections cs ON s.section_id=cs.id
        JOIN classes c ON cs.class_id=c.id
        WHERE fi.school_id=:school_id AND fi.status NOT IN('paid','cancelled' LIMIT 20)
          AND fi.balance_amount>0 {cf}
        GROUP BY s.id,s.first_name,s.last_name,c.name,cs.name
        HAVING SUM(fi.balance_amount)>=:min_amount
        ORDER BY SUM(fi.balance_amount) DESC
    """, p)
    return {"defaulters": rows, "count": len(rows), "total_pending": int(sum(r["pending"] for r in rows))}


async def tool_staff_summary(db, school_id):
    p = {"school_id": school_id}
    total = await _scalar(db, "SELECT COUNT(*) FROM staff WHERE school_id=:school_id AND is_active=1", p)
    on_leave = await _scalar(db, """
        SELECT COUNT(DISTINCT staff_id) FROM leave_requests
        WHERE school_id=:school_id AND status='approved'
          AND start_date<=CAST(NOW() AS DATE) AND end_date>=CAST(NOW() AS DATE)
    """, p)
    by_dept = await _q(db, """
        SELECT d.name as department, COUNT(s.id) as count
        FROM staff s LEFT JOIN departments d ON s.department_id=d.id
        WHERE s.school_id=:school_id AND s.is_active=1
        GROUP BY d.name ORDER BY count DESC
    """, p)
    return {"total": int(total), "on_leave_today": int(on_leave),
            "present": int(total)-int(on_leave), "by_department": by_dept}


async def tool_class_summary(db, school_id):
    rows = await _q(db, """
        SELECT c.name as class_name, COUNT(DISTINCT cs.id) as sections,
               COUNT(s.id) as students
        FROM classes c
        LEFT JOIN class_sections cs ON cs.class_id=c.id
        LEFT JOIN students s ON s.section_id=cs.id AND s.is_active=1
        WHERE c.school_id=:school_id AND c.is_active=1
        GROUP BY c.id, c.name ORDER BY c.name
    """, {"school_id": school_id})
    return {"classes": rows, "total_classes": len(rows),
            "total_students": sum(r["students"] or 0 for r in rows)}


async def tool_transport_summary(db, school_id):
    p = {"school_id": school_id}
    routes = await _scalar(db, "SELECT COUNT(*) FROM routes WHERE school_id=:school_id AND is_active=1", p)
    vehicles = await _scalar(db, "SELECT COUNT(*) FROM vehicles WHERE school_id=:school_id AND is_active=1", p)
    assigned = await _scalar(db, "SELECT COUNT(*) FROM student_transport WHERE school_id=:school_id AND is_active=1", p)
    details = await _q(db, """
        SELECT r.name, COUNT(st.id) as students, v.registration_number as vehicle
        FROM routes r
        LEFT JOIN student_transport st ON st.route_id=r.id AND st.is_active=1
        LEFT JOIN vehicles v ON r.vehicle_id=v.id
        WHERE r.school_id=:school_id AND r.is_active=1
        GROUP BY r.id,r.name,v.registration_number ORDER BY students DESC
    """, p)
    return {"routes": int(routes), "vehicles": int(vehicles),
            "students_assigned": int(assigned), "route_details": details}


async def tool_library_summary(db, school_id):
    p = {"school_id": school_id}
    try:
        titles = await _scalar(db, "SELECT COUNT(*) FROM books WHERE school_id=:school_id", p)
        copies = await _scalar(db, "SELECT COALESCE(SUM(total_copies),0) FROM books WHERE school_id=:school_id", p)
        issued = await _scalar(db, "SELECT COUNT(*) FROM book_issues WHERE school_id=:school_id AND status='issued'", p)
        overdue = await _scalar(db, "SELECT COUNT(*) FROM book_issues WHERE school_id=:school_id AND status='issued' AND due_date<CAST(NOW() AS DATE)", p)
        return {"titles": int(titles), "total_copies": int(copies), "currently_issued": int(issued), "overdue": int(overdue)}
    except Exception:
        return {"error": "Library data unavailable"}


async def tool_accounting_summary(db, school_id):
    p = {"school_id": school_id}
    try:
        inc_m = await _scalar(db, """SELECT COALESCE(SUM(amount),0) FROM income_entries WHERE school_id=:school_id
            AND DATE_TRUNC('month', entry_date)=DATE_TRUNC('month', NOW())""", p)
        exp_m = await _scalar(db, """SELECT COALESCE(SUM(amount),0) FROM expense_entries WHERE school_id=:school_id
            AND DATE_TRUNC('month', entry_date)=DATE_TRUNC('month', NOW())""", p)
        inc_y = await _scalar(db, "SELECT COALESCE(SUM(amount),0) FROM income_entries WHERE school_id=:school_id AND EXTRACT(YEAR FROM entry_date)=EXTRACT(YEAR FROM NOW())", p)
        exp_y = await _scalar(db, "SELECT COALESCE(SUM(amount),0) FROM expense_entries WHERE school_id=:school_id AND EXTRACT(YEAR FROM entry_date)=EXTRACT(YEAR FROM NOW())", p)
        return {"income_month": int(inc_m), "expense_month": int(exp_m), "net_month": int(inc_m)-int(exp_m),
                "income_year": int(inc_y), "expense_year": int(exp_y), "net_year": int(inc_y)-int(exp_y)}
    except Exception:
        return {"error": "Accounting data unavailable"}


async def tool_exam_info(db, school_id, class_name=None):
    p: dict = {"school_id": school_id}
    cf = ""
    if class_name:
        p["class_name"] = f"%{class_name}%"
        cf = "AND LOWER(c.name) LIKE LOWER(:class_name)"
    upcoming = await _q(db, f"""
        SELECT e.name, e.start_date FROM exams e
        WHERE e.school_id=:school_id AND e.start_date>=CAST(NOW() AS DATE) {cf}
        ORDER BY e.start_date ASC
     LIMIT 5""", p)
    recent = await _q(db, f"""
        SELECT e.name, e.start_date, COUNT(DISTINCT em.student_id) as appeared
        FROM exams e LEFT JOIN exam_marks em ON em.exam_id=e.id
        LEFT JOIN students s ON em.student_id=s.id
        LEFT JOIN class_sections cs ON s.section_id=cs.id
        LEFT JOIN classes c ON cs.class_id=c.id
        WHERE e.school_id=:school_id {cf}
        GROUP BY e.id,e.name,e.start_date ORDER BY e.start_date DESC
     LIMIT 5""", p)
    return {"upcoming": upcoming, "recent": recent}


async def tool_inventory_summary(db, school_id):
    p = {"school_id": school_id}
    try:
        total = await _scalar(db, "SELECT COUNT(*) FROM inventory_items WHERE school_id=:school_id", p)
        low = await _q(db, """
            SELECT name, current_stock, minimum_stock
            FROM inventory_items WHERE school_id=:school_id AND current_stock<=minimum_stock
            ORDER BY (current_stock-minimum_stock) ASC
         LIMIT 5""", p)
        return {"total_items": int(total), "low_stock": low}
    except Exception:
        return {"error": "Inventory data unavailable"}


async def tool_admissions_summary(db, school_id):
    p = {"school_id": school_id}
    try:
        by_status = await _q(db, """
            SELECT status, COUNT(*) as count FROM admission_enquiries
            WHERE school_id=:school_id GROUP BY status ORDER BY count DESC
        """, p)
        this_month = await _scalar(db, """
            SELECT COUNT(*) FROM admission_enquiries WHERE school_id=:school_id
            AND DATE_TRUNC('month', created_at)=DATE_TRUNC('month', NOW())
        """, p)
        return {"by_status": by_status, "this_month": int(this_month)}
    except Exception:
        return {"error": "Admissions data unavailable"}


# ══════════════════════════════════════════════════════════════════════════════
# LLM TOOL DEFINITIONS (OpenAI-compatible function calling)
# ══════════════════════════════════════════════════════════════════════════════

TOOL_DEFS = [
    {"type":"function","function":{"name":"get_student_summary","description":"Get student enrollment count and breakdown by class/section.","parameters":{"type":"object","properties":{"class_name":{"type":"string","description":"Class filter e.g. '5', 'Class 5'. Empty = all."},"section":{"type":"string","description":"Section filter e.g. 'A'. Empty = all."}},"required":[]}}},
    {"type":"function","function":{"name":"get_attendance_today","description":"Get today's attendance — present, absent, late counts and absent student list.","parameters":{"type":"object","properties":{"class_name":{"type":"string","description":"Class filter. Empty = whole school."}},"required":[]}}},
    {"type":"function","function":{"name":"get_fee_summary","description":"Get fee collection and pending fee summary.","parameters":{"type":"object","properties":{"period":{"type":"string","enum":["today","month","year"],"description":"Time period. Default: month"}},"required":[]}}},
    {"type":"function","function":{"name":"get_fee_defaulters","description":"Get students with pending/overdue fees.","parameters":{"type":"object","properties":{"class_name":{"type":"string"},"min_amount":{"type":"integer"}},"required":[]}}},
    {"type":"function","function":{"name":"get_staff_summary","description":"Get staff count, department breakdown, who is on leave today.","parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"get_class_summary","description":"Get class and section breakdown with student counts.","parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"get_transport_summary","description":"Get transport route and vehicle info.","parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"get_library_summary","description":"Get library stats: books, issued, overdue.","parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"get_accounting_summary","description":"Get income and expense figures.","parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"get_exam_info","description":"Get upcoming and recent exam schedule.","parameters":{"type":"object","properties":{"class_name":{"type":"string"}},"required":[]}}},
    {"type":"function","function":{"name":"get_inventory_summary","description":"Get inventory count and low-stock alerts.","parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"get_admissions_summary","description":"Get admission enquiry counts by status.","parameters":{"type":"object","properties":{},"required":[]}}},
]

async def _exec_tool(name: str, args: dict, db, school_id) -> str:
    try:
        dispatch = {
            "get_student_summary": lambda: tool_student_summary(db, school_id, args.get("class_name"), args.get("section")),
            "get_attendance_today": lambda: tool_attendance_today(db, school_id, args.get("class_name")),
            "get_fee_summary": lambda: tool_fee_summary(db, school_id, args.get("period","month")),
            "get_fee_defaulters": lambda: tool_fee_defaulters(db, school_id, args.get("min_amount",0), args.get("class_name")),
            "get_staff_summary": lambda: tool_staff_summary(db, school_id),
            "get_class_summary": lambda: tool_class_summary(db, school_id),
            "get_transport_summary": lambda: tool_transport_summary(db, school_id),
            "get_library_summary": lambda: tool_library_summary(db, school_id),
            "get_accounting_summary": lambda: tool_accounting_summary(db, school_id),
            "get_exam_info": lambda: tool_exam_info(db, school_id, args.get("class_name")),
            "get_inventory_summary": lambda: tool_inventory_summary(db, school_id),
            "get_admissions_summary": lambda: tool_admissions_summary(db, school_id),
        }
        result = await dispatch[name]()
        return json.dumps(result, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ══════════════════════════════════════════════════════════════════════════════
# LLM AGENT PATH
# ══════════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """You are a smart school management assistant. You have access to live school data tools.

Your role:
- Answer questions about this school using the provided tools
- Be concise, clear, and use markdown: **bold** key numbers, use bullet lists for breakdowns
- Use ₹ (Indian Rupee) for monetary values, format large numbers as ₹X.XL or ₹X,XXX
- If attendance is low (<75%) — proactively flag it
- If fee defaults are high — mention action needed
- Stay strictly within school management scope; politely redirect off-topic queries
- Suggest 2-3 relevant follow-up questions at the end of data answers
- Today's date: {today}

Always be helpful, professional, and data-driven."""


async def llm_agent(message: str, history: List[ConversationMessage], db, school_id) -> ChatResponse:
    provider = settings.LLM_PROVIDER.lower()
    api_key = settings.GROQ_API_KEY if provider == "groq" else settings.OPENAI_API_KEY
    model = settings.GROQ_MODEL if provider == "groq" else settings.OPENAI_MODEL
    base_url = "https://api.groq.com/openai/v1" if provider == "groq" else "https://api.openai.com/v1"

    messages: list = [{"role": "system", "content": SYSTEM_PROMPT.format(today=date.today())}]
    for h in history[-6:]:
        messages.append({"role": h.role, "content": h.content})
    messages.append({"role": "user", "content": message})

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    tool_results = []

    for _ in range(5):  # max agent loop iterations
        payload = {
            "model": model, "messages": messages, "tools": TOOL_DEFS,
            "tool_choice": "auto", "max_tokens": settings.LLM_MAX_TOKENS,
            "temperature": settings.LLM_TEMPERATURE,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(f"{base_url}/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()

        choice = resp.json()["choices"][0]
        msg = choice["message"]
        messages.append(msg)

        if not msg.get("tool_calls"):
            answer = msg.get("content", "").strip()
            return ChatResponse(
                answer=answer, type="data",
                actions=_nav_actions_from_text(answer),
                suggestions=_smart_suggestions_llm(tool_results),
                cards=[],
            )

        for tc in msg["tool_calls"]:
            fn_name = tc["function"]["name"]
            fn_args = json.loads(tc["function"]["arguments"] or "{}")
            result_str = await _exec_tool(fn_name, fn_args, db, school_id)
            tool_results.append({"tool": fn_name, "result": json.loads(result_str)})
            messages.append({"role": "tool", "tool_call_id": tc["id"], "content": result_str})

    return await rule_agent(message, db, school_id)


# ══════════════════════════════════════════════════════════════════════════════
# RULE-BASED AGENT — sophisticated fallback with rich cards
# ══════════════════════════════════════════════════════════════════════════════

def _n(t: str) -> str: return t.lower().strip()

def _cls(msg: str) -> Optional[str]:
    m = re.search(r'class\s+(\d+|[ivxIVX]+|[a-zA-Z]+(?:\s+[a-zA-Z]+)?)', msg, re.I)
    return m.group(1).strip() if m else None

def _period(msg: str) -> str:
    m = _n(msg)
    if re.search(r'\btoday\b', m): return "today"
    if re.search(r'\byear\b|\bannual\b', m): return "year"
    return "month"

def _inr(n) -> str:
    n = int(n or 0)
    if n >= 10_00_000: return f"₹{n/10_00_000:.2f}L"
    if n >= 1_00_000: return f"₹{n/1_00_000:.1f}L"
    return f"₹{n:,}"

def _tbl(title: str, headers: List[str], rows: List[list]) -> dict:
    return {"type": "table", "title": title, "headers": headers, "rows": [[str(c) for c in r] for r in rows]}

def _stats(items: List[dict]) -> dict:
    return {"type": "stats", "stats": items}

def _stat(label, value, color="blue") -> dict:
    return {"label": label, "value": str(value), "color": color}

def _action(label, path) -> dict:
    return {"label": label, "path": path}


async def rule_agent(message: str, db, school_id) -> ChatResponse:
    m = _n(message)

    # ── Students ──────────────────────────────────────────────────────────
    if re.search(r'\bstudent|\benroll|\bpupil|how many.{0,10}(student|kid|child)', m):
        cn = _cls(message)
        data = await tool_student_summary(db, school_id, cn)
        total, breakdown = data["total"], data["breakdown"]
        cards = []
        if breakdown:
            rows = [[r["class_name"], r["section_name"], r["student_count"], r.get("boys",0), r.get("girls",0)] for r in breakdown[:20]]
            cards = [_tbl(f"Enrollment {'— Class '+cn.upper() if cn else 'by Class'}", ["Class","Section","Total","Boys","Girls"], rows)]
        answer = f"📊 **{'Class '+cn.upper()+' has' if cn else 'Total'} {total} active student{'s' if total!=1 else ''}**"
        if breakdown and not cn:
            answer += f" across {len(breakdown)} class-sections."
        return ChatResponse(answer=answer, type="data", cards=cards,
            actions=[_action("→ Students", "/students")],
            suggestions=["Today's attendance","Fee defaulters","Staff count",f"Students in class {cn or '5'}"])

    # ── Attendance ────────────────────────────────────────────────────────
    if re.search(r'\battend|\bpresent|\babsent|\bwho is.{0,10}(here|school)', m):
        cn = _cls(message)
        d = await tool_attendance_today(db, school_id, cn)
        if d["total"] == 0:
            return ChatResponse(answer="📋 No attendance recorded for today yet.", type="data",
                actions=[_action("→ Take Attendance", "/attendance")],
                suggestions=["Students in class 5","Total students"])
        rate = d["rate"] or 0
        emoji = "🟢" if rate>=90 else "🟡" if rate>=75 else "🔴"
        lbl = f" — Class {cn.upper()}" if cn else ""
        answer = (f"📋 **Today's Attendance{lbl}**\n\n"
                  f"✅ Present: **{d['present']}** &nbsp; ❌ Absent: **{d['absent']}**"
                  + (f" &nbsp; ⏰ Late: **{d['late']}**" if d["late"] else "")
                  + f"\n{emoji} Rate: **{rate}%**")
        if rate < 75:
            answer += "\n\n⚠️ _Attendance is below 75% — consider sending parent notifications._"
        cards = [_stats([_stat("Present",d["present"],"green"),_stat("Absent",d["absent"],"red"),_stat("Rate",f"{rate}%","green" if rate>=90 else "orange")])]
        if d["absent_students"]:
            cards.append(_tbl("Absent Students", ["Name","Class","Section"],
                [[r["name"],r["class_name"],r["section"]] for r in d["absent_students"]]))
        return ChatResponse(answer=answer, type="data", cards=cards,
            actions=[_action("→ Attendance", "/attendance")],
            suggestions=["Total students","Fee defaulters","Staff on leave today","Yesterday's attendance"])

    # ── Fee defaulters ────────────────────────────────────────────────────
    if re.search(r'\bdefault|\bpending fee|\bunpaid|\boverdue fee|\bfee.{0,10}(due|pending|balance|owe)', m):
        cn = _cls(message)
        d = await tool_fee_defaulters(db, school_id, 0, cn)
        if not d["defaulters"]:
            return ChatResponse(answer=f"✅ No fee defaulters{'in class '+cn.upper() if cn else ''}! All fees cleared.", type="data",
                actions=[_action("→ Fees","  /fees")], suggestions=["Fee collection today"])
        rows = [[r["student_name"],r["class_name"],r["section"],_inr(r["pending"])] for r in d["defaulters"]]
        answer = (f"⚠️ **{d['count']} student{'s' if d['count']!=1 else ''} with pending fees"
                  + (f" in class {cn.upper()}" if cn else "") + f"**\n💰 Total outstanding: **{_inr(d['total_pending'])}**")
        return ChatResponse(answer=answer, type="data",
            cards=[_tbl(f"Fee Defaulters{' — '+cn.upper() if cn else ''}",["Student","Class","Section","Pending"],rows)],
            actions=[_action("→ Fees","/fees")],
            suggestions=["Today's collection","This month collection","Send fee reminder"])

    # ── Fee collection ────────────────────────────────────────────────────
    if re.search(r'\bfee.{0,20}(collect|income|payment|today|month|year|how much)|today.*fee|income.*fee', m):
        p = _period(m)
        d = await tool_fee_summary(db, school_id, p)
        mode_rows = [[r["payment_mode"] or "Unknown", r["cnt"], _inr(r["total"])] for r in d["by_mode"]]
        cards = [_stats([_stat(f"Collected ({d['period']})",_inr(d["collected"]),"green"),
                         _stat("Transactions",d["transactions"],"blue"),
                         _stat("Pending",_inr(d["pending_amount"]),"red")])]
        if mode_rows:
            cards.append(_tbl("By Payment Mode",["Mode","Count","Amount"],mode_rows))
        answer = (f"💰 **Fee Collection — {d['period']}**\n\n"
                  f"✅ Collected: **{_inr(d['collected'])}** ({d['transactions']} transactions)\n"
                  f"⚠️ Pending: **{_inr(d['pending_amount'])}** across {d['pending_invoices']} invoices")
        return ChatResponse(answer=answer, type="data", cards=cards,
            actions=[_action("→ Fees","/fees")],
            suggestions=["Fee defaulters","This year's collection","Fee defaulters in class 5"])

    # ── Staff ─────────────────────────────────────────────────────────────
    if re.search(r'\bstaff|\bteacher|\bemployee|\bfaculty|how many.{0,10}(teacher|staff)', m):
        d = await tool_staff_summary(db, school_id)
        dept_rows = [[r["department"] or "N/A", r["count"]] for r in d["by_department"]]
        cards = [_stats([_stat("Total Staff",d["total"],"blue"),
                         _stat("On Leave Today",d["on_leave_today"],"orange"),
                         _stat("Present Today",d["present"],"green")])]
        if dept_rows:
            cards.append(_tbl("Staff by Department",["Department","Count"],dept_rows))
        answer = (f"👨‍🏫 **Staff: {d['total']} active**\n"
                  f"Present today: **{d['present']}** · On leave: **{d['on_leave_today']}**")
        return ChatResponse(answer=answer, type="data", cards=cards,
            actions=[_action("→ Staff","/staff")],
            suggestions=["How to add staff?","Pending leave requests","Process payroll"])

    # ── Classes ───────────────────────────────────────────────────────────
    if re.search(r'\bclasses?\b|\bsections?\b|how many class', m) and not re.search(r'\bstudent', m):
        d = await tool_class_summary(db, school_id)
        rows = [[r["class_name"],r["sections"],r["students"] or 0] for r in d["classes"]]
        answer = f"🏫 **{d['total_classes']} active classes · {d['total_students']} total students**"
        return ChatResponse(answer=answer, type="data",
            cards=[_tbl("Classes & Enrollment",["Class","Sections","Students"],rows)],
            actions=[_action("→ Classes","/classes")],
            suggestions=["Students in class 5","Add a section","Today's attendance"])

    # ── Transport ─────────────────────────────────────────────────────────
    if re.search(r'\btransport|\bbus\b|\broute\b|\bvehicle|\bvan\b|\bdriver|\bpickup|\bdrop', m):
        d = await tool_transport_summary(db, school_id)
        r_rows = [[r["name"],r["students"],r["vehicle"] or "—"] for r in d["route_details"]]
        answer = f"🚌 **Transport: {d['routes']} routes · {d['vehicles']} vehicles · {d['students_assigned']} students assigned**"
        return ChatResponse(answer=answer, type="data",
            cards=[_stats([_stat("Routes",d["routes"]),_stat("Vehicles",d["vehicles"]),_stat("Students",d["students_assigned"],"green")]),
                   _tbl("Route Details",["Route","Students","Vehicle"],r_rows)] if r_rows else
                  [_stats([_stat("Routes",d["routes"]),_stat("Vehicles",d["vehicles"])])],
            actions=[_action("→ Transport","/transport")],
            suggestions=["How to add transport route?","Assign student to route"])

    # ── Library ────────────────────────────────────────────────────────────
    if re.search(r'\blibrary|\bbook\b|\bborrow|\bissue.{0,10}book|\boverdue', m):
        d = await tool_library_summary(db, school_id)
        if "error" not in d:
            answer = (f"📚 **Library: {d['titles']} titles · {d['total_copies']} copies**\n"
                      f"Issued: **{d['currently_issued']}**" +
                      (f" · ⚠️ Overdue: **{d['overdue']}**" if d["overdue"] else ""))
            return ChatResponse(answer=answer, type="data",
                cards=[_stats([_stat("Titles",d["titles"]),_stat("Copies",d["total_copies"]),
                               _stat("Issued",d["currently_issued"],"blue"),_stat("Overdue",d["overdue"],"red")])],
                actions=[_action("→ Library","/library")],
                suggestions=["How to add a book?","How to issue a book?"])

    # ── Accounting ────────────────────────────────────────────────────────
    if re.search(r'\bincome|\bexpense|\bprofit|\baccounting|\brevenue|\bbudget|\bearning', m):
        d = await tool_accounting_summary(db, school_id)
        if "error" not in d:
            net = d["net_month"]
            answer = (f"📊 **Accounting — This Month**\n"
                      f"Income: **{_inr(d['income_month'])}** · Expense: **{_inr(d['expense_month'])}**\n"
                      f"Net: **{_inr(net)}** {'✅' if net>=0 else '⚠️'}\n\n"
                      f"Year-to-date: Income {_inr(d['income_year'])} · Expense {_inr(d['expense_year'])}")
            return ChatResponse(answer=answer, type="data",
                cards=[_stats([_stat("Income (Month)",_inr(d["income_month"]),"green"),
                               _stat("Expense (Month)",_inr(d["expense_month"]),"red"),
                               _stat("Net (Month)",_inr(net),"green" if net>=0 else "red")])],
                actions=[_action("→ Accounting","/accounting")],
                suggestions=["Fee collection this month","How to add income entry?"])

    # ── Exams ─────────────────────────────────────────────────────────────
    if re.search(r'\bexam|\btest\b|\bmarks\b|\bresult\b|\breport card|\bupcoming', m):
        cn = _cls(message)
        d = await tool_exam_info(db, school_id, cn)
        cards = []
        if d["upcoming"]:
            cards.append(_tbl("Upcoming Exams",["Exam","Date"],[[r["name"],str(r["start_date"])[:10]] for r in d["upcoming"]]))
        if d["recent"]:
            cards.append(_tbl("Recent Exams",["Exam","Date","Students"],[[r["name"],str(r["start_date"])[:10],r["appeared"]] for r in d["recent"]]))
        answer = f"📝 **Exams{' — Class '+cn.upper() if cn else ''}**\n"
        if d["upcoming"]: answer += f"\n{len(d['upcoming'])} upcoming exam(s) scheduled."
        if not d["upcoming"] and not d["recent"]: answer += "\nNo exam data found."
        return ChatResponse(answer=answer, type="data", cards=cards,
            actions=[_action("→ Exams","/exams")],
            suggestions=["How to create an exam?","How to enter marks?","How to generate report cards?"])

    # ── Inventory ─────────────────────────────────────────────────────────
    if re.search(r'\binventory|\bstock|\bsupply|\bstationer', m):
        d = await tool_inventory_summary(db, school_id)
        if "error" not in d:
            cards = []
            answer = f"📦 **Inventory: {d['total_items']} items**"
            if d["low_stock"]:
                cards = [_tbl("⚠️ Low Stock Items",["Item","Current","Minimum"],
                              [[r["name"],r["current_stock"],r["minimum_stock"]] for r in d["low_stock"]])]
                answer += f"\n⚠️ **{len(d['low_stock'])} items low on stock!**"
            return ChatResponse(answer=answer, type="data", cards=cards,
                actions=[_action("→ Inventory","/inventory")],
                suggestions=["How to add inventory?","Purchase order"])

    # ── Admissions ────────────────────────────────────────────────────────
    if re.search(r'\badmission|\benquir|\bapplicat|\bnew.{0,5}student.{0,10}(join|enroll)', m):
        d = await tool_admissions_summary(db, school_id)
        if "error" not in d:
            rows = [[r["status"],r["count"]] for r in d["by_status"]]
            answer = f"📋 **{d['this_month']} admission enquiries this month**"
            return ChatResponse(answer=answer, type="data",
                cards=[_tbl("Admissions by Status",["Status","Count"],rows)] if rows else [],
                actions=[_action("→ Admissions","/admissions")],
                suggestions=["How to add a student?","Total students"])

    # ── FAQ ───────────────────────────────────────────────────────────────
    faq = _faq_match(m)
    if faq:
        return ChatResponse(
            answer=f"**{faq.question}**\n\n{faq.answer}", type="faq",
            actions=_faq_nav(faq.category),
            suggestions=_faq_related(faq.category),
        )

    # ── Fallback ──────────────────────────────────────────────────────────
    return ChatResponse(
        answer=(
            "I can help with school data and how-to guides. Try asking:\n\n"
            "**📊 Live Data:**\n"
            "• _How many students in class 5?_\n"
            "• _Who is absent today?_\n"
            "• _Show fee defaulters_\n"
            "• _Today's fee collection_\n"
            "• _Staff count_\n"
            "• _Upcoming exams_\n\n"
            "**❓ How-to:**\n"
            "• _How to add a student?_\n"
            "• _How to take attendance?_\n"
            "• _How to generate report cards?_"
        ),
        type="fallback",
        suggestions=["Total students","Today's attendance","Fee defaulters","Staff count","Upcoming exams","How to add a student?"],
    )


# ══════════════════════════════════════════════════════════════════════════════
# FAQ DATABASE
# ══════════════════════════════════════════════════════════════════════════════

_FAQ: List[FAQItem] = [
    FAQItem(category="Students",question="How to add a new student?",answer="1. Go to **Students** → **+ Add Student**\n2. Fill personal details, select Class & Section\n3. Upload photo if needed → **Save**\n\n_Tip: Use **Admissions** for full inquiry-to-enrollment flow._"),
    FAQItem(category="Students",question="How to assign fee to a student?",answer="1. **Fees** → **Fee Invoices** → **+ Create Invoice**\n2. Choose student, select fee structure, set due date → **Save**\n\nRecord payment: open invoice → **Record Payment** → enter amount & mode."),
    FAQItem(category="Students",question="How to promote students to next class?",answer="1. **Students** → filter by class → bulk-select\n2. Click **Promote Selected**\n3. Choose target class and new academic year → **Confirm**"),
    FAQItem(category="Classes",question="How to add a class or section?",answer="**Class:** Classes → **+ Add Class** → name & year → Save\n**Section:** Open class → Sections tab → **+ Add Section** → name & capacity → Save"),
    FAQItem(category="Classes",question="How to assign subjects to a class?",answer="1. **Subjects** → **+ Add Subject** → select class\n2. Set name, code, assign teacher → Save\n\nFor timetable: go to **Timetable** → set periods."),
    FAQItem(category="Staff",question="How to add a staff member?",answer="1. **Staff** → **+ Add Staff**\n2. Fill personal info, designation, department, joining date\n3. Set role → **Save**\n\nTo create a login: **Admin** → **Roles** → **+ Invite User**."),
    FAQItem(category="Staff",question="How to process staff payroll?",answer="1. **Staff** → **Payroll** tab\n2. Select month → **Generate Payroll**\n3. Review salary, allowances, deductions\n4. **Approve & Process**\n\nDownload payslips from the payroll list."),
    FAQItem(category="Attendance",question="How to take student attendance?",answer="1. **Attendance** → select Class & Section (date auto = today)\n2. Mark each student: Present / Absent / Late\n3. **Submit Attendance**\n\nMonthly reports: Attendance → Reports tab."),
    FAQItem(category="Fees",question="How to create a fee structure?",answer="1. **Fees** → **Fee Structures** → **+ New Structure**\n2. Name, class(es), frequency (monthly/termly/annual)\n3. Add fee heads with amounts → **Save**\n\nBulk apply: Fees → Invoices → **Bulk Generate**."),
    FAQItem(category="Fees",question="How to record a fee payment?",answer="1. **Fees** → **Invoices** → find invoice\n2. **Record Payment** → enter amount, mode, reference → Save\n\nReceipt auto-generated and printable from invoice."),
    FAQItem(category="Exams",question="How to create an exam and enter marks?",answer="**Create:** Exams → Exam Schedule → **+ New Exam** → set name, type, dates, subjects.\n\n**Enter Marks:** Open exam → **Enter Marks** → select subject & class → fill marks → Save."),
    FAQItem(category="Exams",question="How to generate report cards?",answer="1. **Exams** → **Report Cards** tab\n2. Select exam and class\n3. **Generate Report Cards** → preview & download PDF(s)\n\nCustomise template: Settings → Report Card Templates."),
    FAQItem(category="Transport",question="How to add a transport route and stops?",answer="**Route:** Transport → Routes & Stops → **+ Route** → fill name, start/end point, times → Save.\n**Stops:** Click **🚏 Add/View Stops** on route → **+ Add Stop** → name, morning pickup time, evening drop time → Save.\nAssign students: Transport → **Assignments** tab."),
    FAQItem(category="Library",question="How to add a book and issue it?",answer="**Add:** Library → Books → **+ Add Book** → title, author, ISBN, copies → Save.\n**Issue:** Library → Issues → **+ Issue Book** → select member & book → Save."),
    FAQItem(category="Communication",question="How to send a notice to parents?",answer="1. **Communication** → **Notices** → **+ New Notice**\n2. Set title, message, target (All/Class/Individual)\n3. **Publish**\n\nParents see it in Parent Portal. SMS/email depends on school config."),
    FAQItem(category="Admin",question="How to create a user account?",answer="1. **Admin** → **Roles & Permissions** → **+ Invite User**\n2. Enter email, select role\n3. User receives email to set password."),
    FAQItem(category="Admin",question="How to reset a password?",answer="**Self-service:** Login page → **Forgot Password** → email → check inbox.\n**Admin:** Admin → Roles → find user → **Reset Password**.\n\nLink valid for 1 hour."),
    FAQItem(category="Reports",question="How to generate and export reports?",answer="1. **Reports** from the sidebar\n2. Select report type (Student List, Fee Collection, Attendance, etc.)\n3. Set filters (date, class, section)\n4. **Generate** → **Export PDF/Excel**"),
]

_FAQ_KW: List[Tuple[Tuple[str,...],int]] = [
    (("add student","new student","enroll student","register student","create student"),0),
    (("assign fee","fee to student","create invoice","fee invoice"),1),
    (("promote student","next class","class promotion","transfer student"),2),
    (("add class","new class","add section","new section"),3),
    (("assign subject","add subject","subject to class"),4),
    (("add staff","new staff","create staff","add teacher"),5),
    (("payroll","salary","payslip","pay staff"),6),
    (("take attendance","mark attendance","how.*attendance","record attendance"),7),
    (("fee structure","create fee structure","fee head","new fee structure"),8),
    (("record payment","how to pay","pay fee"),9),
    (("create exam","add exam","enter marks","mark entry"),10),
    (("report card","generate report card"),11),
    (("transport route","add route","add stop","pickup stop"),12),
    (("add book","issue book","library book","borrow book"),13),
    (("notice","circular","send message","notify parent"),14),
    (("create user","user account","staff login","invite user"),15),
    (("reset password","forgot password","change password"),16),
    (("generate report","export report","download report"),17),
]

def _faq_match(msg: str) -> Optional[FAQItem]:
    for keywords, idx in _FAQ_KW:
        if any(re.search(kw, msg) for kw in keywords):
            return _FAQ[idx]
    return None

def _faq_nav(category: str) -> List[dict]:
    return {
        "Students":[_action("→ Students","/students")],
        "Classes":[_action("→ Classes","/classes")],
        "Staff":[_action("→ Staff","/staff")],
        "Attendance":[_action("→ Attendance","/attendance")],
        "Fees":[_action("→ Fees","/fees")],
        "Exams":[_action("→ Exams","/exams")],
        "Transport":[_action("→ Transport","/transport")],
        "Library":[_action("→ Library","/library")],
        "Communication":[_action("→ Communication","/communication")],
        "Admin":[_action("→ Admin","/admin/roles")],
        "Reports":[_action("→ Reports","/reports")],
    }.get(category, [])

def _faq_related(category: str) -> List[str]:
    return {
        "Students":["How to assign fee?","How to take attendance?"],
        "Classes":["Students in class 5","How to assign subjects?"],
        "Staff":["How to process payroll?","Staff on leave today"],
        "Attendance":["Today's attendance","Absent students today"],
        "Fees":["Fee defaulters","Today's fee collection"],
        "Exams":["How to generate report cards?","Upcoming exams"],
        "Transport":["Transport summary","How to assign student to route?"],
        "Library":["Library summary","How to issue a book?"],
        "Communication":["How to send notice?"],
        "Admin":["How to add staff?"],
        "Reports":["How to generate report cards?"],
    }.get(category, ["Total students","Today's attendance"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _nav_actions_from_text(text: str) -> List[dict]:
    actions = []
    pairs = [(r'\bstudent',"/students","→ Students"),(r'\battend',"/attendance","→ Attendance"),
             (r'\bfee',"/fees","→ Fees"),(r'\bstaff',"/staff","→ Staff"),
             (r'\bexam',"/exams","→ Exams"),(r'\btransport',"/transport","→ Transport"),
             (r'\blibrary',"/library","→ Library"),(r'\baccounting',"/accounting","→ Accounting")]
    for pat, path, label in pairs:
        if re.search(pat, text, re.I):
            actions.append(_action(label, path))
            if len(actions) >= 2: break
    return actions

def _smart_suggestions_llm(tool_results: List[dict]) -> List[str]:
    if not tool_results: return ["Total students","Today's attendance","Fee defaulters"]
    tools_used = [r["tool"] for r in tool_results]
    if "get_attendance_today" in tools_used:
        return ["Fee defaulters","Total students","Staff on leave today"]
    if "get_fee_summary" in tools_used or "get_fee_defaulters" in tools_used:
        return ["Today's attendance","Total students","Send fee reminder"]
    if "get_student_summary" in tools_used:
        return ["Today's attendance","Fee defaulters","Class breakdown"]
    return ["Total students","Today's attendance","Fee collection this month"]


# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@router.post("/query", response_model=ChatResponse)
async def chat_query(
    body: ChatRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    msg = body.message.strip()
    if not msg:
        return ChatResponse(answer="Please type a question.", type="fallback")

    # Resolve school_id — optional for super admin
    _raw_school = (
        getattr(request.state, "school_id", None)
        or request.headers.get("X-School-Id")
        or request.query_params.get("school_id")
        or (str(current_user.school_id) if getattr(current_user, "school_id", None) else None)
    )
    if not _raw_school and not getattr(current_user, "is_super_admin", False):
        raise HTTPException(status_code=400, detail="School context not found. Provide X-School-Id header.")
    school_id: Optional[str] = _raw_school

    provider = settings.LLM_PROVIDER.lower()
    has_key = bool(settings.GROQ_API_KEY if provider == "groq" else settings.OPENAI_API_KEY)

    if provider in ("groq", "openai") and has_key:
        try:
            return await llm_agent(msg, body.history, db, school_id)
        except Exception as e:
            logger.warning(f"LLM agent failed, using rule engine: {e}")

    return await rule_agent(msg, db, school_id)


@router.get("/faq", response_model=List[FAQItem])
async def list_faq(_: User = Depends(get_current_user)):
    return _FAQ


@router.get("/suggestions")
async def quick_suggestions(_: User = Depends(get_current_user)):
    return {
        "data_queries": [
            "How many students total?","Students in class 5",
            "Today's attendance","Who is absent today?",
            "Fee defaulters","Today's fee collection",
            "This month's fee collection","Staff count",
            "Staff on leave today","Upcoming exams",
            "Transport summary","Library summary",
            "Low stock inventory","Accounting income this month",
            "Admission enquiries this month",
        ],
        "how_to": [
            "How to add a student?","How to assign fee?",
            "How to take attendance?","How to add a class?",
            "How to process payroll?","How to create fee structure?",
            "How to generate report cards?","How to add transport route?",
            "How to send a notice to parents?","How to reset a password?",
        ],
    }


# ══════════════════════════════════════════════════════════════════════════════
# STATEFUL FLOW ENDPOINT  — multi-turn guided conversations
# ══════════════════════════════════════════════════════════════════════════════

import uuid as _uuid_mod
from datetime import datetime, timezone
from sqlalchemy import select as _select

from app.models.chat_session import ConversationSession
from app.services.chat_flow_engine import FlowEngine, BotResponse as FlowBotResponse


class FlowMessageRequest(BaseModel):
    session_id: Optional[str] = None   # client-provided UUID (web) or phone (WA)
    message: str
    payload: Optional[Dict[str, Any]] = None  # extra data e.g. attendance present_ids/absent_ids


class FlowMessageResponse(BaseModel):
    session_id: str
    text: str
    type: str
    options: List[Dict[str, Any]] = []
    attendance_rows: List[Dict[str, Any]] = []
    table: Optional[Dict[str, Any]] = None
    breadcrumb: str = ""
    session_ended: bool = False
    suggestions: List[str] = []
    cards: List[Dict[str, Any]] = []
    actions: List[Dict[str, str]] = []


_flow_engine = FlowEngine()


async def _get_or_create_session(
    session_id: Optional[str],
    user: User,
    school_id: str,
    channel: str,
    db: AsyncSession,
) -> ConversationSession:
    sid = session_id or str(_uuid_mod.uuid4())
    result = await db.execute(
        _select(ConversationSession).where(ConversationSession.id == sid)
    )
    session = result.scalar_one_or_none()

    if session is None or session.is_expired:
        # Create fresh session
        session = ConversationSession(
            id=sid,
            user_id=str(user.id),
            school_id=school_id,
            channel=channel,
            current_flow=None,
            current_step=None,
        )
        db.add(session)
        await db.flush()

    return session


@router.post("/message", response_model=FlowMessageResponse)
async def chat_flow_message(
    body: FlowMessageRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Multi-turn stateful conversation endpoint.

    Replaces one-shot /query for guided flows such as marking attendance,
    applying leave, looking up student details, etc.
    Super admin does not require a school context.
    """
    # Resolve school_id — optional for super admin
    _raw_school = (
        getattr(request.state, "school_id", None)
        or request.headers.get("X-School-Id")
        or request.query_params.get("school_id")
        or (str(current_user.school_id) if getattr(current_user, "school_id", None) else None)
    )
    if not _raw_school and not getattr(current_user, "is_super_admin", False):
        raise HTTPException(status_code=400, detail="School context not found. Provide X-School-Id header.")
    school_id: Optional[str] = _raw_school

    session = await _get_or_create_session(
        body.session_id, current_user, school_id, "web", db
    )

    response: FlowBotResponse = await _flow_engine.handle(
        session=session,
        message=body.message.strip() or "hi",
        payload=body.payload,
        user=current_user,
        db=db,
        school_id=school_id,
    )

    # Persist session
    await db.commit()
    await db.refresh(session)

    return FlowMessageResponse(
        session_id=session.id,
        text=response.text,
        type=response.type,
        options=[o.model_dump() for o in response.options],
        attendance_rows=[r.model_dump() for r in response.attendance_rows],
        table=response.table.model_dump() if response.table else None,
        breadcrumb=response.breadcrumb,
        session_ended=response.session_ended,
        suggestions=response.suggestions,
        cards=response.cards,
        actions=response.actions,
    )
