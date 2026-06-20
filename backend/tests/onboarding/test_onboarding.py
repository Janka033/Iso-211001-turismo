"""Tests de integración del módulo onboarding (cadena router→service).

Mockean el repository (sin Supabase real) y las dependencias de auth, así que
ejercitan la cadena completa salvo el acceso a DB.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.security import CurrentUser, get_current_user, get_tenant_id
from app.main import app
from app.modules.onboarding import repository

FAKE_TENANT = "11111111-1111-1111-1111-111111111111"


def _fake_user() -> CurrentUser:
    return CurrentUser(
        user_id="user-1",
        email="demo@aventuraandina.com",
        tenant_id=FAKE_TENANT,
        role="empresa",
        token="fake-token",
    )


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch):
    store: dict[str, dict] = {}

    def fake_get(tenant_id: str, token: str) -> dict:
        return store.get(tenant_id, {})

    def fake_save(tenant_id: str, data: dict, token: str) -> dict:
        store[tenant_id] = data
        return data

    monkeypatch.setattr(repository, "get_onboarding", fake_get)
    monkeypatch.setattr(repository, "save_onboarding", fake_save)

    app.dependency_overrides[get_current_user] = _fake_user
    app.dependency_overrides[get_tenant_id] = lambda: FAKE_TENANT
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_get_onboarding_empty(client: TestClient) -> None:
    res = client.get("/onboarding")
    assert res.status_code == 200
    body = res.json()
    assert body["completeness"] == 0.0
    assert body["completed"] is False
    assert body["data"]["activities"] == []


def test_put_saves_and_measures(client: TestClient) -> None:
    res = client.put(
        "/onboarding",
        json={"activities": ["Rafting", "Parapente"], "main_region": "Santander"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["data"]["activities"] == ["Rafting", "Parapente"]
    assert body["data"]["main_region"] == "Santander"
    # 2 de 5 campos clave => 40%
    assert body["completeness"] == 40.0
    assert body["completed"] is False


def test_put_merges_incrementally(client: TestClient) -> None:
    client.put("/onboarding", json={"activities": ["Rafting"]})
    client.put("/onboarding", json={"main_region": "Huila"})
    body = client.get("/onboarding").json()
    # el segundo PUT no debe borrar activities (merge incremental)
    assert body["data"]["activities"] == ["Rafting"]
    assert body["data"]["main_region"] == "Huila"


def test_put_complete_reaches_100(client: TestClient) -> None:
    res = client.put(
        "/onboarding",
        json={
            "activities": ["Rafting"],
            "main_region": "Santander",
            "certified_guides": "4 a 10",
            "legal_representative": "María Gómez",
            "rnt_status": "Vigente",
        },
    )
    body = res.json()
    assert body["completeness"] == 100.0
    assert body["completed"] is True


def test_onboarding_requires_auth() -> None:
    # Sin overrides de dependencias: el bearer es obligatorio => 403.
    res = TestClient(app).get("/onboarding")
    assert res.status_code in (401, 403)
