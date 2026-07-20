"""
Round 4 — Document Templates Tests
Covers: CRUD for document templates (ID cards, certificates, etc.)
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from tests.conftest import create_test_superadmin


def _data(resp):
    body = resp.json()
    if isinstance(body, list):
        return body
    return body.get("data", body)


@pytest_asyncio.fixture(scope="session")
async def tmpl_setup(session_http_client: AsyncClient) -> dict:
    c = session_http_client
    await create_test_superadmin("tmpl_superadmin", "tmpl_super@test.com")

    login = await c.post("/api/v1/auth/login",
        json={"identifier": "tmpl_super@test.com", "password": "Admin@1234"})
    assert login.status_code == 200, login.text
    token = login.json()["data"]["access_token"]
    h = {"Authorization": f"Bearer {token}"}

    sr = await c.post("/api/v1/schools/bootstrap",
        json={"school_name": "Templates Test School"}, headers=h)
    assert sr.status_code == 201, sr.text
    body = sr.json()
    school_id = (body.get("data") or body)["id"]
    hh = {**h, "X-School-Id": school_id}

    return {"headers": hh, "school_id": school_id}


def _id_card_payload():
    return {
        "template_name": "Student ID Card",
        "template_type": "id_card",
        "canvas_width_mm": 85.6,
        "canvas_height_mm": 54.0,
        "template_html": "<div>{{student_name}} - {{roll_number}}</div>",
        "is_default": True,
        "is_active": True,
    }


def _cert_payload():
    return {
        "template_name": "Merit Certificate",
        "template_type": "certificate",
        "canvas_width_mm": 297.0,
        "canvas_height_mm": 210.0,
        "template_html": "<div>Certificate of Merit — {{student_name}}</div>",
        "is_default": False,
        "is_active": True,
    }


class TestDocumentTemplates:
    async def test_list_templates_empty(self, async_client: AsyncClient, tmpl_setup: dict):
        resp = await async_client.get("/api/v1/document-templates",
            headers=tmpl_setup["headers"])
        assert resp.status_code == 200, resp.text
        items = _data(resp)
        assert isinstance(items, list)

    async def test_create_id_card_template(self, async_client: AsyncClient, tmpl_setup: dict):
        resp = await async_client.post("/api/v1/document-templates",
            json=_id_card_payload(),
            headers=tmpl_setup["headers"])
        assert resp.status_code in (200, 201), resp.text
        data = _data(resp)
        assert data["template_name"] == "Student ID Card"
        assert data["template_type"] == "id_card"

    async def test_get_template_by_id(self, async_client: AsyncClient, tmpl_setup: dict):
        # Create within this session so async_client can see it
        cr = await async_client.post("/api/v1/document-templates",
            json=_id_card_payload(), headers=tmpl_setup["headers"])
        assert cr.status_code in (200, 201), cr.text
        tmpl_id = _data(cr)["id"]

        resp = await async_client.get(f"/api/v1/document-templates/{tmpl_id}",
            headers=tmpl_setup["headers"])
        assert resp.status_code == 200, resp.text
        data = _data(resp)
        assert data["id"] == tmpl_id

    async def test_update_template(self, async_client: AsyncClient, tmpl_setup: dict):
        # Create within this session
        cr = await async_client.post("/api/v1/document-templates",
            json=_id_card_payload(), headers=tmpl_setup["headers"])
        assert cr.status_code in (200, 201), cr.text
        tmpl_id = _data(cr)["id"]

        resp = await async_client.put(f"/api/v1/document-templates/{tmpl_id}",
            json={"template_name": "Student ID Card (Updated)", "is_default": False},
            headers=tmpl_setup["headers"])
        assert resp.status_code in (200, 201), resp.text
        data = _data(resp)
        assert data["template_name"] == "Student ID Card (Updated)"

    async def test_create_certificate_template(self, async_client: AsyncClient, tmpl_setup: dict):
        resp = await async_client.post("/api/v1/document-templates",
            json=_cert_payload(),
            headers=tmpl_setup["headers"])
        assert resp.status_code in (200, 201), resp.text
        data = _data(resp)
        assert data["template_type"] == "certificate"

    async def test_list_templates_by_type(self, async_client: AsyncClient, tmpl_setup: dict):
        # Create an id_card template first so the list is non-empty
        await async_client.post("/api/v1/document-templates",
            json=_id_card_payload(), headers=tmpl_setup["headers"])

        resp = await async_client.get("/api/v1/document-templates?template_type=id_card",
            headers=tmpl_setup["headers"])
        assert resp.status_code == 200, resp.text
        items = _data(resp)
        assert isinstance(items, list)
        assert len(items) >= 1

    async def test_delete_template(self, async_client: AsyncClient, tmpl_setup: dict):
        # Create within this session
        cr = await async_client.post("/api/v1/document-templates",
            json=_cert_payload(), headers=tmpl_setup["headers"])
        assert cr.status_code in (200, 201), cr.text
        tmpl_id = _data(cr)["id"]

        resp = await async_client.delete(f"/api/v1/document-templates/{tmpl_id}",
            headers=tmpl_setup["headers"])
        assert resp.status_code in (200, 204), resp.text
