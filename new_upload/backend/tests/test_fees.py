"""
Round 3 — Fee Management Tests
Session-scoped fixtures bootstrap school + academic year + class + student.
"""
import uuid
import pytest_asyncio
from httpx import AsyncClient
from tests.conftest import create_test_superadmin


def _data(resp) -> dict:
    body = resp.json()
    return body.get("data", body)


@pytest_asyncio.fixture(scope="session")
async def fee_setup(session_http_client: AsyncClient) -> dict:
    c = session_http_client
    await create_test_superadmin("fee_superadmin", "fee_super@test.com")

    login = await c.post("/api/v1/auth/login",
        json={"identifier": "fee_super@test.com", "password": "Admin@1234"})
    assert login.status_code == 200, login.text
    token = login.json()["data"]["access_token"]
    h = {"Authorization": f"Bearer {token}"}

    sr = await c.post("/api/v1/schools/bootstrap",
        json={"school_name": "Fee Test School"}, headers=h)
    assert sr.status_code == 201, sr.text
    school_id = _data(sr)["id"]
    hh = {**h, "X-School-Id": school_id}

    # Academic Year
    ayr = await c.post("/api/v1/academic-years",
        json={"name": "2025-26-fee", "start_date": "2025-04-01",
              "end_date": "2026-03-31", "is_current": True}, headers=hh)
    assert ayr.status_code in (200, 201), ayr.text
    ay_id = _data(ayr)["id"]

    # Class + Section
    cr = await c.post("/api/v1/classes",
        json={"name": "Class 6", "academic_year_id": ay_id}, headers=hh)
    assert cr.status_code in (200, 201), cr.text
    class_id = _data(cr)["id"]

    secr = await c.post(f"/api/v1/classes/{class_id}/sections",
        json={"name": "A"}, headers=hh)
    assert secr.status_code in (200, 201), secr.text
    section_id = _data(secr)["id"]

    # Enroll a student (direct create)
    uid = uuid.uuid4().hex[:8]
    stu = await c.post("/api/v1/students/", json={
        "first_name": "Fee",
        "last_name": f"Student{uid}",
        "date_of_birth": "2012-05-10",
        "gender": "female",
        "admission_date": "2025-04-01",
        "enrollment": {
            "class_id": class_id,
            "section_id": section_id,
            "academic_year_id": ay_id,
            "roll_number": "001",
        },
    }, headers=hh)
    assert stu.status_code in (200, 201), stu.text
    student_id = stu.json()["id"]

    return {"headers": hh, "school_id": school_id, "academic_year_id": ay_id,
            "class_id": class_id, "section_id": section_id, "student_id": student_id}


# ── Fee Categories ─────────────────────────────────────────────────────────────

class TestFeeCategories:
    async def test_create_fee_category(self, async_client: AsyncClient, fee_setup: dict):
        resp = await async_client.post("/api/v1/fees/categories",
            json={"name": "Tuition Fee", "description": "Monthly tuition"},
            headers=fee_setup["headers"])
        assert resp.status_code in (200, 201), resp.text
        data = resp.json()
        assert data["name"] == "Tuition Fee"

    async def test_list_fee_categories(self, async_client: AsyncClient, fee_setup: dict):
        resp = await async_client.get("/api/v1/fees/categories", headers=fee_setup["headers"])
        assert resp.status_code == 200, resp.text
        assert isinstance(resp.json(), list)

    async def test_update_fee_category(self, async_client: AsyncClient, fee_setup: dict):
        cr = await async_client.post("/api/v1/fees/categories",
            json={"name": "Transport Fee"},
            headers=fee_setup["headers"])
        assert cr.status_code in (200, 201), cr.text
        cat_id = cr.json()["id"]

        ur = await async_client.put(f"/api/v1/fees/categories/{cat_id}",
            json={"name": "Transport Fee Updated"},
            headers=fee_setup["headers"])
        assert ur.status_code == 200, ur.text
        assert ur.json()["name"] == "Transport Fee Updated"

    async def test_delete_fee_category(self, async_client: AsyncClient, fee_setup: dict):
        cr = await async_client.post("/api/v1/fees/categories",
            json={"name": "Delete Me Fee"},
            headers=fee_setup["headers"])
        assert cr.status_code in (200, 201), cr.text
        cat_id = cr.json()["id"]

        dr = await async_client.delete(f"/api/v1/fees/categories/{cat_id}",
            headers=fee_setup["headers"])
        assert dr.status_code in (200, 204), dr.text


# ── Fee Discounts ──────────────────────────────────────────────────────────────

class TestFeeDiscounts:
    async def test_create_fee_discount(self, async_client: AsyncClient, fee_setup: dict):
        resp = await async_client.post("/api/v1/fees/discounts",
            json={"name": "Sibling Discount", "type": "percentage", "value": 10.0,
                  "applicable_to": "student"},
            headers=fee_setup["headers"])
        assert resp.status_code in (200, 201), resp.text
        assert resp.json()["name"] == "Sibling Discount"

    async def test_list_fee_discounts(self, async_client: AsyncClient, fee_setup: dict):
        resp = await async_client.get("/api/v1/fees/discounts", headers=fee_setup["headers"])
        assert resp.status_code == 200, resp.text
        assert isinstance(resp.json(), list)

    async def test_update_fee_discount(self, async_client: AsyncClient, fee_setup: dict):
        cr = await async_client.post("/api/v1/fees/discounts",
            json={"name": "Staff Discount", "type": "percentage", "value": 25.0,
                  "applicable_to": "student"},
            headers=fee_setup["headers"])
        assert cr.status_code in (200, 201), cr.text
        disc_id = cr.json()["id"]

        ur = await async_client.put(f"/api/v1/fees/discounts/{disc_id}",
            json={"value": 30.0},
            headers=fee_setup["headers"])
        assert ur.status_code == 200, ur.text
        assert ur.json()["value"] == 30.0


# ── Fee Structures ─────────────────────────────────────────────────────────────

class TestFeeStructures:
    async def test_create_fee_structure(self, async_client: AsyncClient, fee_setup: dict):
        # First create a category
        cat_r = await async_client.post("/api/v1/fees/categories",
            json={"name": "Admission Fee"},
            headers=fee_setup["headers"])
        assert cat_r.status_code in (200, 201), cat_r.text
        cat_id = cat_r.json()["id"]

        resp = await async_client.post("/api/v1/fees/structures",
            json={
                "class_id": fee_setup["class_id"],
                "academic_year_id": fee_setup["academic_year_id"],
                "items": [
                    {"fee_category_id": cat_id, "amount": 50000,
                     "frequency": "annual", "is_active": True},
                ],
            },
            headers=fee_setup["headers"])
        assert resp.status_code in (200, 201), resp.text
        assert isinstance(resp.json(), list)

    async def test_list_fee_structures(self, async_client: AsyncClient, fee_setup: dict):
        resp = await async_client.get("/api/v1/fees/structures",
            params={"academic_year_id": fee_setup["academic_year_id"]},
            headers=fee_setup["headers"])
        assert resp.status_code == 200, resp.text
        assert isinstance(resp.json(), list)
