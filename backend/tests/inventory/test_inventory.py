"""Tests de integración del módulo inventory (router→service).

Mockean el repository (sin Supabase ni Storage) y la auth. Cubren el CRUD de
ítems, el filtro por categoría, la validación de categoría y la subida de
evidencia (foto).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.core.security import CurrentUser, get_current_user, get_tenant_id
from app.main import app
from app.modules.inventory import repository

FAKE_TENANT = "11111111-1111-1111-1111-111111111111"


def _fake_user() -> CurrentUser:
    return CurrentUser(
        user_id="u1",
        email="demo@aventuraandina.com",
        tenant_id=FAKE_TENANT,
        role="empresa",
        token="tok",
    )


def _new_item(client: TestClient, category: str, name: str, attributes: dict | None = None) -> str:
    r = client.post(
        "/inventory",
        json={"category": category, "name": name, "attributes": attributes or {}},
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch):
    items: dict[str, dict] = {}
    evidence: dict[str, dict] = {}

    def fake_list_items(tenant_id, token, category=None):
        return [
            r
            for r in items.values()
            if r["tenant_id"] == tenant_id and (category is None or r["category"] == category)
        ]

    def fake_get_item(tenant_id, item_id, token):
        r = items.get(item_id)
        return {"id": item_id} if r and r["tenant_id"] == tenant_id else None

    def fake_create_item(tenant_id, data, token):
        iid = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()
        row = {"id": iid, "tenant_id": tenant_id, "created_at": now, "updated_at": now, **data}
        items[iid] = row
        return row

    def fake_update_item(tenant_id, item_id, changes, token):
        r = items.get(item_id)
        if not r or r["tenant_id"] != tenant_id:
            return None
        r.update(changes)
        return r

    def fake_delete_item(tenant_id, item_id, token):
        r = items.get(item_id)
        if not r or r["tenant_id"] != tenant_id:
            return False
        items.pop(item_id, None)
        return True

    def fake_count_evidence(tenant_id, item_ids, token):
        return {}

    def fake_add_evidence_row(tenant_id, item_id, storage_path, caption, token):
        eid = str(uuid.uuid4())
        row = {
            "id": eid,
            "tenant_id": tenant_id,
            "item_id": item_id,
            "storage_path": storage_path,
            "caption": caption,
            "uploaded_at": datetime.now(UTC).isoformat(),
        }
        evidence[eid] = row
        return row

    def fake_upload_file(tenant_id, item_id, filename, content, content_type):
        return f"{tenant_id}/{item_id}/{filename}"

    def fake_signed_url(path, expires_in=300):
        return f"https://signed/{path}"

    def fake_list_evidence(tenant_id, item_id, token):
        return [r for r in evidence.values() if r["item_id"] == item_id]

    for name, fn in {
        "list_items": fake_list_items,
        "get_item": fake_get_item,
        "create_item": fake_create_item,
        "update_item": fake_update_item,
        "delete_item": fake_delete_item,
        "count_evidence": fake_count_evidence,
        "add_evidence_row": fake_add_evidence_row,
        "upload_evidence_file": fake_upload_file,
        "signed_evidence_url": fake_signed_url,
        "list_evidence": fake_list_evidence,
    }.items():
        monkeypatch.setattr(repository, name, fn)

    app.dependency_overrides[get_current_user] = _fake_user
    app.dependency_overrides[get_tenant_id] = lambda: FAKE_TENANT
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_create_and_list(client: TestClient) -> None:
    iid = _new_item(
        client, "vehiculo", "Cuatrimoto", {"estado": "operativa", "placa": "ABC123"}
    )
    listed = client.get("/inventory").json()
    match = [i for i in listed if i["id"] == iid]
    assert match and match[0]["attributes"]["placa"] == "ABC123"


def test_filter_by_category(client: TestClient) -> None:
    _new_item(client, "salida_emergencia", "Salida norte")
    _new_item(client, "guia", "Juan")
    sal = client.get("/inventory?category=salida_emergencia").json()
    assert len(sal) == 1 and sal[0]["name"] == "Salida norte"


def test_update_and_delete(client: TestClient) -> None:
    iid = _new_item(client, "equipo", "Arnés")
    u = client.put(f"/inventory/{iid}", json={"name": "Arnés certificado"})
    assert u.status_code == 200 and u.json()["name"] == "Arnés certificado"
    assert client.delete(f"/inventory/{iid}").status_code == 204
    # Borrar de nuevo (ya no existe / RLS lo filtraría) => 404, no 204 silencioso.
    assert client.delete(f"/inventory/{iid}").status_code == 404


def test_delete_missing_item_returns_404(client: TestClient) -> None:
    assert client.delete(f"/inventory/{uuid.uuid4()}").status_code == 404


def test_invalid_category_rejected(client: TestClient) -> None:
    r = client.post(
        "/inventory", json={"category": "nave_espacial", "name": "X", "attributes": {}}
    )
    assert r.status_code == 422


def test_evidence_upload(client: TestClient) -> None:
    iid = _new_item(client, "vehiculo", "Cuatrimoto")
    r = client.post(
        f"/inventory/{iid}/evidence",
        files={"file": ("foto.jpg", b"\xff\xd8\xff fake jpg", "image/jpeg")},
        data={"caption": "Cuatrimoto nueva"},
    )
    assert r.status_code == 201, r.text
    assert r.json()["url"].startswith("https://signed/")
    assert r.json()["caption"] == "Cuatrimoto nueva"


def test_evidence_rejects_non_image(client: TestClient) -> None:
    iid = _new_item(client, "equipo", "Arnés")
    r = client.post(
        f"/inventory/{iid}/evidence",
        files={"file": ("x.pdf", b"%PDF-1.4", "application/pdf")},
    )
    assert r.status_code == 415


def test_requires_auth() -> None:
    assert TestClient(app).get("/inventory").status_code in (401, 403)
