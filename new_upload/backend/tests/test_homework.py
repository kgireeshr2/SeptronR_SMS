"""
Round 4 — Homework & PTM Tests
Covers: Homework CRUD, Submissions, Grading, Lesson Plans, PTM Events/Slots/Bookings
"""
import uuid
import pytest_asyncio
from httpx import AsyncClient
from tests.conftest import create_test_superadmin


def _data(resp):
    body = resp.json()
    if isinstance(body, list):
        return body
    return body.get("data", body)


@pytest_asyncio.fixture(scope="session")
async def hw_setup(session_http_client: AsyncClient) -> dict:
    c = session_http_client
    uid = uuid.uuid4().hex[:6]
    await create_test_superadmin(f"hw_admin_{uid}", f"hw_{uid}@test.com")

    login = await c.post("/api/v1/auth/login",
        json={"identifier": f"hw_{uid}@test.com", "password": "Admin@1234"})
    assert login.status_code == 200, login.text
    token = login.json()["data"]["access_token"]
    h = {"Authorization": f"Bearer {token}"}

    me = await c.get("/api/v1/auth/me", headers=h)
    teacher_id = me.json().get("data", me.json())["id"]

    sr = await c.post("/api/v1/schools/bootstrap",
        json={"school_name": f"HW School {uid}"}, headers=h)
    assert sr.status_code == 201, sr.text
    school_id = _data(sr)["id"]
    hh = {**h, "X-School-Id": school_id}

    ayr = await c.post("/api/v1/academic-years",
        json={"name": f"2025-26-hw-{uid}", "start_date": "2025-04-01",
              "end_date": "2026-03-31", "is_current": True}, headers=hh)
    assert ayr.status_code in (200, 201), ayr.text
    ay_id = _data(ayr)["id"]

    cr = await c.post("/api/v1/classes",
        json={"name": "Class 9", "academic_year_id": ay_id}, headers=hh)
    assert cr.status_code in (200, 201), cr.text
    class_id = _data(cr)["id"]

    secr = await c.post(f"/api/v1/classes/{class_id}/sections",
        json={"name": "A"}, headers=hh)
    assert secr.status_code in (200, 201), secr.text
    section_id = _data(secr)["id"]

    subr = await c.post("/api/v1/subjects",
        json={"name": "Mathematics", "code": f"MATH{uid}", "class_id": class_id},
        headers=hh)
    assert subr.status_code in (200, 201), subr.text
    subject_id = _data(subr)["id"]

    suid = uuid.uuid4().hex[:8]
    stu = await c.post("/api/v1/students/", json={
        "first_name": "HW",
        "last_name": f"Student{suid}",
        "date_of_birth": "2010-06-15",
        "gender": "male",
        "admission_date": "2025-04-01",
        "enrollment": {
            "class_id": class_id,
            "section_id": section_id,
            "academic_year_id": ay_id,
            "roll_number": "011",
        },
    }, headers=hh)
    assert stu.status_code in (200, 201), stu.text
    student_id = stu.json()["id"]

    return {
        "headers": hh,
        "school_id": school_id,
        "academic_year_id": ay_id,
        "class_id": class_id,
        "section_id": section_id,
        "subject_id": subject_id,
        "student_id": student_id,
        "teacher_id": teacher_id,
    }


def _hw_json(s: dict) -> dict:
    return {
        "class_id": s["class_id"],
        "section_id": s["section_id"],
        "subject_id": s["subject_id"],
        "academic_year_id": s["academic_year_id"],
        "title": "Chapter 5 Exercises",
        "description": "Complete exercises from chapter 5.",
        "due_date": "2025-12-20",
    }


# ── Homework ──────────────────────────────────────────────────────────────────

class TestHomework:
    async def test_create_homework(self, async_client: AsyncClient, hw_setup: dict):
        resp = await async_client.post("/api/v1/homework",
            json=_hw_json(hw_setup), headers=hw_setup["headers"])
        assert resp.status_code in (200, 201), resp.text
        data = _data(resp)
        assert data["title"] == "Chapter 5 Exercises"

    async def test_list_homework(self, async_client: AsyncClient, hw_setup: dict):
        await async_client.post("/api/v1/homework",
            json=_hw_json(hw_setup), headers=hw_setup["headers"])
        resp = await async_client.get("/api/v1/homework", headers=hw_setup["headers"])
        assert resp.status_code == 200, resp.text
        items = _data(resp)
        assert isinstance(items, list)
        assert len(items) >= 1

    async def test_update_homework(self, async_client: AsyncClient, hw_setup: dict):
        cr = await async_client.post("/api/v1/homework",
            json=_hw_json(hw_setup), headers=hw_setup["headers"])
        assert cr.status_code in (200, 201), cr.text
        hw_id = _data(cr)["id"]

        resp = await async_client.put(f"/api/v1/homework/{hw_id}",
            json={"title": "Chapter 5 (Updated)"},
            headers=hw_setup["headers"])
        assert resp.status_code in (200, 201), resp.text
        data = _data(resp)
        assert data["title"] == "Chapter 5 (Updated)"

    async def test_create_submission(self, async_client: AsyncClient, hw_setup: dict):
        cr = await async_client.post("/api/v1/homework",
            json=_hw_json(hw_setup), headers=hw_setup["headers"])
        assert cr.status_code in (200, 201), cr.text
        hw_id = _data(cr)["id"]

        resp = await async_client.post(f"/api/v1/homework/{hw_id}/submissions",
            json={"homework_id": hw_id, "student_id": hw_setup["student_id"],
                  "content": "My solutions."},
            headers=hw_setup["headers"])
        assert resp.status_code in (200, 201), resp.text
        data = _data(resp)
        assert data["student_id"] == hw_setup["student_id"]

    async def test_list_submissions(self, async_client: AsyncClient, hw_setup: dict):
        cr = await async_client.post("/api/v1/homework",
            json=_hw_json(hw_setup), headers=hw_setup["headers"])
        assert cr.status_code in (200, 201), cr.text
        hw_id = _data(cr)["id"]
        await async_client.post(f"/api/v1/homework/{hw_id}/submissions",
            json={"homework_id": hw_id, "student_id": hw_setup["student_id"],
                  "content": "Test."},
            headers=hw_setup["headers"])

        resp = await async_client.get(f"/api/v1/homework/{hw_id}/submissions",
            headers=hw_setup["headers"])
        assert resp.status_code == 200, resp.text

    async def test_grade_submission(self, async_client: AsyncClient, hw_setup: dict):
        cr = await async_client.post("/api/v1/homework",
            json=_hw_json(hw_setup), headers=hw_setup["headers"])
        assert cr.status_code in (200, 201), cr.text
        hw_id = _data(cr)["id"]
        sr = await async_client.post(f"/api/v1/homework/{hw_id}/submissions",
            json={"homework_id": hw_id, "student_id": hw_setup["student_id"],
                  "content": "Test."},
            headers=hw_setup["headers"])
        assert sr.status_code in (200, 201), sr.text
        sub_id = _data(sr)["id"]

        resp = await async_client.put(f"/api/v1/homework/submissions/{sub_id}/grade",
            json={"marks_given": 18, "remarks": "Good work!"},
            headers=hw_setup["headers"])
        assert resp.status_code in (200, 201), resp.text
        data = _data(resp)
        assert data["marks_given"] == 18


# ── Lesson Plans ──────────────────────────────────────────────────────────────

class TestLessonPlans:
    def _lp_json(self, s: dict, period: int = 1, date: str = "2025-11-25") -> dict:
        return {
            "class_id": s["class_id"],
            "section_id": s["section_id"],
            "subject_id": s["subject_id"],
            "academic_year_id": s["academic_year_id"],
            "title": f"Algebra Lesson {period}",
            "plan_date": date,
            "period_number": period,
            "content": "Introduction to Algebra — basic identities.",
            "learning_objectives": "Understand algebraic identities.",
        }

    async def test_create_lesson_plan(self, async_client: AsyncClient, hw_setup: dict):
        resp = await async_client.post("/api/v1/lesson-plans",
            json=self._lp_json(hw_setup), headers=hw_setup["headers"])
        assert resp.status_code in (200, 201), resp.text
        data = _data(resp)
        assert data["period_number"] == 1

    async def test_list_lesson_plans(self, async_client: AsyncClient, hw_setup: dict):
        await async_client.post("/api/v1/lesson-plans",
            json=self._lp_json(hw_setup, period=2, date="2025-11-26"),
            headers=hw_setup["headers"])
        resp = await async_client.get("/api/v1/lesson-plans", headers=hw_setup["headers"])
        assert resp.status_code == 200, resp.text
        items = _data(resp)
        assert isinstance(items, list)
        assert len(items) >= 1


# ── PTM Events & Slots ────────────────────────────────────────────────────────

class TestPTM:
    def _ptm_json(self, s: dict, title: str = "Q2 PTM", date: str = "2025-12-05") -> dict:
        return {
            "title": title,
            "ptm_date": date,
            "slot_duration_minutes": 15,
            "academic_year_id": s["academic_year_id"],
            "description": "Quarterly parent-teacher meeting.",
        }

    async def test_create_ptm_event(self, async_client: AsyncClient, hw_setup: dict):
        resp = await async_client.post("/api/v1/ptm/events",
            json=self._ptm_json(hw_setup), headers=hw_setup["headers"])
        assert resp.status_code in (200, 201), resp.text
        data = _data(resp)
        assert data["title"] == "Q2 PTM"

    async def test_list_ptm_events(self, async_client: AsyncClient, hw_setup: dict):
        await async_client.post("/api/v1/ptm/events",
            json=self._ptm_json(hw_setup, title="PTM List Test", date="2025-12-06"),
            headers=hw_setup["headers"])
        resp = await async_client.get("/api/v1/ptm/events", headers=hw_setup["headers"])
        assert resp.status_code == 200, resp.text
        items = _data(resp)
        assert isinstance(items, list)
        assert len(items) >= 1

    async def test_create_ptm_slot(self, async_client: AsyncClient, hw_setup: dict):
        er = await async_client.post("/api/v1/ptm/events",
            json=self._ptm_json(hw_setup, title="PTM Slot Test", date="2025-12-07"),
            headers=hw_setup["headers"])
        assert er.status_code in (200, 201), er.text
        event_id = _data(er)["id"]

        resp = await async_client.post("/api/v1/ptm/slots",
            json={"ptm_event_id": event_id, "teacher_id": hw_setup["teacher_id"],
                  "slot_start": "2025-12-07T09:00:00",
                  "slot_end": "2025-12-07T09:15:00"},
            headers=hw_setup["headers"])
        assert resp.status_code in (200, 201), resp.text
        data = _data(resp)
        assert data["teacher_id"] == hw_setup["teacher_id"]

    async def test_list_ptm_event_slots(self, async_client: AsyncClient, hw_setup: dict):
        er = await async_client.post("/api/v1/ptm/events",
            json=self._ptm_json(hw_setup, title="PTM Slot List", date="2025-12-08"),
            headers=hw_setup["headers"])
        assert er.status_code in (200, 201), er.text
        event_id = _data(er)["id"]
        await async_client.post("/api/v1/ptm/slots",
            json={"ptm_event_id": event_id, "teacher_id": hw_setup["teacher_id"],
                  "slot_start": "2025-12-08T09:00:00",
                  "slot_end": "2025-12-08T09:15:00"},
            headers=hw_setup["headers"])

        resp = await async_client.get(f"/api/v1/ptm/events/{event_id}/slots",
            headers=hw_setup["headers"])
        assert resp.status_code == 200, resp.text

    async def test_create_ptm_booking(self, async_client: AsyncClient, hw_setup: dict):
        er = await async_client.post("/api/v1/ptm/events",
            json=self._ptm_json(hw_setup, title="PTM Booking", date="2025-12-09"),
            headers=hw_setup["headers"])
        assert er.status_code in (200, 201), er.text
        event_id = _data(er)["id"]
        slr = await async_client.post("/api/v1/ptm/slots",
            json={"ptm_event_id": event_id, "teacher_id": hw_setup["teacher_id"],
                  "slot_start": "2025-12-09T09:00:00",
                  "slot_end": "2025-12-09T09:15:00"},
            headers=hw_setup["headers"])
        assert slr.status_code in (200, 201), slr.text
        slot_id = _data(slr)["id"]

        resp = await async_client.post("/api/v1/ptm/bookings",
            json={"slot_id": slot_id, "student_id": hw_setup["student_id"],
                  "parent_notes": "Please discuss exam results."},
            headers=hw_setup["headers"])
        assert resp.status_code in (200, 201), resp.text
        data = _data(resp)
        assert data["student_id"] == hw_setup["student_id"]

    async def test_list_ptm_bookings(self, async_client: AsyncClient, hw_setup: dict):
        er = await async_client.post("/api/v1/ptm/events",
            json=self._ptm_json(hw_setup, title="PTM Booking List", date="2025-12-10"),
            headers=hw_setup["headers"])
        assert er.status_code in (200, 201), er.text
        event_id = _data(er)["id"]
        slr = await async_client.post("/api/v1/ptm/slots",
            json={"ptm_event_id": event_id, "teacher_id": hw_setup["teacher_id"],
                  "slot_start": "2025-12-10T09:00:00",
                  "slot_end": "2025-12-10T09:15:00"},
            headers=hw_setup["headers"])
        assert slr.status_code in (200, 201), slr.text
        slot_id = _data(slr)["id"]
        await async_client.post("/api/v1/ptm/bookings",
            json={"slot_id": slot_id, "student_id": hw_setup["student_id"],
                  "parent_notes": "Test."},
            headers=hw_setup["headers"])

        resp = await async_client.get(f"/api/v1/ptm/events/{event_id}/bookings",
            headers=hw_setup["headers"])
        assert resp.status_code == 200, resp.text
