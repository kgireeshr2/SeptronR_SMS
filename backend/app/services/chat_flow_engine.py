"""
Chat Flow Engine — Multi-turn Conversational Bot
=================================================
Stateful conversation engine supporting 7 guided flows:
  1. greeting         — role-based menu
  2. student_attendance — mark student attendance for a class/section
  3. staff_attendance   — mark staff attendance for the day
  4. fee               — fee summary, defaulters, student lookup
  5. leave             — staff leave application
  6. marks             — student exam results
  7. student_details   — search and display student card

Works across channels: 'web' (rich UI) and 'whatsapp' (text-based menus).
"""
from __future__ import annotations

import uuid
import logging
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth import User
from app.models.chat_session import ConversationSession

logger = logging.getLogger(__name__)

# ─── Response Schema ─────────────────────────────────────────────────────────

class BotOption(BaseModel):
    id: str
    label: str
    description: str = ""


class AttendanceRow(BaseModel):
    student_id: str
    name: str
    roll_number: str
    default_status: str = "present"  # 'present' | 'absent'


class BotTable(BaseModel):
    title: str
    headers: List[str] = []
    rows: List[Dict[str, Any]] = []


class BotResponse(BaseModel):
    text: str
    type: str  # menu | question | attendance_table | staff_table | data | confirm | success | error
    options: List[BotOption] = []
    attendance_rows: List[AttendanceRow] = []
    table: Optional[BotTable] = None
    breadcrumb: str = ""
    session_ended: bool = False
    suggestions: List[str] = []
    # Legacy compat fields for existing ChatWidget cards/actions:
    cards: List[Dict[str, Any]] = []
    actions: List[Dict[str, str]] = []


# ─── DB helper ───────────────────────────────────────────────────────────────

async def _q(db: AsyncSession, sql: str, params: dict) -> List[Dict[str, Any]]:
    result = await db.execute(text(sql), params)
    cols = list(result.keys())
    return [dict(zip(cols, row)) for row in result.fetchall()]


async def _scalar(db: AsyncSession, sql: str, params: dict) -> Any:
    result = await db.execute(text(sql), params)
    row = result.fetchone()
    return row[0] if row and row[0] is not None else 0


def _new_id() -> str:
    return str(uuid.uuid4())


# ─── Role detection ──────────────────────────────────────────────────────────

async def get_user_role(db: AsyncSession, user: User) -> str:
    """Return the primary role name for a user."""
    if user.is_super_admin:
        return "super_admin"
    rows = await _q(
        db,
        "SELECT r.name FROM roles r JOIN user_roles ur ON r.id = ur.role_id "
        "WHERE ur.user_id = :uid",
        {"uid": str(user.id)},
    )
    names = [str(r["name"]).lower() for r in rows]
    for keyword in ["admin", "principal", "vice_principal", "headmaster"]:
        if any(keyword in n for n in names):
            return "admin"
    for keyword in ["teacher", "faculty", "educator", "instructor"]:
        if any(keyword in n for n in names):
            return "teacher"
    if any("parent" in n for n in names):
        return "parent"
    if any("student" in n for n in names):
        return "student"
    return "staff"


async def get_user_permissions(db: AsyncSession, user: User) -> set:
    """Return a set of 'module:action' permission strings for a user."""
    if user.is_super_admin:
        return {"*:*"}
    rows = await _q(
        db,
        "SELECT DISTINCT p.module, p.action FROM permissions p "
        "JOIN role_permissions rp ON p.id = rp.permission_id "
        "JOIN user_roles ur ON rp.role_id = ur.role_id "
        "WHERE ur.user_id = :uid",
        {"uid": str(user.id)},
    )
    perms: set = set()
    for r in rows:
        perms.add(f"{r['module']}:{r['action']}")
        if r["action"] == "manage":
            perms.update({
                f"{r['module']}:view", f"{r['module']}:create",
                f"{r['module']}:update", f"{r['module']}:delete",
            })
    return perms


def _has_perm(permissions: set, module: str, action: str) -> bool:
    """Check if user has a specific permission."""
    return (
        "*:*" in permissions or
        f"{module}:{action}" in permissions or
        f"{module}:manage" in permissions
    )


# ─── Role-based menus ────────────────────────────────────────────────────────

MENUS: Dict[str, List[Dict[str, str]]] = {
    "super_admin": [
        {"id": "sa_schools",      "label": "Manage Schools",    "description": "View / create schools"},
        {"id": "sa_plans",        "label": "Subscription Plans","description": "Manage plans"},
        {"id": "attendance_today","label": "Today's Attendance","description": "School attendance summary"},
        {"id": "attendance_view",  "label": "View Attendance",   "description": "View class attendance by date"},
        {"id": "accounting",      "label": "Income & Expenses", "description": "Today's income & expenses"},
        {"id": "fee",             "label": "Fee Overview",      "description": "Fee summary across schools"},
        {"id": "student_details",  "label": "Student Info",      "description": "Search student details"},
        {"id": "student_edit",     "label": "Edit Student",      "description": "Search and edit student info"},
    ],
    "admin": [
        {"id": "attendance_today",   "label": "Today's Attendance",  "description": "School-wide summary for today"},
        {"id": "student_attendance", "label": "Mark Attendance",      "description": "Mark class attendance"},
        {"id": "staff_attendance",   "label": "Staff Attendance",    "description": "Mark staff attendance"},
        {"id": "attendance_view",    "label": "View Attendance",     "description": "View class attendance by date"},
        {"id": "fee",                "label": "Fee",                  "description": "Collect & view fee details"},
        {"id": "accounting",         "label": "Income & Expenses",   "description": "Today's income & expenses"},
        {"id": "leave",              "label": "Leave Requests",       "description": "View pending leave requests"},
        {"id": "marks",              "label": "Exam Results",         "description": "View student marks"},
        {"id": "student_details",    "label": "Student Info",         "description": "Search student details"},
        {"id": "student_edit",       "label": "Edit Student",         "description": "Search and edit student info"},
    ],
    "teacher": [
        {"id": "attendance_today",   "label": "Today's Attendance",  "description": "Class attendance summary"},
        {"id": "student_attendance", "label": "Mark Attendance",      "description": "Mark your class attendance"},
        {"id": "attendance_view",    "label": "View Attendance",     "description": "View class attendance by date"},
        {"id": "marks",              "label": "Student Marks",        "description": "View exam results"},
        {"id": "leave",              "label": "Apply Leave",          "description": "Submit leave request"},
        {"id": "student_details",    "label": "Student Info",         "description": "Search student details"},
    ],
    "staff": [
        {"id": "leave",           "label": "Apply Leave",    "description": "Submit leave request"},
        {"id": "fee",             "label": "My Fee Info",    "description": "Fee related info"},
    ],
    "student": [
        {"id": "marks",   "label": "My Marks",      "description": "View exam results"},
        {"id": "fee",     "label": "My Fee",         "description": "Outstanding fee details"},
        {"id": "leave",   "label": "My Attendance",  "description": "Attendance summary"},
    ],
    "parent": [
        {"id": "student_details", "label": "My Child's Info", "description": "View child details"},
        {"id": "marks",           "label": "Results",          "description": "Exam marks"},
        {"id": "fee",             "label": "Fee",              "description": "Due & payments"},
    ],
}

FEE_MENU_OPTIONS = [
    {"id": "fee_summary",    "label": "Fee Summary",       "description": "This month collection"},
    {"id": "fee_collect",   "label": "Collect Fee",       "description": "Record a student payment"},
    {"id": "fee_defaulters", "label": "Defaulters",       "description": "Students with pending fees"},
    {"id": "fee_student",   "label": "Student Lookup",    "description": "Check fee for a student"},
    {"id": "fee_balance",   "label": "Balance Report",    "description": "Day / Month / Year collection & balance"},
]

PAYMENT_METHOD_OPTIONS = [
    {"id": "cash",   "label": "Cash",         "description": ""},
    {"id": "upi",    "label": "UPI",          "description": ""},
    {"id": "online", "label": "Online/NEFT",  "description": ""},
    {"id": "card",   "label": "Card",         "description": ""},
    {"id": "cheque", "label": "Cheque",       "description": ""},
]


# ══════════════════════════════════════════════════════════════════════════════
# FLOW ENGINE
# ══════════════════════════════════════════════════════════════════════════════

class FlowEngine:
    """Stateful conversation engine.

    Usage:
        engine = FlowEngine()
        response = await engine.handle(session, message, payload, user, db, school_id)
    """

    async def handle(
        self,
        session: ConversationSession,
        message: str,
        payload: Optional[Dict[str, Any]],
        user: User,
        db: AsyncSession,
        school_id: str,
    ) -> BotResponse:
        """Route to the correct flow+step handler. Update session in-place."""
        session.touch()
        msg = message.strip()
        msg_lower = msg.lower()

        # Global: "menu", "hi", "hello", "/start", "back to menu" → restart
        if msg_lower in ("menu", "hi", "hello", "/start", "start", "home",
                         "back to menu", "main menu", "0"):
            return await self._start_greeting(session, user, db)

        # Global: "cancel" / "exit" → end session
        if msg_lower in ("cancel", "exit", "quit", "bye", "goodbye"):
            session.current_flow = None
            session.current_step = None
            session.set_context({})
            session.is_active = False
            return BotResponse(
                text="Goodbye! 👋 Type **Hi** anytime to start again.",
                type="success",
                session_ended=True,
            )

        # No active flow → treat as greeting
        if not session.current_flow:
            # Check if message is one of the menu option IDs or keywords
            role = await get_user_role(db, user)
            options = MENUS.get(role, MENUS["staff"])
            matched = next((o for o in options if o["id"] == msg_lower or
                           o["label"].lower() in msg_lower), None)
            if matched:
                return await self._route_flow(matched["id"], session, msg, payload, user, db, school_id)
            # Also accept any valid flow ID directly (e.g. typing 'student_edit' directly)
            _all_flow_ids = {
                "greeting", "attendance_today", "student_attendance", "staff_attendance",
                "attendance_view", "fee", "accounting", "leave", "marks",
                "student_details", "student_edit", "sa_schools", "sa_plans",
            }
            if msg_lower in _all_flow_ids:
                return await self._route_flow(msg_lower, session, msg, payload, user, db, school_id)
            # Otherwise show the greeting menu
            return await self._start_greeting(session, user, db)

        # Active flow — route to handler
        return await self._route_flow(
            session.current_flow, session, msg, payload, user, db, school_id
        )

    # ── Router ────────────────────────────────────────────────────────────────

    async def _route_flow(
        self,
        flow: str,
        session: ConversationSession,
        message: str,
        payload: Optional[Dict],
        user: User,
        db: AsyncSession,
        school_id: str,
    ) -> BotResponse:
        session.current_flow = flow
        handlers = {
            "greeting":           self._flow_greeting,
            "attendance_today":   self._flow_attendance_today,
            "student_attendance": self._flow_student_attendance,
            "staff_attendance":   self._flow_staff_attendance,
            "attendance_view":    self._flow_attendance_view,
            "fee":                self._flow_fee,
            "accounting":         self._flow_accounting,
            "leave":              self._flow_leave,
            "marks":              self._flow_marks,
            "student_details":    self._flow_student_details,
            "student_edit":       self._flow_student_edit,
            "sa_schools":         self._flow_sa_schools,
            "sa_plans":           self._flow_sa_plans,
        }
        handler = handlers.get(flow)
        if not handler:
            session.current_flow = None
            return await self._start_greeting(session, user, db)
        try:
            return await handler(session, message, payload, user, db, school_id)
        except Exception as exc:
            logger.exception("FlowEngine error in flow=%s step=%s", flow, session.current_step)
            return BotResponse(
                text=f"⚠️ Something went wrong: {exc}\n\nType **menu** to start over.",
                type="error",
            )

    # ─── GREETING ─────────────────────────────────────────────────────────────

    async def _start_greeting(
        self, session: ConversationSession, user: User, db: AsyncSession
    ) -> BotResponse:
        session.current_flow = None
        session.current_step = None
        session.set_context({})
        role = await get_user_role(db, user)
        options = MENUS.get(role, MENUS["staff"])
        name = (user.first_name or user.username or "there")
        greeting = (
            f"👋 Hi **{name}**! I'm your School Assistant.\n"
            f"What would you like to do today?"
        )
        return BotResponse(
            text=greeting,
            type="menu",
            options=[BotOption(**o) for o in options],
            suggestions=["Hi", "Menu"],
        )

    async def _flow_greeting(
        self, session, message, payload, user, db, school_id
    ) -> BotResponse:
        return await self._start_greeting(session, user, db)

    # ─── STUDENT ATTENDANCE ───────────────────────────────────────────────────

    async def _flow_student_attendance(
        self, session, message, payload, user, db, school_id
    ) -> BotResponse:
        step = session.current_step or "select_class"

        if step == "select_class":
            return await self._sa_select_class(session, db, school_id)

        if step == "select_section":
            return await self._sa_select_section(session, message, db, school_id)

        if step == "load_students":
            return await self._sa_load_students(session, message, db, school_id)

        if step == "save":
            return await self._sa_save(session, payload, user, db, school_id)

        return await self._sa_select_class(session, db, school_id)

    async def _sa_select_class(self, session, db, school_id) -> BotResponse:
        classes = await _q(
            db,
            "SELECT id, name FROM classes WHERE school_id = :sid AND is_active = 1 "
            "ORDER BY name",
            {"sid": school_id},
        )
        if not classes:
            return BotResponse(text="No classes found in this school.", type="error")
        session.current_step = "select_section"
        session.set_context({})
        options = [BotOption(id=str(c["id"]), label=c["name"]) for c in classes]
        return BotResponse(
            text="📚 **Student Attendance**\n\nSelect a class:",
            type="options",
            options=options,
            breadcrumb="Attendance",
        )

    async def _sa_select_section(self, session, message, db, school_id) -> BotResponse:
        ctx = session.context

        # First time entering this step — message is the class_id or class name
        if "class_id" not in ctx:
            # Try matching by class id (option button clicked) or by name
            classes = await _q(
                db,
                "SELECT id, name FROM classes WHERE school_id = :sid AND is_active = 1",
                {"sid": school_id},
            )
            # Match by id or label
            matched = next(
                (c for c in classes if str(c["id"]) == message or
                 c["name"].lower() == message.lower()), None
            )
            if not matched:
                # Try partial name match
                matched = next((c for c in classes if message.lower() in c["name"].lower()), None)
            if not matched:
                return BotResponse(
                    text=f"Class '{message}' not found. Please select from the list.",
                    type="options",
                    options=[BotOption(id=str(c["id"]), label=c["name"]) for c in classes],
                    breadcrumb="Attendance",
                )
            session.patch_context({"class_id": str(matched["id"]), "class_name": matched["name"]})
            ctx = session.context

        # Load sections for the selected class
        sections = await _q(
            db,
            "SELECT id, name FROM sections WHERE class_id = :cid AND is_active = 1 ORDER BY name",
            {"cid": ctx["class_id"]},
        )
        if not sections:
            return BotResponse(
                text=f"No sections found for class {ctx['class_name']}.", type="error"
            )
        if len(sections) == 1:
            # Auto-select if only one section
            section = sections[0]
            session.patch_context({"section_id": str(section["id"]), "section_name": section["name"]})
            session.current_step = "load_students"
            return await self._sa_load_students(session, str(section["id"]), db, school_id)

        session.current_step = "load_students"
        return BotResponse(
            text=f"Select a section for **{ctx['class_name']}**:",
            type="options",
            options=[BotOption(id=str(s["id"]), label=s["name"]) for s in sections],
            breadcrumb=f"Attendance › {ctx['class_name']}",
        )

    async def _sa_load_students(self, session, message, db, school_id) -> BotResponse:
        ctx = session.context

        # message is the section_id if arriving from section selection
        if "section_id" not in ctx:
            sections = await _q(
                db,
                "SELECT id, name FROM sections WHERE class_id = :cid AND is_active = 1",
                {"cid": ctx.get("class_id", "")},
            )
            matched = next(
                (s for s in sections if str(s["id"]) == message or
                 s["name"].lower() == message.lower()), None
            )
            if not matched:
                matched = next((s for s in sections if message.lower() in s["name"].lower()), None)
            if not matched:
                return BotResponse(
                    text="Section not found. Please select from the list.",
                    type="options",
                    options=[BotOption(id=str(s["id"]), label=s["name"]) for s in sections],
                )
            session.patch_context({"section_id": str(matched["id"]), "section_name": matched["name"]})
            ctx = session.context

        # Check if attendance is already taken today
        existing = await _q(
            db,
            "SELECT id FROM attendance_sessions "
            "WHERE school_id = :sid AND section_id = :sec_id "
            "AND date = CAST(NOW() AS DATE) AND session_type = 'full_day'",
            {"sid": school_id, "sec_id": ctx["section_id"]},
        )
        if existing:
            session.current_flow = None
            session.current_step = None
            class_name = ctx.get("class_name", "")
            section_name = ctx.get("section_name", "")
            return BotResponse(
                text=f"✅ Attendance for **{class_name} - {section_name}** has already been "
                     f"marked today.\n\nType **menu** to go back.",
                type="info",
                actions=[{"label": "View Attendance", "path": "/attendance"}],
                session_ended=True,
            )

        # Load students via student_enrollments (section_id and roll_number live there)
        students = await _q(
            db,
            "SELECT s.id, s.first_name, s.last_name, "
            "COALESCE(se.roll_number, '') AS roll_number "
            "FROM students s "
            "JOIN student_enrollments se ON se.student_id = s.id "
            "   AND se.section_id = :sec_id AND se.school_id = :sid AND se.is_current = 1 "
            "WHERE s.school_id = :sid AND s.is_active = 1 "
            "ORDER BY se.roll_number, s.first_name",
            {"sec_id": ctx["section_id"], "sid": school_id},
        )
        if not students:
            session.current_flow = None
            return BotResponse(text="No students found in this section.", type="error")

        session.current_step = "save"
        class_name = ctx.get("class_name", "")
        section_name = ctx.get("section_name", "")

        rows = [
            AttendanceRow(
                student_id=str(s["id"]),
                name=f"{s['first_name']} {s['last_name']}".strip(),
                roll_number=str(s["roll_number"] or ""),
                default_status="present",
            )
            for s in students
        ]
        return BotResponse(
            text=f"Mark attendance for **{class_name} - {section_name}** "
                 f"({len(rows)} students).\n\nToggle absent students then tap **Save**.",
            type="attendance_table",
            attendance_rows=rows,
            breadcrumb=f"Attendance › {class_name} › {section_name}",
        )

    async def _sa_save(self, session, payload, user, db, school_id) -> BotResponse:
        ctx = session.context
        if not payload:
            return BotResponse(
                text="Please submit attendance data.", type="error"
            )
        present_ids: List[str] = payload.get("present_ids", [])
        absent_ids: List[str] = payload.get("absent_ids", [])

        # Get class_id for the section
        section_info = await _q(
            db,
            "SELECT class_id FROM sections WHERE id = :sec_id",
            {"sec_id": ctx.get("section_id", "")},
        )
        if not section_info:
            return BotResponse(text="Section not found.", type="error")
        class_id = str(section_info[0]["class_id"])

        # Create attendance session
        session_id = _new_id()
        await db.execute(
            text(
                "INSERT INTO attendance_sessions "
                "(id, school_id, session_type, date, class_id, section_id, taken_by, is_finalized, created_at) "
                "VALUES (:id, :sid, 'full_day', CAST(NOW() AS DATE), :cid, :sec_id, :taken_by, 0, NOW())"
            ),
            {
                "id": session_id,
                "sid": school_id,
                "cid": class_id,
                "sec_id": ctx.get("section_id"),
                "taken_by": str(user.id),
            },
        )

        # Insert attendance records
        for sid in present_ids:
            await db.execute(
                text(
                    "INSERT INTO student_attendance "
                    "(id, school_id, session_id, student_id, status, created_at, updated_at) "
                    "VALUES (:id, :sid, :sess_id, :stud_id, 'present', NOW(), NOW())"
                ),
                {"id": _new_id(), "sid": school_id, "sess_id": session_id, "stud_id": sid},
            )
        for sid in absent_ids:
            await db.execute(
                text(
                    "INSERT INTO student_attendance "
                    "(id, school_id, session_id, student_id, status, created_at, updated_at) "
                    "VALUES (:id, :sid, :sess_id, :stud_id, 'absent', NOW(), NOW())"
                ),
                {"id": _new_id(), "sid": school_id, "sess_id": session_id, "stud_id": sid},
            )
        await db.commit()

        section_name = ctx.get("section_name", "")
        class_name = ctx.get("class_name", "")
        session.current_flow = None
        session.current_step = None
        session.set_context({})

        return BotResponse(
            text=(
                f"✅ **Attendance Saved!**\n\n"
                f"Class: {class_name} - {section_name}\n"
                f"✔ Present: {len(present_ids)}  ✖ Absent: {len(absent_ids)}\n\n"
                f"Type **menu** to continue."
            ),
            type="success",
            actions=[{"label": "View Attendance", "path": "/attendance"}],
            session_ended=True,
        )

    # ─── STAFF ATTENDANCE ────────────────────────────────────────────────────

    async def _flow_staff_attendance(
        self, session, message, payload, user, db, school_id
    ) -> BotResponse:
        step = session.current_step or "load_staff"

        if step == "load_staff":
            return await self._sta_load_staff(session, db, school_id)

        if step == "save":
            return await self._sta_save(session, payload, user, db, school_id)

        return await self._sta_load_staff(session, db, school_id)

    async def _sta_load_staff(self, session, db, school_id) -> BotResponse:
        # Check if already marked today
        existing_count = await _scalar(
            db,
            "SELECT COUNT(*) FROM staff_attendance "
            "WHERE school_id = :sid AND date = CAST(NOW() AS DATE)",
            {"sid": school_id},
        )

        staff = await _q(
            db,
            "SELECT id, first_name, last_name, employee_id, "
            "COALESCE(CAST(department_id AS VARCHAR(36)), '') AS dept_id "
            "FROM staff WHERE school_id = :sid AND is_active = 1 "
            "ORDER BY first_name",
            {"sid": school_id},
        )
        if not staff:
            return BotResponse(text="No active staff found.", type="error")

        session.current_step = "save"

        rows = [
            AttendanceRow(
                student_id=str(s["id"]),  # reuse field for staff_id
                name=f"{s['first_name']} {s['last_name']}".strip(),
                roll_number=str(s["employee_id"] or ""),
                default_status="present",
            )
            for s in staff
        ]
        note = f"ℹ️ {existing_count} records already marked today. Adding new ones." if existing_count else ""
        return BotResponse(
            text=f"👥 **Staff Attendance** — {len(rows)} staff members.\n"
                 f"{note}\nToggle absent staff and tap **Save**.",
            type="staff_table",
            attendance_rows=rows,
            breadcrumb="Staff Attendance",
        )

    async def _sta_save(self, session, payload, user, db, school_id) -> BotResponse:
        if not payload:
            return BotResponse(text="Please submit attendance data.", type="error")

        present_ids: List[str] = payload.get("present_ids", [])
        absent_ids: List[str] = payload.get("absent_ids", [])

        for sid in present_ids:
            # MERGE / INSERT IGNORE pattern for MSSQL
            await db.execute(
                text(
                    "IF NOT EXISTS (SELECT 1 FROM staff_attendance WHERE staff_id = :sid AND date = CAST(NOW() AS DATE)) "
                    "INSERT INTO staff_attendance "
                    "(id, school_id, staff_id, date, status, source, created_at, updated_at) "
                    "VALUES (:id, :school_id, :sid, CAST(NOW() AS DATE), 'present', 'manual', NOW(), NOW())"
                ),
                {"id": _new_id(), "school_id": school_id, "sid": sid},
            )
        for sid in absent_ids:
            await db.execute(
                text(
                    "IF NOT EXISTS (SELECT 1 FROM staff_attendance WHERE staff_id = :sid AND date = CAST(NOW() AS DATE)) "
                    "INSERT INTO staff_attendance "
                    "(id, school_id, staff_id, date, status, source, created_at, updated_at) "
                    "VALUES (:id, :school_id, :sid, CAST(NOW() AS DATE), 'absent', 'manual', NOW(), NOW())"
                ),
                {"id": _new_id(), "school_id": school_id, "sid": sid},
            )
        await db.commit()

        session.current_flow = None
        session.current_step = None
        session.set_context({})
        return BotResponse(
            text=(
                f"✅ **Staff Attendance Saved!**\n\n"
                f"✔ Present: {len(present_ids)}  ✖ Absent: {len(absent_ids)}\n\n"
                f"Type **menu** to continue."
            ),
            type="success",
            actions=[{"label": "Staff Attendance Report", "path": "/staff-attendance"}],
            session_ended=True,
        )

    # ─── FEE ─────────────────────────────────────────────────────────────────

    async def _flow_fee(
        self, session, message, payload, user, db, school_id
    ) -> BotResponse:
        step = session.current_step or "fee_menu"
        role = await get_user_role(db, user)

        # For student/parent: jump straight to their fee info
        if role in ("student", "parent") and step == "fee_menu":
            return await self._fee_student_info(session, user, db, school_id)

        if step == "fee_menu":
            session.current_step = "fee_action"
            return BotResponse(
                text="💰 **Fee Section** — What would you like to see?",
                type="options",
                options=[BotOption(**o) for o in FEE_MENU_OPTIONS],
                breadcrumb="Fee",
            )

        if step == "fee_action":
            return await self._fee_dispatch(session, message, user, db, school_id)

        if step == "fee_student_search":
            return await self._fee_student_lookup(session, message, db, school_id)

        # Fee collect steps
        if step == "fee_collect_search":
            return await self._fee_collect_find_student(session, message, db, school_id)
        if step == "fee_collect_invoice":
            return await self._fee_collect_pick_invoice(session, message, db, school_id)
        if step == "fee_collect_method":
            return await self._fee_collect_pick_method(session, message)
        if step == "fee_collect_confirm":
            return await self._fee_collect_confirm(session, message, user, db, school_id)

        if step == "fee_balance_period":
            return await self._fee_balance_report(session, message, db, school_id)

        return BotResponse(text="Type **menu** to go back.", type="info")

    async def _fee_dispatch(self, session, message, user, db, school_id) -> BotResponse:
        msg = message.lower()
        if message in ("fee_summary", ) or "summary" in msg:
            return await self._fee_summary(session, db, school_id)
        if message in ("fee_defaulters", ) or "default" in msg:
            return await self._fee_defaulters(session, db, school_id)
        if message in ("fee_collect", ) or "collect" in msg or "pay" in msg:
            session.current_step = "fee_collect_search"
            return BotResponse(
                text="💳 **Collect Fee**\n\nEnter student name or admission number:",
                type="question",
                breadcrumb="Fee › Collect",
            )
        if message in ("fee_student", ) or "student" in msg or "lookup" in msg:
            session.current_step = "fee_student_search"
            return BotResponse(
                text="Enter student name or admission number:",
                type="question",
                breadcrumb="Fee › Student Lookup",
            )
        if message in ("fee_balance", ) or "balance" in msg or ("report" in msg and "fee" in msg):
            session.current_step = "fee_balance_period"
            return BotResponse(
                text="📊 **Balance Report** — Select period:",
                type="options",
                options=[
                    BotOption(id="fee_balance_today", label="Today",      description="Today's collection & balance"),
                    BotOption(id="fee_balance_month", label="This Month",  description="Current month summary"),
                    BotOption(id="fee_balance_year",  label="This Year",   description="Annual collection summary"),
                ],
                breadcrumb="Fee › Balance Report",
            )
        # Unknown — re-show menu
        session.current_step = "fee_action"
        return BotResponse(
            text="Please select an option:",
            type="options",
            options=[BotOption(**o) for o in FEE_MENU_OPTIONS],
            breadcrumb="Fee",
        )

    async def _fee_summary(self, session, db, school_id) -> BotResponse:
        session.current_flow = None
        session.current_step = None

        s_where = "AND school_id = :sid" if school_id else ""
        s_p: Dict[str, Any] = {"sid": school_id} if school_id else {}

        collected_month = await _scalar(
            db,
            f"SELECT COALESCE(SUM(amount),0) FROM fee_payments "
            f"WHERE 1=1 {s_where} "
            "AND EXTRACT(YEAR FROM payment_date) = EXTRACT(YEAR FROM NOW()) AND EXTRACT(MONTH FROM payment_date) = EXTRACT(MONTH FROM NOW())",
            s_p,
        )
        collected_total = await _scalar(
            db,
            f"SELECT COALESCE(SUM(amount),0) FROM fee_payments WHERE 1=1 {s_where}",
            s_p,
        )
        outstanding = await _scalar(
            db,
            f"SELECT COALESCE(SUM(balance_amount),0) FROM fee_invoices "
            f"WHERE 1=1 {s_where} AND status NOT IN ('paid','cancelled')",
            s_p,
        )
        defaulters = await _scalar(
            db,
            f"SELECT COUNT(DISTINCT student_id) FROM fee_invoices "
            f"WHERE 1=1 {s_where} AND status NOT IN ('paid','cancelled') AND balance_amount > 0",
            s_p,
        )

        def fmt(p): return f"Rs.{int(p):,}" if p else "Rs.0"

        return BotResponse(
            text=(
                f"💰 **Fee Summary**\n\n"
                f"This Month Collected: **{fmt(collected_month)}**\n"
                f"Total Collected: **{fmt(collected_total)}**\n"
                f"Outstanding: **{fmt(outstanding)}**\n"
                f"Defaulters: **{defaulters} students**\n\n"
                f"Type **menu** to continue."
            ),
            type="data",
            cards=[{
                "type": "stats",
                "stats": [
                    {"label": "This Month", "value": fmt(collected_month), "color": "green"},
                    {"label": "Total Collected", "value": fmt(collected_total), "color": "blue"},
                    {"label": "Outstanding", "value": fmt(outstanding), "color": "red"},
                    {"label": "Defaulters", "value": str(defaulters), "color": "orange"},
                ],
            }],
            actions=[{"label": "Fee Management", "path": "/fees"}],
            session_ended=True,
        )

    async def _fee_defaulters(self, session, db, school_id) -> BotResponse:
        session.current_flow = None
        session.current_step = None

        s_where = "fi.school_id = :sid AND" if school_id else ""
        s_p: Dict[str, Any] = {"sid": school_id} if school_id else {}

        rows = await _q(
            db,
            f"""SELECT s.first_name + ' ' + s.last_name AS student_name,
                 s.admission_number,
                 c.name AS class_name,
                 COALESCE(SUM(fi.balance_amount),0) AS balance
               FROM fee_invoices fi
               JOIN students s ON fi.student_id = s.id
               LEFT JOIN student_enrollments se ON se.student_id = s.id AND se.is_current = 1
               LEFT JOIN classes c ON se.class_id = c.id
               WHERE {s_where if s_where else '1=1 AND'} fi.status NOT IN ('paid','cancelled' LIMIT 20)
                 AND fi.balance_amount > 0
               GROUP BY s.id, s.first_name, s.last_name, s.admission_number, c.name
               ORDER BY balance DESC""",
            s_p,
        )

        def fmt(p): return f"Rs.{int(p):,}" if p else "Rs.0"

        table_rows = [[r["student_name"], r["admission_number"], r["class_name"],
                       fmt(r["balance"])] for r in rows]

        return BotResponse(
            text=f"📋 **Fee Defaulters** — Top {len(rows)} by outstanding amount.",
            type="data",
            cards=[{
                "type": "table",
                "title": "Fee Defaulters",
                "headers": ["Student", "Admission No", "Class", "Outstanding"],
                "rows": table_rows,
            }],
            actions=[{"label": "Fee Management", "path": "/fees"}],
            session_ended=True,
        )

    async def _fee_student_lookup(self, session, message, db, school_id) -> BotResponse:
        session.current_flow = None

        s_where = "AND s.school_id = :sid" if school_id else ""
        s_p: Dict[str, Any] = {"sid": school_id, "q": f"%{message}%"} if school_id else {"q": f"%{message}%"}

        rows = await _q(
            db,
            f"""SELECT s.first_name + ' ' + s.last_name AS name,
                 s.admission_number, c.name AS class_name,
                 COALESCE(SUM(fi.balance_amount),0) AS balance
               FROM students s
               LEFT JOIN fee_invoices fi ON fi.student_id = s.id
                 AND fi.status NOT IN ('paid','cancelled' LIMIT 5)
               LEFT JOIN student_enrollments se ON se.student_id = s.id AND se.is_current = 1
               LEFT JOIN classes c ON se.class_id = c.id
               WHERE s.is_active = 1 {s_where}
                 AND (
                   LOWER(s.first_name + ' ' + s.last_name) LIKE LOWER(:q)
                   OR LOWER(s.admission_number) LIKE LOWER(:q)
                 )
               GROUP BY s.id, s.first_name, s.last_name, s.admission_number, c.name""",
            s_p,
        )

        def fmt(p): return f"Rs.{int(p):,}" if p else "Rs.0"

        if not rows:
            return BotResponse(
                text=f"No students found matching **{message}**.\n\nType **menu** to go back.",
                type="info",
                session_ended=True,
            )

        table_rows = [[r["name"], r["admission_number"], r["class_name"], fmt(r["balance"])]
                      for r in rows]
        return BotResponse(
            text=f"Fee info for '{message}':",
            type="data",
            cards=[{
                "type": "table",
                "title": "Student Fee Lookup",
                "headers": ["Student", "Admission No", "Class", "Outstanding"],
                "rows": table_rows,
            }],
            session_ended=True,
        )

    async def _fee_student_info(self, session, user, db, school_id) -> BotResponse:
        """For student/parent — show own fee info."""
        session.current_flow = None
        session.current_step = None

        outstanding = await _scalar(
            db,
            "SELECT COALESCE(SUM(fi.balance_amount),0) FROM fee_invoices fi "
            "JOIN students s ON fi.student_id = s.id "
            "WHERE fi.school_id = :sid AND s.user_id = :uid "
            "AND fi.status NOT IN ('paid','cancelled')",
            {"sid": school_id, "uid": str(user.id)},
        )

        def fmt(p): return f"₹{p/100:,.0f}" if p else "₹0"

        return BotResponse(
            text=f"💰 **Your Fee Info**\n\nOutstanding: **{fmt(outstanding)}**\n\nType **menu** to continue.",
            type="data",
            actions=[{"label": "View Fee Details", "path": "/fees"}],
            session_ended=True,
        )

    # ─── LEAVE ───────────────────────────────────────────────────────────────

    async def _flow_leave(
        self, session, message, payload, user, db, school_id
    ) -> BotResponse:
        role = await get_user_role(db, user)
        step = session.current_step or "check_role"

        # Admin: show pending leave requests (read-only)
        if role == "admin" and step == "check_role":
            return await self._leave_admin_view(session, db, school_id)

        # Staff/Teacher: apply leave flow
        if step in ("check_role", "select_type"):
            return await self._leave_select_type(session, db, school_id)

        if step == "enter_from_date":
            session.patch_context({"leave_type_id": session.context.get("pending_type_id", ""),
                                   "leave_type_name": session.context.get("pending_type_name", "")})
            # Actually entering the from_date
            return await self._leave_enter_dates(session, message, db)

        if step == "enter_to_date":
            return await self._leave_enter_to_date(session, message, db)

        if step == "enter_reason":
            return await self._leave_enter_reason(session, message)

        if step == "confirm":
            return await self._leave_confirm(session, message, user, db, school_id)

        return await self._leave_select_type(session, db, school_id)

    async def _leave_select_type(self, session, db, school_id) -> BotResponse:
        types = await _q(
            db,
            "SELECT id, name, max_days_per_year, is_paid FROM leave_types "
            "WHERE school_id = :sid AND is_active = 1 ORDER BY name",
            {"sid": school_id},
        )
        if not types:
            return BotResponse(text="No leave types configured. Contact admin.", type="error")

        session.current_step = "enter_from_date"
        options = [
            BotOption(
                id=str(t["id"]),
                label=t["name"],
                description=f"Max {t['max_days_per_year']} days | {'Paid' if t['is_paid'] else 'Unpaid'}",
            )
            for t in types
        ]
        return BotResponse(
            text="📋 **Apply Leave**\n\nSelect leave type:",
            type="options",
            options=options,
            breadcrumb="Leave",
        )

    async def _leave_enter_dates(self, session, message, db) -> BotResponse:
        ctx = session.context
        # message is leave_type_id (option button clicked)
        if "leave_type_id" not in ctx or not ctx["leave_type_id"]:
            # Look up from message
            leave_types = await _q(
                db,
                "SELECT id, name FROM leave_types WHERE is_active = 1",
                {},
            )
            matched = next((t for t in leave_types if str(t["id"]) == message or
                           t["name"].lower() == message.lower()), None)
            if matched:
                session.patch_context({
                    "leave_type_id": str(matched["id"]),
                    "leave_type_name": matched["name"],
                })
            else:
                session.patch_context({"leave_type_id": message, "leave_type_name": message})

        session.current_step = "enter_to_date"
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        return BotResponse(
            text=f"📅 Enter **from date** (YYYY-MM-DD)\nExample: {tomorrow}",
            type="question",
            breadcrumb=f"Leave › {ctx.get('leave_type_name', '')}",
        )

    async def _leave_enter_to_date(self, session, message, db) -> BotResponse:
        session.patch_context({"from_date": message})
        session.current_step = "enter_reason"
        return BotResponse(
            text="📅 Enter **to date** (YYYY-MM-DD):",
            type="question",
            breadcrumb="Leave › Dates",
        )

    async def _leave_enter_reason(self, session, message) -> BotResponse:
        session.patch_context({"to_date": message})
        session.current_step = "confirm"
        return BotResponse(
            text="✏️ Enter **reason** for leave:",
            type="question",
            breadcrumb="Leave › Reason",
        )

    async def _leave_confirm(self, session, message, user, db, school_id) -> BotResponse:
        ctx = session.context

        # Check if we received the reason just now
        if "reason" not in ctx:
            session.patch_context({"reason": message})
            ctx = session.context
            # Show confirmation
            try:
                from_d = date.fromisoformat(ctx.get("from_date", ""))
                to_d = date.fromisoformat(ctx.get("to_date", ""))
                total_days = (to_d - from_d).days + 1
            except ValueError:
                return BotResponse(
                    text="Invalid dates. Please start over. Type **menu**.",
                    type="error", session_ended=True,
                )
            session.patch_context({"total_days": total_days})
            ctx = session.context
            return BotResponse(
                text=(
                    f"📋 **Confirm Leave Request**\n\n"
                    f"Type: {ctx.get('leave_type_name', '')}\n"
                    f"From: {ctx.get('from_date')}\n"
                    f"To: {ctx.get('to_date')}\n"
                    f"Days: {total_days}\n"
                    f"Reason: {ctx.get('reason')}\n\n"
                    f"Type **yes** to submit or **no** to cancel."
                ),
                type="confirm",
                breadcrumb="Leave › Confirm",
                options=[
                    BotOption(id="yes", label="Yes, Submit"),
                    BotOption(id="no", label="Cancel"),
                ],
            )

        # User confirmed yes/no
        if message.lower() in ("yes", "y", "submit", "confirm"):
            return await self._leave_save(session, user, db, school_id)
        else:
            session.current_flow = None
            session.current_step = None
            session.set_context({})
            return BotResponse(
                text="Leave request cancelled. Type **menu** to continue.",
                type="info",
                session_ended=True,
            )

    async def _leave_save(self, session, user, db, school_id) -> BotResponse:
        ctx = session.context

        # Find staff record for this user
        staff = await _q(
            db,
            "SELECT id FROM staff WHERE user_id = :uid AND school_id = :sid AND is_active = 1",
            {"uid": str(user.id), "sid": school_id},
        )
        if not staff:
            return BotResponse(
                text="Your staff record was not found. Please contact admin.", type="error"
            )

        try:
            from_d = date.fromisoformat(ctx["from_date"])
            to_d = date.fromisoformat(ctx["to_date"])
            total_days = float(ctx.get("total_days", (to_d - from_d).days + 1))
        except (ValueError, KeyError) as e:
            return BotResponse(text=f"Date error: {e}. Type **menu** to restart.", type="error")

        await db.execute(
            text(
                "INSERT INTO staff_leaves "
                "(id, school_id, staff_id, leave_type_id, from_date, to_date, total_days, "
                "reason, status, created_at, updated_at) "
                "VALUES (:id, :sid, :staff_id, :lt_id, :from_d, :to_d, :total, :reason, "
                "'pending', NOW(), NOW())"
            ),
            {
                "id": _new_id(),
                "sid": school_id,
                "staff_id": str(staff[0]["id"]),
                "lt_id": ctx.get("leave_type_id"),
                "from_d": ctx["from_date"],
                "to_d": ctx["to_date"],
                "total": total_days,
                "reason": ctx.get("reason", ""),
            },
        )
        await db.commit()

        session.current_flow = None
        session.current_step = None
        session.set_context({})
        return BotResponse(
            text=(
                f"✅ **Leave Submitted!**\n\n"
                f"Type: {ctx.get('leave_type_name')}\n"
                f"From: {ctx.get('from_date')}  To: {ctx.get('to_date')}\n"
                f"Status: **Pending** (awaiting admin approval)\n\n"
                f"Type **menu** to continue."
            ),
            type="success",
            actions=[{"label": "View Leave Status", "path": "/leaves"}],
            session_ended=True,
        )

    async def _leave_admin_view(self, session, db, school_id) -> BotResponse:
        session.current_flow = None
        rows = await _q(
            db,
            """SELECT (st.first_name + ' ' + st.last_name) AS staff_name,
                 lt.name AS leave_type, sl.from_date, sl.to_date,
                 CAST(sl.days_count AS VARCHAR) + ' days' AS days,
                 sl.status
               FROM staff_leaves sl
               JOIN staff st ON sl.staff_id = st.id
               JOIN leave_types lt ON sl.leave_type_id = lt.id
               WHERE sl.school_id = :sid AND sl.status = 'pending'
               ORDER BY sl.created_at DESC LIMIT 10""",
            {"sid": school_id},
        )
        if not rows:
            return BotResponse(
                text="✅ No pending leave requests.\n\nType **menu** to continue.",
                type="info",
                session_ended=True,
            )
        table_rows = [[r["staff_name"], r["leave_type"],
                       str(r["from_date"]), str(r["to_date"]), r["days"], r["status"]]
                      for r in rows]
        return BotResponse(
            text=f"📋 **Pending Leave Requests** ({len(rows)} found):",
            type="data",
            cards=[{
                "type": "table",
                "title": "Pending Leaves",
                "headers": ["Staff", "Type", "From", "To", "Days", "Status"],
                "rows": table_rows,
            }],
            actions=[{"label": "Manage Leaves", "path": "/leaves"}],
            session_ended=True,
        )

    # ─── MARKS ───────────────────────────────────────────────────────────────

    async def _flow_marks(
        self, session, message, payload, user, db, school_id
    ) -> BotResponse:
        role = await get_user_role(db, user)
        step = session.current_step or "select_exam"

        # Student: auto-load own marks
        if role == "student" and step == "select_exam":
            return await self._marks_select_exam_for_student(session, user, db, school_id)

        if step == "select_exam":
            return await self._marks_list_exams(session, message, db, school_id)

        if step == "show_results":
            return await self._marks_show(session, message, user, db, school_id)

        return await self._marks_list_exams(session, message, db, school_id)

    async def _marks_list_exams(self, session, message, db, school_id) -> BotResponse:
        s_where = "WHERE school_id = :sid" if school_id else ""
        s_p: Dict[str, Any] = {"sid": school_id} if school_id else {}
        exams = await _q(
            db,
            f"SELECT id, name, exam_date FROM exams {s_where} ORDER BY exam_date DESC LIMIT 10",
            s_p,
        )
        if not exams:
            return BotResponse(text="No exams found.", type="info", session_ended=True)

        session.current_step = "show_results"
        return BotResponse(
            text="📝 **Exam Results**\n\nSelect an exam:",
            type="options",
            options=[BotOption(id=str(e["id"]), label=e["name"]) for e in exams],
            breadcrumb="Marks",
        )

    async def _marks_select_exam_for_student(self, session, user, db, school_id) -> BotResponse:
        s_where = "WHERE e.school_id = :sid" if school_id else ""
        s_p: Dict[str, Any] = {"sid": school_id} if school_id else {}
        exams = await _q(
            db,
            f"SELECT e.id, e.name, e.exam_date FROM exams e {s_where} ORDER BY e.exam_date DESC LIMIT 10",
            s_p,
        )
        session.current_step = "show_results"
        return BotResponse(
            text="📝 **My Exam Results**\n\nSelect an exam:",
            type="options",
            options=[BotOption(id=str(e["id"]), label=e["name"]) for e in exams],
            breadcrumb="Marks",
        )

    async def _marks_show(self, session, message, user, db, school_id) -> BotResponse:
        role = await get_user_role(db, user)
        exam_id = message  # option id

        # Get exam name
        exam_sid_clause = "AND school_id = :sid" if school_id else ""
        marks_sid_clause = "AND sm.school_id = :sid" if school_id else ""
        sid_p_eid: Dict[str, Any] = {"eid": exam_id, "sid": school_id} if school_id else {"eid": exam_id}
        exam_info = await _q(
            db, f"SELECT name FROM exams WHERE id = :eid {exam_sid_clause}",
            sid_p_eid
        )
        exam_name = exam_info[0]["name"] if exam_info else exam_id

        if role == "student":
            student_p: Dict[str, Any] = {**sid_p_eid, "uid": str(user.id)}
            rows = await _q(
                db,
                f"""SELECT sub.name AS subject, sm.marks_obtained,
                     e.full_marks AS max_marks,
                     sm.grade,
                     CASE WHEN sm.marks_obtained >= e.pass_marks THEN 1 ELSE 0 END AS is_pass
                   FROM student_marks sm
                   JOIN exams e ON sm.exam_id = e.id
                   JOIN subjects sub ON e.subject_id = sub.id
                   JOIN students s ON sm.student_id = s.id
                   WHERE sm.exam_id = :eid {marks_sid_clause} AND s.user_id = :uid
                   ORDER BY sub.name""",
                student_p,
            )
            if not rows:
                session.current_flow = None
                return BotResponse(text=f"No marks found for {exam_name}.", type="info", session_ended=True)

            table_rows = [
                [r["subject"],
                 f"{r['marks_obtained']}/{r['max_marks']}",
                 str(r.get("grade") or ""),
                 "P" if r.get("is_pass") else "F"]
                for r in rows
            ]
            session.current_flow = None
            session.current_step = None
            return BotResponse(
                text=f"Your Results — {exam_name}:",
                type="data",
                cards=[{
                    "type": "table",
                    "title": exam_name,
                    "headers": ["Subject", "Marks", "Grade", "Pass"],
                    "rows": table_rows,
                }],
                session_ended=True,
            )
        else:
            # Admin/Teacher: student-wise results for selected exam
            rows = await _q(
                db,
                f"""SELECT s.first_name + ' ' + s.last_name AS student,
                     s.admission_number,
                     COALESCE(c.name, '') AS class_name,
                     sm.marks_obtained,
                     e.full_marks AS max_marks,
                     sm.grade,
                     CASE WHEN sm.marks_obtained >= e.pass_marks THEN 1 ELSE 0 END AS is_pass
                   FROM student_marks sm
                   JOIN students s ON sm.student_id = s.id
                   JOIN exams e ON sm.exam_id = e.id
                   LEFT JOIN student_enrollments se ON se.student_id = s.id AND se.is_current = 1
                   LEFT JOIN classes c ON se.class_id = c.id
                   WHERE sm.exam_id = :eid {marks_sid_clause}
                   ORDER BY sm.marks_obtained DESC LIMIT 20""",
                sid_p_eid,
            )
            table_rows = [
                [r["student"], r["class_name"],
                 f"{r['marks_obtained']}/{r['max_marks']}",
                 str(r.get("grade") or ""),
                 "P" if r.get("is_pass") else "F"]
                for r in rows
            ]
            session.current_flow = None
            session.current_step = None
            return BotResponse(
                text=f"Exam Results — {exam_name} ({len(rows)} students):",
                type="data",
                cards=[{
                    "type": "table",
                    "title": exam_name,
                    "headers": ["Student", "Class", "Marks", "Grade", "Pass"],
                    "rows": table_rows,
                }],
                actions=[{"label": "Full Results", "path": "/exams"}],
                session_ended=True,
            )

    # ─── STUDENT DETAILS ─────────────────────────────────────────────────────

    async def _flow_student_details(
        self, session, message, payload, user, db, school_id
    ) -> BotResponse:
        role = await get_user_role(db, user)
        step = session.current_step or "search"

        if step == "search":
            session.current_step = "show"
            return BotResponse(
                text="🔍 Enter student **name** or **admission number**:",
                type="question",
                breadcrumb="Student Info",
            )

        return await self._student_show(session, message, db, school_id)

    async def _student_show(self, session, message, db, school_id) -> BotResponse:
        session.current_flow = None

        s_where = "AND s.school_id = :sid" if school_id else ""
        s_p: Dict[str, Any] = {"sid": school_id, "q": f"%{message}%"} if school_id else {"q": f"%{message}%"}

        rows = await _q(
            db,
            f"""SELECT s.first_name + ' ' + s.last_name AS name,
                 s.admission_number,
                 s.date_of_birth, s.gender, COALESCE(u.phone, '') AS phone,
                 c.name AS class_name, sec.name AS section_name,
                 COALESCE(u.email, '') AS email
               FROM students s
               LEFT JOIN student_enrollments se ON se.student_id = s.id AND se.is_current = 1
               LEFT JOIN classes c ON se.class_id = c.id
               LEFT JOIN sections sec ON se.section_id = sec.id
               LEFT JOIN users u ON s.user_id = u.id
               WHERE s.is_active = 1 {s_where}
                 AND (
                   LOWER(s.first_name + ' ' + s.last_name) LIKE LOWER(:q LIMIT 5)
                   OR LOWER(s.admission_number) LIKE LOWER(:q)
                 )""",
            s_p,
        )

        if not rows:
            return BotResponse(
                text=f"No students found matching **{message}**.\n\nType **menu** to go back.",
                type="info",
                session_ended=True,
            )

        table_rows = [
            [r["name"], r["admission_number"], r["class_name"],
             str(r["section_name"] or ""), str(r["gender"] or "")]
            for r in rows
        ]
        return BotResponse(
            text=f"Found {len(rows)} student(s) matching '{message}':",
            type="data",
            cards=[{
                "type": "table",
                "title": "Student Details",
                "headers": ["Name", "Admission No", "Class", "Section", "Gender"],
                "rows": table_rows,
            }],
            actions=[{"label": "Student Management", "path": "/students"}],
            suggestions=["Edit Student", "Menu"],
            session_ended=True,
        )

    # ─── ATTENDANCE TODAY ─────────────────────────────────────────────────────

    async def _flow_attendance_today(
        self, session, message, payload, user, db, school_id
    ) -> BotResponse:
        session.current_flow = None
        session.current_step = None

        # Build school filter (super admin has no school_id — show all schools)
        sid_clause = "AND asess.school_id = :sid" if school_id else ""
        sid_params: Dict[str, Any] = {"sid": school_id} if school_id else {}

        # School-wide summary
        totals = await _q(
            db,
            f"""SELECT
                 COUNT(DISTINCT sa.student_id) AS total,
                 SUM(CASE WHEN sa.status='present' THEN 1 ELSE 0 END) AS present_count,
                 SUM(CASE WHEN sa.status='absent'  THEN 1 ELSE 0 END) AS absent_count,
                 SUM(CASE WHEN sa.status='late'    THEN 1 ELSE 0 END) AS late_count
               FROM attendance_sessions asess
               JOIN student_attendance sa ON sa.session_id = asess.id
               WHERE 1 = 1 {sid_clause}
                 AND CAST(asess.date AS DATE) = CAST(NOW() AS DATE)""",
            sid_params,
        )
        total   = int(totals[0]["total"]         or 0) if totals else 0
        present = int(totals[0]["present_count"] or 0) if totals else 0
        absent  = int(totals[0]["absent_count"]  or 0) if totals else 0
        late    = int(totals[0]["late_count"]    or 0) if totals else 0
        pct     = f"{present/total*100:.0f}%" if total else "N/A"

        # Class-wise breakdown
        rows = await _q(
            db,
            f"""SELECT c.name AS class_name, sec.name AS section_name,
                 COUNT(DISTINCT sa.student_id) AS total,
                 SUM(CASE WHEN sa.status='present' THEN 1 ELSE 0 END) AS present_count,
                 SUM(CASE WHEN sa.status='absent'  THEN 1 ELSE 0 END) AS absent_count
               FROM attendance_sessions asess
               JOIN classes c ON asess.class_id = c.id
               JOIN sections sec ON asess.section_id = sec.id
               JOIN student_attendance sa ON sa.session_id = asess.id
               WHERE 1 = 1 {sid_clause}
                 AND CAST(asess.date AS DATE) = CAST(NOW() AS DATE)
               GROUP BY c.name, sec.name
               ORDER BY c.name, sec.name""",
            sid_params,
        )

        if not rows and total == 0:
            return BotResponse(
                text="📋 **Today's Attendance**\n\nNo attendance has been marked yet today.\n\nUse **Mark Attendance** to start.",
                type="data",
                suggestions=["Mark Attendance", "Menu"],
                session_ended=True,
            )

        table_rows = [
            [f"{r['class_name']} {r['section_name']}",
             str(int(r["total"] or 0)),
             str(int(r["present_count"] or 0)),
             str(int(r["absent_count"] or 0)),
             f"{int(r['present_count'] or 0)/int(r['total'] or 1)*100:.0f}%"]
            for r in rows
        ]

        return BotResponse(
            text=f"📋 **Today's Attendance**\n\nTotal: **{total}** | Present: **{present}** | Absent: **{absent}** | Late: **{late}**\nAttendance Rate: **{pct}**",
            type="data",
            cards=[
                {
                    "type": "stats",
                    "stats": [
                        {"label": "Total", "value": str(total), "color": "blue"},
                        {"label": "Present", "value": str(present), "color": "green"},
                        {"label": "Absent", "value": str(absent), "color": "red"},
                        {"label": "Rate", "value": pct, "color": "orange"},
                    ],
                },
                {
                    "type": "table",
                    "title": "Class-wise Breakdown",
                    "headers": ["Class", "Total", "Present", "Absent", "%"],
                    "rows": table_rows,
                },
            ],
            actions=[{"label": "Attendance", "path": "/attendance"}],
            session_ended=True,
        )

    # ─── ACCOUNTING — TODAY'S INCOME & EXPENSES ───────────────────────────────

    async def _flow_accounting(
        self, session, message, payload, user, db, school_id
    ) -> BotResponse:
        session.current_flow = None
        session.current_step = None

        def fmt(p): return f"Rs.{int(p):,}" if p else "Rs.0"

        # Build school filter (super admin = cross-school)
        s_where = "AND school_id = :sid" if school_id else ""
        s_p: Dict[str, Any] = {"sid": school_id} if school_id else {}

        today_income = await _scalar(
            db,
            f"SELECT COALESCE(SUM(amount),0) FROM income_records "
            f"WHERE 1=1 {s_where} AND CAST(income_date AS DATE) = CAST(NOW() AS DATE)",
            s_p,
        )
        month_income = await _scalar(
            db,
            f"SELECT COALESCE(SUM(amount),0) FROM income_records "
            f"WHERE 1=1 {s_where} "
            "AND EXTRACT(YEAR FROM income_date) = EXTRACT(YEAR FROM NOW()) AND EXTRACT(MONTH FROM income_date) = EXTRACT(MONTH FROM NOW())",
            s_p,
        )
        today_expense = await _scalar(
            db,
            f"SELECT COALESCE(SUM(amount),0) FROM expense_records "
            f"WHERE 1=1 {s_where} AND CAST(expense_date AS DATE) = CAST(NOW() AS DATE)",
            s_p,
        )
        month_expense = await _scalar(
            db,
            f"SELECT COALESCE(SUM(amount),0) FROM expense_records "
            f"WHERE 1=1 {s_where} "
            "AND EXTRACT(YEAR FROM expense_date) = EXTRACT(YEAR FROM NOW()) AND EXTRACT(MONTH FROM expense_date) = EXTRACT(MONTH FROM NOW())",
            s_p,
        )
        today_fee = await _scalar(
            db,
            f"SELECT COALESCE(SUM(amount),0) FROM fee_payments "
            f"WHERE 1=1 {s_where} AND CAST(payment_date AS DATE) = CAST(NOW() AS DATE)",
            s_p,
        )
        month_fee = await _scalar(
            db,
            f"SELECT COALESCE(SUM(amount),0) FROM fee_payments "
            f"WHERE 1=1 {s_where} "
            "AND EXTRACT(YEAR FROM payment_date) = EXTRACT(YEAR FROM NOW()) AND EXTRACT(MONTH FROM payment_date) = EXTRACT(MONTH FROM NOW())",
            s_p,
        )

        net_today = today_income - today_expense
        net_month = month_income - month_expense

        # Category breakdown for today
        income_cats = await _q(
            db,
            f"""SELECT ic.name, COALESCE(SUM(ir.amount),0) AS total
               FROM income_records ir
               JOIN income_categories ic ON ic.id = ir.category_id
               WHERE CAST(ir.income_date AS DATE) = CAST(NOW() AS DATE) {s_where.replace('school_id', 'ir.school_id')}
               GROUP BY ic.name ORDER BY total DESC""",
            s_p,
        )
        expense_cats = await _q(
            db,
            f"""SELECT ec.name, COALESCE(SUM(er.amount),0) AS total
               FROM expense_records er
               JOIN expense_categories ec ON ec.id = er.category_id
               WHERE CAST(er.expense_date AS DATE) = CAST(NOW() AS DATE) {s_where.replace('school_id', 'er.school_id')}
               GROUP BY ec.name ORDER BY total DESC""",
            s_p,
        )

        cards = [
            {
                "type": "stats",
                "stats": [
                    {"label": "Today Income",  "value": fmt(today_income),  "color": "green"},
                    {"label": "Today Expense", "value": fmt(today_expense), "color": "red"},
                    {"label": "Fee Collected", "value": fmt(today_fee),     "color": "blue"},
                    {"label": "Net Today",     "value": fmt(net_today),     "color": "green" if net_today >= 0 else "red"},
                ],
            },
            {
                "type": "stats",
                "stats": [
                    {"label": "Month Income",  "value": fmt(month_income),  "color": "green"},
                    {"label": "Month Expense", "value": fmt(month_expense), "color": "red"},
                    {"label": "Month Fee",     "value": fmt(month_fee),     "color": "blue"},
                    {"label": "Net Month",     "value": fmt(net_month),     "color": "green" if net_month >= 0 else "red"},
                ],
            },
        ]
        if income_cats:
            cards.append({
                "type": "table",
                "title": "Today's Income by Category",
                "headers": ["Category", "Amount"],
                "rows": [[r["name"], fmt(r["total"])] for r in income_cats],
            })
        if expense_cats:
            cards.append({
                "type": "table",
                "title": "Today's Expenses by Category",
                "headers": ["Category", "Amount"],
                "rows": [[r["name"], fmt(r["total"])] for r in expense_cats],
            })

        return BotResponse(
            text=f"📊 **Today's Financials**\n\nIncome: **{fmt(today_income)}** | Expenses: **{fmt(today_expense)}** | Fee: **{fmt(today_fee)}**\nNet: **{fmt(net_today)}**",
            type="data",
            cards=cards,
            actions=[{"label": "Accounting", "path": "/accounting"}],
            session_ended=True,
        )

    # ─── FEE COLLECT ─────────────────────────────────────────────────────────

    async def _fee_collect_find_student(self, session, message, db, school_id) -> BotResponse:
        rows = await _q(
            db,
            """SELECT s.id, s.first_name + ' ' + s.last_name AS name,
                 s.admission_number, c.name AS class_name,
                 COALESCE((SELECT SUM(fi.balance_amount) FROM fee_invoices fi
                           WHERE fi.student_id = s.id AND fi.status NOT IN ('paid','cancelled')),0) AS outstanding
               FROM students s
               LEFT JOIN student_enrollments se ON se.student_id = s.id AND se.is_current = 1
               LEFT JOIN classes c ON se.class_id = c.id
               WHERE s.school_id = :sid AND s.is_active = 1
                 AND (LOWER(s.first_name + ' ' + s.last_name) LIKE LOWER(:q LIMIT 5)
                      OR LOWER(s.admission_number) LIKE LOWER(:q))""",
            {"sid": school_id, "q": f"%{message}%"},
        )

        def fmt(p): return f"₹{p/100:,.0f}" if p else "₹0"

        if not rows:
            return BotResponse(
                text=f"No students found for **{message}**. Try again with a different name or admission number:",
                type="question",
                breadcrumb="Fee › Collect",
            )

        if len(rows) == 1:
            r = rows[0]
            session.patch_context({"collect_student_id": str(r["id"]), "collect_student_name": r["name"]})
            return await self._fee_collect_show_invoices(session, r["id"], r["name"], db, school_id)

        # Multiple matches — let user pick
        session.current_step = "fee_collect_search"
        options = [
            BotOption(id=str(r["id"]), label=r["name"],
                      description=f"{r['admission_number']} | {r['class_name']} | Due: {fmt(r['outstanding'])}")
            for r in rows
        ]
        session.current_step = "fee_collect_invoice"
        session.patch_context({"collect_students": {str(r["id"]): r["name"] for r in rows}})
        return BotResponse(
            text="Multiple students found. Select one:",
            type="options",
            options=options,
            breadcrumb="Fee › Collect",
        )

    async def _fee_collect_pick_invoice(self, session, message, db, school_id) -> BotResponse:
        ctx = session.context
        # Phase A: student was just picked (message = student_id from option button)
        if "collect_student_id" not in ctx:
            student_id = message
            students_map = ctx.get("collect_students", {})
            student_name = students_map.get(student_id, "Student")
            session.patch_context({"collect_student_id": student_id, "collect_student_name": student_name})
            return await self._fee_collect_show_invoices(session, student_id, student_name, db, school_id)

        # Phase B: invoice was just picked (message = invoice_id from option button)
        invoice_id = message
        invoices_map = ctx.get("collect_invoices", {})
        if invoice_id not in invoices_map:
            return BotResponse(text="Invalid selection. Type **menu** to restart.", type="error", session_ended=True)

        invoice = invoices_map[invoice_id]
        session.patch_context({"collect_invoice_id": invoice_id, "collect_invoice": invoice})
        session.current_step = "fee_collect_method"
        return BotResponse(
            text=(f"Invoice **{invoice['number']}** — Balance: **₹{invoice['balance']/100:,.0f}**\n\n"
                  "Select payment method:"),
            type="options",
            options=[BotOption(**o) for o in PAYMENT_METHOD_OPTIONS],
            breadcrumb="Fee › Collect › Method",
        )

    async def _fee_collect_show_invoices(self, session, student_id, student_name, db, school_id) -> BotResponse:
        invoices = await _q(
            db,
            """SELECT id, invoice_number, due_date, balance_amount, status
               FROM fee_invoices
               WHERE student_id = :sid AND school_id = :school
                 AND status NOT IN ('paid','cancelled') AND balance_amount > 0
               ORDER BY due_date""",
            {"sid": str(student_id), "school": school_id},
        )
        if not invoices:
            return BotResponse(
                text=f"✅ **{student_name}** has no pending fee invoices.",
                type="data",
                session_ended=True,
            )

        session.current_step = "fee_collect_invoice"
        inv_map = {
            str(r["id"]): {"number": r["invoice_number"], "balance": r["balance_amount"], "due": str(r["due_date"])}
            for r in invoices
        }
        session.patch_context({"collect_invoices": inv_map})
        options = [
            BotOption(
                id=str(r["id"]),
                label=f"Invoice {r['invoice_number']}",
                description=f"Due: {r['due_date']} | Balance: ₹{r['balance_amount']/100:,.0f}",
            )
            for r in invoices
        ]
        return BotResponse(
            text=f"📄 **{student_name}** — Select invoice to pay:",
            type="options",
            options=options,
            breadcrumb="Fee › Collect",
        )

    async def _fee_collect_pick_method(self, session, message) -> BotResponse:
        valid = {"cash", "upi", "online", "neft", "card", "cheque"}
        method = message.lower()
        if method not in valid:
            return BotResponse(
                text="Select a payment method:",
                type="options",
                options=[BotOption(**o) for o in PAYMENT_METHOD_OPTIONS],
                breadcrumb="Fee › Collect › Method",
            )
        # Map "online" -> "online", "neft" -> "neft" — both valid DB enums
        session.patch_context({"collect_method": method})
        ctx = session.context
        inv = ctx.get("collect_invoice", {})
        student_name = ctx.get("collect_student_name", "Student")
        session.current_step = "fee_collect_confirm"
        return BotResponse(
            text=(
                f"📋 **Confirm Payment**\n\n"
                f"Student: **{student_name}**\n"
                f"Invoice: **{inv.get('number', '')}**\n"
                f"Amount: **₹{inv.get('balance', 0)/100:,.0f}**\n"
                f"Method: **{method.upper()}**\n\n"
                "Confirm payment?"
            ),
            type="confirm",
            options=[BotOption(id="yes", label="✅ Confirm"), BotOption(id="no", label="❌ Cancel")],
            breadcrumb="Fee › Collect › Confirm",
        )

    async def _fee_collect_confirm(self, session, message, user, db, school_id) -> BotResponse:
        session.current_flow = None
        session.current_step = None
        if message.lower() in ("no", "cancel"):
            return BotResponse(text="Payment cancelled. Type **menu** to start over.", type="info", session_ended=True)

        ctx = session.context
        invoice_id  = ctx.get("collect_invoice_id")
        inv         = ctx.get("collect_invoice", {})
        method      = ctx.get("collect_method", "cash")
        student_name = ctx.get("collect_student_name", "Student")
        amount      = inv.get("balance", 0)

        if not invoice_id or not amount:
            return BotResponse(text="⚠️ Session expired. Type **menu** to restart.", type="error", session_ended=True)

        receipt_number = f"RCP-{date.today().strftime('%Y%m%d')}-{_new_id()[:8].upper()}"
        await db.execute(
            text("""INSERT INTO fee_payments
                    (id, school_id, invoice_id, amount, payment_date, payment_method,
                     receipt_number, collected_by, created_at)
                    VALUES
                    (UUID(), :school_id, :invoice_id, :amount, CAST(NOW() AS DATE),
                     :method, :receipt, :collected_by, NOW())"""),
            {
                "school_id":    school_id,
                "invoice_id":   invoice_id,
                "amount":       amount,
                "method":       method,
                "receipt":      receipt_number,
                "collected_by": str(user.id),
            },
        )
        # Update invoice paid_amount
        await db.execute(
            text("UPDATE fee_invoices SET paid_amount = paid_amount + :amt, "
                 "status = CASE WHEN paid_amount + :amt >= total_amount THEN 'paid' ELSE 'partial' END, "
                 "updated_at = NOW() WHERE id = :iid"),
            {"amt": amount, "iid": invoice_id},
        )

        def fmt(p): return f"₹{p/100:,.0f}" if p else "₹0"

        return BotResponse(
            text=(f"✅ **Payment Recorded!**\n\n"
                  f"Student: **{student_name}**\n"
                  f"Amount: **{fmt(amount)}** via {method.upper()}\n"
                  f"Receipt: **{receipt_number}**"),
            type="success",
            actions=[{"label": "Fee Management", "path": "/fees"}],
            session_ended=True,
        )

    # ─── FEE BALANCE REPORT ──────────────────────────────────────────────────

    async def _fee_balance_report(self, session, message, db, school_id) -> BotResponse:
        """Day / Month / Year fee collection & balance report."""
        session.current_flow = None
        session.current_step = None

        period = message.lower()
        if period in ("fee_balance_today", "today"):
            where_pay  = "CAST(payment_date AS DATE) = CAST(NOW() AS DATE)"
            where_inv  = "CAST(due_date AS DATE) = CAST(NOW() AS DATE)"
            period_label = "Today"
        elif period in ("fee_balance_year", "year", "this year"):
            where_pay  = "EXTRACT(YEAR FROM payment_date) = EXTRACT(YEAR FROM NOW())"
            where_inv  = "EXTRACT(YEAR FROM due_date) = EXTRACT(YEAR FROM NOW())"
            period_label = "This Year"
        else:  # default: this month
            where_pay  = "EXTRACT(YEAR FROM payment_date) = EXTRACT(YEAR FROM NOW()) AND EXTRACT(MONTH FROM payment_date) = EXTRACT(MONTH FROM NOW())"
            where_inv  = "EXTRACT(YEAR FROM due_date) = EXTRACT(YEAR FROM NOW()) AND EXTRACT(MONTH FROM due_date) = EXTRACT(MONTH FROM NOW())"
            period_label = "This Month"

        def fmt(p): return f"₹{p/100:,.0f}" if p else "₹0"

        collected = await _scalar(
            db,
            f"SELECT COALESCE(SUM(amount),0) FROM fee_payments WHERE school_id = :sid AND {where_pay}",
            {"sid": school_id},
        )
        total_invoiced = await _scalar(
            db,
            f"SELECT COALESCE(SUM(total_amount),0) FROM fee_invoices WHERE school_id = :sid AND {where_inv}",
            {"sid": school_id},
        )
        pending = await _scalar(
            db,
            "SELECT COALESCE(SUM(balance_amount),0) FROM fee_invoices "
            "WHERE school_id = :sid AND status NOT IN ('paid','cancelled')",
            {"sid": school_id},
        )
        paid_count = await _scalar(
            db,
            f"SELECT COUNT(*) FROM fee_invoices WHERE school_id = :sid AND status = 'paid' AND {where_inv}",
            {"sid": school_id},
        )
        unpaid_count = await _scalar(
            db,
            f"SELECT COUNT(*) FROM fee_invoices WHERE school_id = :sid AND status NOT IN ('paid','cancelled') AND {where_inv}",
            {"sid": school_id},
        )

        return BotResponse(
            text=(
                f"💰 **Fee Balance Report — {period_label}**\n\n"
                f"Total Invoiced : **{fmt(total_invoiced)}**\n"
                f"Collected      : **{fmt(collected)}**\n"
                f"Balance/Pending: **{fmt(pending)}**\n"
                f"Paid Invoices  : **{paid_count}**\n"
                f"Unpaid Invoices: **{unpaid_count}**\n\n"
                f"Type **menu** to continue."
            ),
            type="data",
            cards=[{
                "type": "stats",
                "stats": [
                    {"label": "Invoiced",       "value": fmt(total_invoiced), "color": "blue"},
                    {"label": "Collected",      "value": fmt(collected),      "color": "green"},
                    {"label": "Balance",        "value": fmt(pending),        "color": "red"},
                    {"label": "Paid/Unpaid",    "value": f"{paid_count}/{unpaid_count}", "color": "orange"},
                ],
            }],
            actions=[{"label": "Fee Management", "path": "/fees"}],
            session_ended=True,
        )

    # ─── STUDENT EDIT ─────────────────────────────────────────────────────────

    async def _flow_student_edit(
        self, session, message, payload, user, db, school_id
    ) -> BotResponse:
        # Permission gate — only admin/super_admin may edit students
        perms = await get_user_permissions(db, user)
        if not _has_perm(perms, "students", "update"):
            session.current_flow = None
            return BotResponse(
                text="⛔ You don't have permission to edit student records.",
                type="error",
                session_ended=True,
            )
        step = session.current_step or "search"

        if step == "search":
            session.current_step = "select_student"
            return BotResponse(
                text="✏️ **Edit Student**\n\nEnter student name or admission number:",
                type="question",
                breadcrumb="Student Edit",
            )
        if step == "select_student":
            return await self._se_find_student(session, message, db, school_id)
        if step == "select_field":
            return await self._se_select_field(session, message, db, school_id)
        if step == "enter_value":
            return await self._se_enter_value(session, message)
        if step == "confirm":
            return await self._se_confirm(session, message, db, school_id)

        return await self._start_greeting(session, user, db)

    async def _se_find_student(self, session, message, db, school_id) -> BotResponse:
        rows = await _q(
            db,
            """SELECT s.id, s.first_name + ' ' + s.last_name AS name,
                 s.admission_number, c.name AS class_name,
                 COALESCE(u.phone, '') AS phone,
                 COALESCE(s.blood_group, '') AS blood_group,
                 COALESCE(s.category, '') AS category, s.is_active
               FROM students s
               LEFT JOIN student_enrollments se ON se.student_id = s.id AND se.is_current = 1
               LEFT JOIN classes c ON se.class_id = c.id
               LEFT JOIN users u ON s.user_id = u.id
               WHERE s.school_id = :sid AND s.is_active = 1
                 AND (
                   LOWER(s.first_name + ' ' + s.last_name) LIKE LOWER(:q LIMIT 5)
                   OR LOWER(s.admission_number) LIKE LOWER(:q)
                 )""",
            {"sid": school_id, "q": f"%{message}%"},
        )
        if not rows:
            return BotResponse(
                text=f"No students found matching **{message}**. Try again:",
                type="question",
                breadcrumb="Student Edit",
            )
        if len(rows) == 1:
            s = rows[0]
            session.patch_context({
                "edit_student_id": str(s["id"]),
                "edit_student_name": s["name"],
            })
            session.current_step = "select_field"
            return self._se_field_menu(s["name"])

        # Multiple: let user pick
        session.current_step = "select_field"
        session.patch_context({"search_results": [
            {"id": str(r["id"]), "name": r["name"],
             "admission_number": r["admission_number"],
             "class_name": r["class_name"] or ""}
            for r in rows
        ]})
        return BotResponse(
            text=f"Found {len(rows)} students. Select one:",
            type="options",
            options=[BotOption(id=str(r["id"]), label=r["name"],
                               description=f'{r["admission_number"]} | {r["class_name"] or ""}')
                     for r in rows],
            breadcrumb="Student Edit › Select",
        )

    def _se_field_menu(self, student_name: str) -> BotResponse:
        return BotResponse(
            text=f"✏️ Editing **{student_name}**\n\nWhich field would you like to update?",
            type="options",
            options=[
                BotOption(id="phone",       label="Phone Number",  description="Contact number"),
                BotOption(id="blood_group", label="Blood Group",   description="e.g. A+, O-, AB+"),
                BotOption(id="category",    label="Category",      description="General / OBC / SC / ST / EWS"),
                BotOption(id="status",      label="Active Status", description="Activate or deactivate student"),
            ],
            breadcrumb="Student Edit › Fields",
        )

    async def _se_select_field(self, session, message, db, school_id) -> BotResponse:
        ctx = session.context
        valid_fields = {"phone", "blood_group", "category", "status"}

        # If message is a student_id from the multiple-match list
        if "edit_student_id" not in ctx or message not in valid_fields:
            search_results = ctx.get("search_results", [])
            matched = next((r for r in search_results if r["id"] == message), None)
            if matched:
                session.patch_context({
                    "edit_student_id": matched["id"],
                    "edit_student_name": matched["name"],
                })
                return self._se_field_menu(matched["name"])

        if message.lower() not in valid_fields:
            return self._se_field_menu(ctx.get("edit_student_name", "Student"))

        field = message.lower()
        session.patch_context({"edit_field": field})
        session.current_step = "enter_value"
        prompts = {
            "phone":       "Enter the new **phone number**:",
            "blood_group": "Enter the **blood group** (e.g. A+, B-, O+, AB+):",
            "category":    "Enter **category** (General / OBC / SC / ST / EWS):",
            "status":      "Type **active** to enable or **inactive** to disable:",
        }
        return BotResponse(
            text=prompts[field],
            type="question",
            breadcrumb=f"Student Edit › {field.replace('_', ' ').title()}",
        )

    async def _se_enter_value(self, session, message) -> BotResponse:
        ctx = session.context
        field = ctx.get("edit_field", "")
        new_value = message.strip()

        if field == "blood_group":
            valid_bg = {"A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"}
            if new_value.upper() not in valid_bg:
                return BotResponse(
                    text=f"Invalid blood group. Enter one of: {', '.join(sorted(valid_bg))}",
                    type="question",
                )
            new_value = new_value.upper()
        elif field == "status":
            val_lower = new_value.lower()
            if val_lower not in ("active", "inactive"):
                return BotResponse(text="Enter **active** or **inactive**.", type="question")
            new_value = "true" if val_lower == "active" else "false"
        elif field == "category":
            valid_cats = {"general", "obc", "sc", "st", "ews"}
            if new_value.lower() not in valid_cats:
                return BotResponse(
                    text="Enter one of: General, OBC, SC, ST, EWS", type="question"
                )
            new_value = new_value.upper()

        session.patch_context({"edit_new_value": new_value})
        session.current_step = "confirm"
        field_label = field.replace("_", " ").title()
        student_name = ctx.get("edit_student_name", "Student")
        display_val = "Active" if new_value == "true" else ("Inactive" if new_value == "false" else new_value)
        return BotResponse(
            text=(
                f"Confirm update for **{student_name}**:\n\n"
                f"Field: **{field_label}**\nNew Value: **{display_val}**\n\n"
                f"Type **yes** to confirm or **no** to cancel."
            ),
            type="confirm",
            options=[BotOption(id="yes", label="✅ Confirm"), BotOption(id="no", label="❌ Cancel")],
            breadcrumb="Student Edit › Confirm",
        )

    async def _se_confirm(self, session, message, db, school_id) -> BotResponse:
        if message.lower() in ("no", "cancel", "n"):
            session.current_flow = None
            session.current_step = None
            session.set_context({})
            return BotResponse(
                text="❌ Update cancelled. Type **menu** to continue.",
                type="info",
                session_ended=True,
            )
        if message.lower() not in ("yes", "confirm", "y"):
            return BotResponse(
                text="Type **yes** to confirm or **no** to cancel.",
                type="confirm",
                options=[BotOption(id="yes", label="✅ Confirm"), BotOption(id="no", label="❌ Cancel")],
            )

        ctx = session.context
        student_id = ctx.get("edit_student_id", "")
        field      = ctx.get("edit_field", "")
        new_value  = ctx.get("edit_new_value", "")

        db_field_map = {
            "phone":       "phone",
            "blood_group": "blood_group",
            "category":    "category",
            "status":      "is_active",
        }
        db_field = db_field_map.get(field)
        if not student_id or not db_field:
            return BotResponse(text="Session expired. Type **menu** to start again.", type="error", session_ended=True)

        sql_val = (1 if new_value == "true" else 0) if field == "status" else new_value

        await db.execute(
            text(f"UPDATE students SET {db_field} = :val, updated_at = NOW() "
                 "WHERE id = :sid AND school_id = :school"),
            {"val": sql_val, "sid": student_id, "school": school_id},
        )
        await db.commit()

        student_name = ctx.get("edit_student_name", "Student")
        field_label  = field.replace("_", " ").title()
        display_val  = "Active" if new_value == "true" else ("Inactive" if new_value == "false" else new_value)
        session.current_flow = None
        session.current_step = None
        session.set_context({})
        return BotResponse(
            text=(
                f"✅ **Updated Successfully!**\n\n"
                f"Student: **{student_name}**\n"
                f"{field_label}: **{display_val}**\n\n"
                f"Type **menu** to continue."
            ),
            type="success",
            actions=[{"label": "Student Management", "path": "/students"}],
            session_ended=True,
        )

    # ─── ATTENDANCE VIEW ──────────────────────────────────────────────────────

    async def _flow_attendance_view(
        self, session, message, payload, user, db, school_id
    ) -> BotResponse:
        step = session.current_step or "select_class"

        if step == "select_class":
            return await self._av_select_class(session, db, school_id)
        if step == "select_section":
            return await self._av_select_section(session, message, db, school_id)
        if step == "select_date":
            return await self._av_select_date(session, message, db, school_id)
        if step == "show":
            return await self._av_show(session, message, db, school_id)
        return await self._av_select_class(session, db, school_id)

    async def _av_select_class(self, session, db, school_id) -> BotResponse:
        classes = await _q(
            db,
            "SELECT id, name FROM classes WHERE school_id = :sid AND is_active = 1 ORDER BY name",
            {"sid": school_id},
        )
        if not classes:
            return BotResponse(text="No classes found.", type="error")
        session.current_step = "select_section"
        session.set_context({})
        return BotResponse(
            text="📋 **View Attendance**\n\nSelect a class:",
            type="options",
            options=[BotOption(id=str(c["id"]), label=c["name"]) for c in classes],
            breadcrumb="View Attendance",
        )

    async def _av_select_section(self, session, message, db, school_id) -> BotResponse:
        ctx = session.context
        if "class_id" not in ctx:
            classes = await _q(db,
                "SELECT id, name FROM classes WHERE school_id = :sid AND is_active = 1",
                {"sid": school_id})
            matched = next(
                (c for c in classes if str(c["id"]) == message or c["name"].lower() == message.lower()),
                None)
            if not matched:
                matched = next((c for c in classes if message.lower() in c["name"].lower()), None)
            if not matched:
                return BotResponse(text="Class not found. Select:", type="options",
                                   options=[BotOption(id=str(c["id"]), label=c["name"]) for c in classes])
            session.patch_context({"class_id": str(matched["id"]), "class_name": matched["name"]})
            ctx = session.context

        sections = await _q(db,
            "SELECT id, name FROM sections WHERE class_id = :cid AND is_active = 1 ORDER BY name",
            {"cid": ctx["class_id"]})
        if not sections:
            return BotResponse(text=f"No sections for {ctx['class_name']}.", type="error")
        if len(sections) == 1:
            s = sections[0]
            session.patch_context({"section_id": str(s["id"]), "section_name": s["name"]})
            session.current_step = "show"
            return BotResponse(
                text=f"Enter date for **{ctx['class_name']} - {s['name']}**\n(YYYY-MM-DD or 'today'):",
                type="question",
                options=[BotOption(id="today", label="Today"), BotOption(id="yesterday", label="Yesterday")],
                breadcrumb=f"View Attendance › {ctx['class_name']}",
            )
        session.current_step = "select_date"
        return BotResponse(
            text=f"Select section for **{ctx['class_name']}**:",
            type="options",
            options=[BotOption(id=str(s["id"]), label=s["name"]) for s in sections],
            breadcrumb=f"View Attendance › {ctx['class_name']}",
        )

    async def _av_select_date(self, session, message, db, school_id) -> BotResponse:
        ctx = session.context
        if "section_id" not in ctx:
            sections = await _q(db,
                "SELECT id, name FROM sections WHERE class_id = :cid AND is_active = 1",
                {"cid": ctx.get("class_id", "")})
            matched = next(
                (s for s in sections if str(s["id"]) == message or s["name"].lower() == message.lower()),
                None)
            if not matched:
                matched = next((s for s in sections if message.lower() in s["name"].lower()), None)
            if not matched:
                return BotResponse(text="Section not found. Select:", type="options",
                                   options=[BotOption(id=str(s["id"]), label=s["name"]) for s in sections])
            session.patch_context({"section_id": str(matched["id"]), "section_name": matched["name"]})
            ctx = session.context
            session.current_step = "show"
            return BotResponse(
                text=f"Enter date (YYYY-MM-DD or 'today'):",
                type="question",
                options=[BotOption(id="today", label="Today"), BotOption(id="yesterday", label="Yesterday")],
                breadcrumb=f"View Attendance › {ctx.get('class_name','')}" ,
            )
        return await self._av_show(session, message, db, school_id)

    async def _av_show(self, session, message, db, school_id) -> BotResponse:
        from datetime import datetime as _dt
        ctx = session.context
        session.current_flow = None
        session.current_step = None

        msg_lower = message.lower().strip()
        if msg_lower in ("today", "now", "t", ""):
            view_date = date.today().isoformat()
        elif msg_lower in ("yesterday", "y"):
            view_date = (date.today() - timedelta(days=1)).isoformat()
        else:
            try:
                view_date = _dt.strptime(message.strip(), "%Y-%m-%d").date().isoformat()
            except ValueError:
                view_date = date.today().isoformat()

        section_id   = ctx.get("section_id", "")
        class_name   = ctx.get("class_name", "")
        section_name = ctx.get("section_name", "")

        records = await _q(
            db,
            """SELECT s.first_name + ' ' + s.last_name AS name,
                 s.admission_number, sa.status
               FROM student_attendance sa
               JOIN attendance_sessions asess ON sa.session_id = asess.id
               JOIN students s ON sa.student_id = s.id
               WHERE asess.section_id = :sec_id
                 AND CAST(asess.date AS DATE) = CAST(:dt AS DATE)
               ORDER BY s.first_name""",
            {"sec_id": section_id, "dt": view_date},
        )
        if not records:
            return BotResponse(
                text=(f"📋 No attendance data for **{class_name} - {section_name}** on {view_date}.\n\n"
                      f"Type **menu** to continue."),
                type="info",
                session_ended=True,
            )

        total   = len(records)
        present = sum(1 for r in records if r["status"] == "present")
        absent  = sum(1 for r in records if r["status"] == "absent")
        late    = sum(1 for r in records if r["status"] == "late")
        table_rows = [[r["name"], r["admission_number"], r["status"].upper()] for r in records[:30]]

        return BotResponse(
            text=(f"📋 **Attendance — {class_name} {section_name}** ({view_date})\n\n"
                  f"Total: {total} | Present: {present} | Absent: {absent} | Late: {late}\n"
                  f"Rate: {present/total*100:.0f}%"),
            type="data",
            cards=[{
                "type": "table",
                "title": f"Attendance Report — {view_date}",
                "headers": ["Name", "Admission No", "Status"],
                "rows": table_rows,
            }],
            actions=[{"label": "Attendance", "path": "/attendance"}],
            session_ended=True,
        )

    # ─── SUPER ADMIN ─────────────────────────────────────────────────────────

    async def _flow_sa_schools(
        self, session, message, payload, user, db, school_id
    ) -> BotResponse:
        session.current_flow = None
        rows = await _q(
            db,
            "SELECT name, code, is_active FROM schools ORDER BY created_at DESC LIMIT 20",
            {},
        )
        table_rows = [[r["name"], r["code"] or "", "Active" if r["is_active"] else "Inactive"]
                      for r in rows]
        return BotResponse(
            text=f"🏫 **All Schools** ({len(rows)} found):",
            type="data",
            cards=[{
                "type": "table",
                "title": "Schools",
                "headers": ["Name", "Code", "Status"],
                "rows": table_rows,
            }],
            actions=[{"label": "Super Admin", "path": "/super-admin"}],
            session_ended=True,
        )

    async def _flow_sa_plans(
        self, session, message, payload, user, db, school_id
    ) -> BotResponse:
        session.current_flow = None
        rows = await _q(
            db,
            "SELECT name, price_monthly_paise, max_students, max_staff FROM subscription_plans ORDER BY price_monthly_paise",
            {},
        )

        def fmt(p):
            return f"₹{p/100:,.0f}/mo" if p else "Free"

        table_rows = [
            [r["name"], fmt(r["price_monthly_paise"]),
             str(r.get("max_students") or "Unlimited"),
             str(r.get("max_staff") or "Unlimited")]
            for r in rows
        ]
        return BotResponse(
            text=f"📦 **Subscription Plans** ({len(rows)} plans):",
            type="data",
            cards=[{
                "type": "table",
                "title": "Plans",
                "headers": ["Name", "Price", "Max Students", "Max Staff"],
                "rows": table_rows,
            }],
            actions=[{"label": "Super Admin", "path": "/super-admin"}],
            session_ended=True,
        )
