"""
Round 3 — Exam Management Tests
Session-scoped fixtures bootstrap school + academic year + class + subject.
"""
import uuid
import pytest_asyncio
from httpx import AsyncClient
from tests.conftest import create_test_superadmin


def _data(resp) -> dict:
    body = resp.json()
    return body.get("data", body)


@pytest_asyncio.fixture(scope="session")
async def exam_setup(session_http_client: AsyncClient) -> dict:
    c = session_http_client
    await create_test_superadmin("exam_superadmin", "exam_super@test.com")

    login = await c.post("/api/v1/auth/login",
        json={"identifier": "exam_super@test.com", "password": "Admin@1234"})
    assert login.status_code == 200, login.text
    token = login.json()["data"]["access_token"]
    h = {"Authorization": f"Bearer {token}"}

    sr = await c.post("/api/v1/schools/bootstrap",
        json={"school_name": "Exam Test School"}, headers=h)
    assert sr.status_code == 201, sr.text
    school_id = _data(sr)["id"]
    hh = {**h, "X-School-Id": school_id}

    # Academic Year
    ayr = await c.post("/api/v1/academic-years",
        json={"name": "2025-26-exam", "start_date": "2025-04-01",
              "end_date": "2026-03-31", "is_current": True}, headers=hh)
    assert ayr.status_code in (200, 201), ayr.text
    ay_id = _data(ayr)["id"]

    # Class + Section
    cr = await c.post("/api/v1/classes",
        json={"name": "Class 7", "academic_year_id": ay_id}, headers=hh)
    assert cr.status_code in (200, 201), cr.text
    class_id = _data(cr)["id"]

    secr = await c.post(f"/api/v1/classes/{class_id}/sections",
        json={"name": "A"}, headers=hh)
    assert secr.status_code in (200, 201), secr.text
    section_id = _data(secr)["id"]

    # Subject (returns ok() wrapped)
    subj = await c.post("/api/v1/subjects",
        json={"name": "Mathematics", "code": "MATH", "full_marks": 100, "pass_marks": 35},
        headers=hh)
    assert subj.status_code in (200, 201), subj.text
    subject_id = subj.json()["data"]["id"]

    # Exam Type (create directly)
    et = await c.post("/api/v1/exam-types",
        json={"name": "Unit Test", "weightage": 25.0}, headers=hh)
    assert et.status_code in (200, 201), et.text
    exam_type_id = et.json()["id"]

    return {"headers": hh, "school_id": school_id, "academic_year_id": ay_id,
            "class_id": class_id, "section_id": section_id,
            "subject_id": subject_id, "exam_type_id": exam_type_id}


# ── Exam Types ─────────────────────────────────────────────────────────────────

class TestExamTypes:
    async def test_create_exam_type(self, async_client: AsyncClient, exam_setup: dict):
        resp = await async_client.post("/api/v1/exam-types",
            json={"name": "Half Yearly", "weightage": 30.0},
            headers=exam_setup["headers"])
        assert resp.status_code in (200, 201), resp.text
        assert resp.json()["name"] == "Half Yearly"

    async def test_list_exam_types(self, async_client: AsyncClient, exam_setup: dict):
        resp = await async_client.get("/api/v1/exam-types", headers=exam_setup["headers"])
        assert resp.status_code == 200, resp.text
        assert isinstance(resp.json(), list)
        assert len(resp.json()) >= 1

    async def test_update_exam_type(self, async_client: AsyncClient, exam_setup: dict):
        cr = await async_client.post("/api/v1/exam-types",
            json={"name": "Annual Exam", "weightage": 100.0},
            headers=exam_setup["headers"])
        assert cr.status_code in (200, 201), cr.text
        et_id = cr.json()["id"]

        ur = await async_client.put(f"/api/v1/exam-types/{et_id}",
            json={"name": "Annual Exam Updated"},
            headers=exam_setup["headers"])
        assert ur.status_code == 200, ur.text
        assert ur.json()["name"] == "Annual Exam Updated"

    async def test_delete_exam_type(self, async_client: AsyncClient, exam_setup: dict):
        cr = await async_client.post("/api/v1/exam-types",
            json={"name": "Delete Me Exam", "weightage": 10.0},
            headers=exam_setup["headers"])
        assert cr.status_code in (200, 201), cr.text
        et_id = cr.json()["id"]

        dr = await async_client.delete(f"/api/v1/exam-types/{et_id}",
            headers=exam_setup["headers"])
        assert dr.status_code in (200, 204), dr.text


# ── Grading Scales ─────────────────────────────────────────────────────────────

class TestGradingScales:
    async def test_upsert_grading_scale(self, async_client: AsyncClient, exam_setup: dict):
        resp = await async_client.put("/api/v1/grading-scales",
            json={
                "name": "Standard Grading",
                "ranges": [
                    {"grade": "A+", "min_pct": 90, "max_pct": 100, "grade_point": 10.0},
                    {"grade": "A",  "min_pct": 80, "max_pct": 89,  "grade_point": 9.0},
                    {"grade": "B+", "min_pct": 70, "max_pct": 79,  "grade_point": 8.0},
                    {"grade": "B",  "min_pct": 60, "max_pct": 69,  "grade_point": 7.0},
                    {"grade": "C",  "min_pct": 50, "max_pct": 59,  "grade_point": 6.0},
                    {"grade": "D",  "min_pct": 35, "max_pct": 49,  "grade_point": 5.0},
                    {"grade": "F",  "min_pct": 0,  "max_pct": 34,  "grade_point": 0.0},
                ],
            },
            headers=exam_setup["headers"])
        assert resp.status_code in (200, 201), resp.text
        data = resp.json()
        assert data["name"] == "Standard Grading"
        assert len(data["ranges"]) == 7

    async def test_get_grading_scale(self, async_client: AsyncClient, exam_setup: dict):
        resp = await async_client.get("/api/v1/grading-scales", headers=exam_setup["headers"])
        assert resp.status_code == 200, resp.text
        # May return null before upsert or the scale after upsert


# ── Exams ──────────────────────────────────────────────────────────────────────

class TestExams:
    async def test_create_exam(self, async_client: AsyncClient, exam_setup: dict):
        resp = await async_client.post("/api/v1/exams",
            json={
                "name": "Math Unit Test 1",
                "academic_year_id": exam_setup["academic_year_id"],
                "exam_type_id": exam_setup["exam_type_id"],
                "class_id": exam_setup["class_id"],
                "subject_id": exam_setup["subject_id"],
                "exam_date": "2025-06-15",
                "full_marks": 100,
                "pass_marks": 35,
            },
            headers=exam_setup["headers"])
        assert resp.status_code in (200, 201), resp.text
        data = resp.json()
        assert data["name"] == "Math Unit Test 1"

    async def test_list_exams(self, async_client: AsyncClient, exam_setup: dict):
        resp = await async_client.get("/api/v1/exams", headers=exam_setup["headers"])
        assert resp.status_code == 200, resp.text
        items = resp.json()
        assert isinstance(items, list)
        assert len(items) >= 1

    async def test_get_exam_by_id(self, async_client: AsyncClient, exam_setup: dict):
        # Create a fresh exam_type to avoid unique constraint (school+year+type+class+subject)
        et = await async_client.post("/api/v1/exam-types",
            json={"name": "Get Test Type", "weightage": 50.0},
            headers=exam_setup["headers"])
        assert et.status_code in (200, 201), et.text
        new_et_id = et.json()["id"]

        cr = await async_client.post("/api/v1/exams",
            json={
                "name": "Science Test",
                "academic_year_id": exam_setup["academic_year_id"],
                "exam_type_id": new_et_id,
                "class_id": exam_setup["class_id"],
                "subject_id": exam_setup["subject_id"],
                "full_marks": 50,
                "pass_marks": 17,
            },
            headers=exam_setup["headers"])
        assert cr.status_code in (200, 201), cr.text
        exam_id = cr.json()["id"]

        gr = await async_client.get(f"/api/v1/exams/{exam_id}", headers=exam_setup["headers"])
        assert gr.status_code == 200, gr.text
        assert gr.json()["id"] == exam_id

    async def test_update_exam(self, async_client: AsyncClient, exam_setup: dict):
        # Create a fresh exam_type to avoid unique constraint
        et = await async_client.post("/api/v1/exam-types",
            json={"name": "Update Test Type", "weightage": 50.0},
            headers=exam_setup["headers"])
        assert et.status_code in (200, 201), et.text
        new_et_id = et.json()["id"]

        cr = await async_client.post("/api/v1/exams",
            json={
                "name": "Exam To Update",
                "academic_year_id": exam_setup["academic_year_id"],
                "exam_type_id": new_et_id,
                "class_id": exam_setup["class_id"],
                "subject_id": exam_setup["subject_id"],
                "full_marks": 100,
                "pass_marks": 40,
            },
            headers=exam_setup["headers"])
        assert cr.status_code in (200, 201), cr.text
        exam_id = cr.json()["id"]

        ur = await async_client.put(f"/api/v1/exams/{exam_id}",
            json={"name": "Exam Updated"},
            headers=exam_setup["headers"])
        assert ur.status_code == 200, ur.text
        assert ur.json()["name"] == "Exam Updated"
