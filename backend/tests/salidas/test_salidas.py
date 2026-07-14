"""Tests de integración del módulo salidas (router→service).

Mockean el repository (sin Supabase) y la auth. Cubren: creación de salidas
con roles (incluido el legado 'empresa'), transiciones de estado, asignación
de guías, manifiesto, sync idempotente de eventos y el registro público del
turista (token, expiración, cupo, menores, duplicados, alerta médica).
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from postgrest.exceptions import APIError

from app.core.security import CurrentUser, get_current_user
from app.main import app
from app.modules.salidas import repository

FAKE_TENANT = "11111111-1111-1111-1111-111111111111"
OTHER_TENANT = "22222222-2222-2222-2222-222222222222"
ACTIVITY_ID = "aaaaaaaa-0000-0000-0000-000000000001"
INACTIVE_ACTIVITY_ID = "aaaaaaaa-0000-0000-0000-000000000002"
GUIA_ID = "bbbbbbbb-0000-0000-0000-000000000001"
RECEP_ID = "bbbbbbbb-0000-0000-0000-000000000002"


def _dup_error() -> APIError:
    return APIError(
        {"message": "duplicate key value", "code": "23505", "details": "", "hint": ""}
    )


@pytest.fixture
def state() -> dict:
    return {
        "activities": {
            ACTIVITY_ID: {
                "id": ACTIVITY_ID,
                "name": "Tour ATV Salento",
                "is_active": True,
                "min_age": 10,
                "max_age": 70,
                "participant_form_fields": [],
            },
            INACTIVE_ACTIVITY_ID: {
                "id": INACTIVE_ACTIVITY_ID,
                "name": "Rafting (inactiva)",
                "is_active": False,
                "min_age": None,
                "max_age": None,
                "participant_form_fields": [],
            },
        },
        "salidas": {},
        "guias": {},  # (salida_id, guia_user_id) -> row
        "profiles": {
            GUIA_ID: {"user_id": GUIA_ID, "role": "guia"},
            RECEP_ID: {"user_id": RECEP_ID, "role": "recepcionista"},
        },
        "participantes": {},
        "salud": {},
        "eventos": {},
    }


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, state: dict):
    def fake_get_activity_profile(tenant_id, activity_profile_id, token):
        return state["activities"].get(activity_profile_id)

    def fake_list_activity_profiles(tenant_id, token):
        return [
            {
                "id": a["id"],
                "name": a["name"],
                "activity_type": a.get("activity_type", "atv"),
                "min_age": a["min_age"],
                "max_age": a["max_age"],
                "difficulty": a.get("difficulty"),
                "duration_minutes": a.get("duration_minutes"),
                "location": a.get("location"),
            }
            for a in state["activities"].values()
            if a["is_active"]
        ]

    def fake_insert_salida(tenant_id, data, token):
        sid = str(uuid.uuid4())
        row = {
            "id": sid,
            "tenant_id": tenant_id,
            "status": "programada",
            "started_at": None,
            "finished_at": None,
            "created_at": datetime.now(UTC).isoformat(),
            **data,
        }
        state["salidas"][sid] = row
        return row

    def fake_list_salidas(tenant_id, token, status=None):
        return [
            r
            for r in state["salidas"].values()
            if r["tenant_id"] == tenant_id and (status is None or r["status"] == status)
        ]

    def fake_get_salida(tenant_id, salida_id, token):
        r = state["salidas"].get(salida_id)
        return r if r and r["tenant_id"] == tenant_id else None

    def fake_update_salida(tenant_id, salida_id, changes, token):
        r = fake_get_salida(tenant_id, salida_id, token)
        if not r:
            return None
        r.update(changes)
        return r

    def fake_insert_guia(tenant_id, salida_id, guia_user_id, is_lead, token):
        key = (salida_id, guia_user_id)
        if key in state["guias"]:
            raise _dup_error()
        row = {"guia_user_id": guia_user_id, "is_lead": is_lead}
        state["guias"][key] = row
        return row

    def fake_delete_guia(tenant_id, salida_id, guia_user_id, token):
        return state["guias"].pop((salida_id, guia_user_id), None) is not None

    def fake_get_profile_for_tenant(tenant_id, user_id):
        return state["profiles"].get(user_id)

    def fake_list_participantes(tenant_id, salida_id, token):
        return [
            p
            for p in state["participantes"].values()
            if p["tenant_id"] == tenant_id and p["salida_id"] == salida_id
        ]

    def fake_list_salud(tenant_id, participante_ids, token):
        return [
            s for pid, s in state["salud"].items() if pid in participante_ids
        ]

    def fake_insert_eventos(rows, token):
        inserted = 0
        for r in rows:
            if r["id"] not in state["eventos"]:
                state["eventos"][r["id"]] = r
                inserted += 1
        return inserted

    def fake_get_salida_by_token_hash(token_hash):
        for r in state["salidas"].values():
            if r["qr_token_hash"] == token_hash:
                return r
        return None

    def fake_get_activity_profile_public(activity_profile_id):
        return state["activities"].get(activity_profile_id)

    def fake_count_participantes_public(salida_id):
        return sum(
            1 for p in state["participantes"].values() if p["salida_id"] == salida_id
        )

    def fake_insert_participante_public(data):
        for p in state["participantes"].values():
            if (
                p["salida_id"] == data["salida_id"]
                and p["document_type"] == data["document_type"]
                and p["document_number"] == data["document_number"]
            ):
                raise _dup_error()
        pid = str(uuid.uuid4())
        row = {"id": pid, "status": "registrado", **data}
        state["participantes"][pid] = row
        return row

    def fake_insert_salud_public(data):
        state["salud"][data["participante_id"]] = data
        return data

    def fake_delete_participante_public(participante_id):
        state["participantes"].pop(participante_id, None)

    for name, fn in {
        "get_activity_profile": fake_get_activity_profile,
        "list_activity_profiles": fake_list_activity_profiles,
        "insert_salida": fake_insert_salida,
        "list_salidas": fake_list_salidas,
        "get_salida": fake_get_salida,
        "update_salida": fake_update_salida,
        "insert_guia": fake_insert_guia,
        "delete_guia": fake_delete_guia,
        "get_profile_for_tenant": fake_get_profile_for_tenant,
        "list_participantes": fake_list_participantes,
        "list_salud": fake_list_salud,
        "insert_eventos": fake_insert_eventos,
        "get_salida_by_token_hash": fake_get_salida_by_token_hash,
        "get_activity_profile_public": fake_get_activity_profile_public,
        "count_participantes_public": fake_count_participantes_public,
        "insert_participante_public": fake_insert_participante_public,
        "insert_salud_public": fake_insert_salud_public,
        "delete_participante_public": fake_delete_participante_public,
    }.items():
        monkeypatch.setattr(repository, name, fn)

    yield TestClient(app)
    app.dependency_overrides.clear()


def _as(role: str, user_id: str = "u1", tenant_id: str = FAKE_TENANT) -> None:
    def _override() -> CurrentUser:
        return CurrentUser(
            user_id=user_id,
            email="staff@test.co",
            tenant_id=tenant_id,
            role=role,
            token="tok",
        )

    app.dependency_overrides[get_current_user] = _override


def _create_salida(client: TestClient, hours_from_now: int = 24, capacity: int = 5) -> dict:
    start = datetime.now(UTC) + timedelta(hours=hours_from_now)
    r = client.post(
        "/salidas",
        json={
            "activity_profile_id": ACTIVITY_ID,
            "route_name": "Ruta vereda El Cañón",
            "scheduled_start": start.isoformat(),
            "capacity": capacity,
        },
    )
    assert r.status_code == 201, r.text
    return r.json()


def _registro_payload(**overrides) -> dict:
    payload = {
        "document_type": "CC",
        "document_number": "1094123456",
        "full_name": "Turista de Prueba",
        "birth_date": "1994-05-20",
        "phone": "3001234567",
        "email": "turista@test.co",
        "emergency_contacts": [
            {"nombre": "Mamá Prueba", "parentesco": "Madre", "telefono": "3017654321"}
        ],
        "eps": "Sura EPS",
        "blood_type": "O+",
        "allergies": "Ninguna",
        "medical_conditions": {},
        "declares_truthful": True,
        "accepts_data_processing": True,
        "received_risk_info": True,
        "declares_sober": True,
    }
    payload.update(overrides)
    return payload


# ---------------------------------------------------------------------------
# Actividades (para que recepción elija al crear salida)
# ---------------------------------------------------------------------------


def test_list_activity_profiles_solo_activas(client):
    _as("recepcionista")
    r = client.get("/activity-profiles")
    assert r.status_code == 200, r.text
    ids = [a["id"] for a in r.json()]
    assert ACTIVITY_ID in ids
    assert INACTIVE_ACTIVITY_ID not in ids


# ---------------------------------------------------------------------------
# Salidas: creación y roles
# ---------------------------------------------------------------------------


def test_create_salida_devuelve_token_en_claro_y_guarda_solo_hash(client, state):
    _as("gerente")
    body = _create_salida(client)
    assert len(body["public_token"]) >= 32
    assert body["public_registration_path"] == f"/registro/{body['public_token']}"
    assert "qr_token_hash" not in body
    row = state["salidas"][body["id"]]
    expected = hashlib.sha256(body["public_token"].encode()).hexdigest()
    assert row["qr_token_hash"] == expected


def test_rol_legado_empresa_equivale_a_gerente(client):
    _as("empresa")
    assert _create_salida(client)["status"] == "programada"


@pytest.mark.parametrize("role", ["recepcionista", "guia"])
def test_roles_sin_permiso_no_crean_salidas(client, role):
    _as(role)
    start = (datetime.now(UTC) + timedelta(hours=24)).isoformat()
    r = client.post(
        "/salidas",
        json={
            "activity_profile_id": ACTIVITY_ID,
            "scheduled_start": start,
            "capacity": 5,
        },
    )
    assert r.status_code == 403


def test_create_salida_actividad_inexistente_o_inactiva(client):
    _as("coordinador")
    start = (datetime.now(UTC) + timedelta(hours=24)).isoformat()
    r = client.post(
        "/salidas",
        json={"activity_profile_id": str(uuid.uuid4()), "scheduled_start": start, "capacity": 5},
    )
    assert r.status_code == 404
    r = client.post(
        "/salidas",
        json={
            "activity_profile_id": INACTIVE_ACTIVITY_ID,
            "scheduled_start": start,
            "capacity": 5,
        },
    )
    assert r.status_code == 422


def test_list_salidas(client):
    _as("gerente")
    _create_salida(client)
    r = client.get("/salidas")
    assert r.status_code == 200
    assert len(r.json()) == 1


# ---------------------------------------------------------------------------
# Transiciones de estado
# ---------------------------------------------------------------------------


def test_transiciones_de_estado(client):
    _as("coordinador")
    salida = _create_salida(client)

    r = client.patch(f"/salidas/{salida['id']}/estado", json={"status": "finalizada"})
    assert r.status_code == 409  # programada no puede saltar a finalizada

    r = client.patch(f"/salidas/{salida['id']}/estado", json={"status": "en_curso"})
    assert r.status_code == 200
    assert r.json()["started_at"] is not None

    r = client.patch(f"/salidas/{salida['id']}/estado", json={"status": "finalizada"})
    assert r.status_code == 200
    assert r.json()["finished_at"] is not None


# ---------------------------------------------------------------------------
# Guías
# ---------------------------------------------------------------------------


def test_asignar_guia_valida_rol_y_duplicados(client):
    _as("gerente")
    salida = _create_salida(client)

    r = client.post(
        f"/salidas/{salida['id']}/guias", json={"guia_user_id": GUIA_ID, "is_lead": True}
    )
    assert r.status_code == 201

    r = client.post(f"/salidas/{salida['id']}/guias", json={"guia_user_id": GUIA_ID})
    assert r.status_code == 409  # ya asignado

    r = client.post(f"/salidas/{salida['id']}/guias", json={"guia_user_id": RECEP_ID})
    assert r.status_code == 422  # no tiene rol guía


# ---------------------------------------------------------------------------
# Registro público del turista
# ---------------------------------------------------------------------------


def test_registro_publico_feliz_sin_alerta_medica(client, state):
    _as("gerente")
    salida = _create_salida(client)
    r = client.post(
        f"/public/salidas/{salida['public_token']}/registro", json=_registro_payload()
    )
    assert r.status_code == 201, r.text
    pid = r.json()["participante_id"]
    assert state["participantes"][pid]["has_medical_alert"] is False
    assert state["salud"][pid]["blood_type"] == "O+"
    # El tenant salió de la salida (derivado del token), nunca del body.
    assert state["participantes"][pid]["tenant_id"] == FAKE_TENANT


def test_registro_publico_enciende_alerta_medica(client, state):
    _as("gerente")
    salida = _create_salida(client)
    r = client.post(
        f"/public/salidas/{salida['public_token']}/registro",
        json=_registro_payload(
            document_number="1094999999",
            allergies="Picadura de abeja (anafilaxia)",
            medical_conditions={"respiratoria": True},
        ),
    )
    assert r.status_code == 201
    assert state["participantes"][r.json()["participante_id"]]["has_medical_alert"] is True


def test_registro_publico_token_invalido(client):
    r = client.post("/public/salidas/token-falso/registro", json=_registro_payload())
    assert r.status_code == 404


def test_registro_publico_expirado(client):
    _as("gerente")
    salida = _create_salida(client, hours_from_now=-72)  # gracia de 24 h ya vencida
    r = client.post(
        f"/public/salidas/{salida['public_token']}/registro", json=_registro_payload()
    )
    assert r.status_code == 410


def test_registro_publico_cupo_lleno_y_duplicado(client):
    _as("gerente")
    salida = _create_salida(client, capacity=1)
    url = f"/public/salidas/{salida['public_token']}/registro"

    assert client.post(url, json=_registro_payload()).status_code == 201
    # mismo documento => 409 por duplicado; documento nuevo => 409 por cupo
    assert client.post(url, json=_registro_payload()).status_code == 409
    assert (
        client.post(url, json=_registro_payload(document_number="52111222")).status_code
        == 409
    )


def test_registro_publico_menor_requiere_acudiente(client):
    _as("gerente")
    salida = _create_salida(client)
    url = f"/public/salidas/{salida['public_token']}/registro"
    birth_minor = (datetime.now(UTC) - timedelta(days=365 * 15)).date().isoformat()

    r = client.post(url, json=_registro_payload(birth_date=birth_minor))
    assert r.status_code == 422

    r = client.post(
        url,
        json=_registro_payload(
            birth_date=birth_minor,
            guardian={
                "nombre": "Acudiente Prueba",
                "documento": "79111222",
                "parentesco": "Padre",
                "telefono": "3109876543",
            },
        ),
    )
    assert r.status_code == 201


def test_registro_publico_valida_edad_de_la_ficha_tecnica(client):
    _as("gerente")
    salida = _create_salida(client)
    r = client.post(
        f"/public/salidas/{salida['public_token']}/registro",
        json=_registro_payload(birth_date="1940-01-01"),  # 86 años > max_age 70
    )
    assert r.status_code == 422


def test_registro_publico_declaraciones_obligatorias(client):
    _as("gerente")
    salida = _create_salida(client)
    r = client.post(
        f"/public/salidas/{salida['public_token']}/registro",
        json=_registro_payload(declares_sober=False),
    )
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Manifiesto y eventos
# ---------------------------------------------------------------------------


def test_manifiesto_incluye_salud_cuando_rls_la_devuelve(client):
    _as("gerente")
    salida = _create_salida(client)
    client.post(
        f"/public/salidas/{salida['public_token']}/registro", json=_registro_payload()
    )
    r = client.get(f"/salidas/{salida['id']}/manifiesto")
    assert r.status_code == 200
    body = r.json()
    assert len(body["participantes"]) == 1
    assert body["participantes"][0]["salud"]["eps"] == "Sura EPS"


def test_sync_eventos_es_idempotente(client):
    _as("guia", user_id=GUIA_ID)
    # la salida la crea un coordinador
    _as("coordinador")
    salida = _create_salida(client)
    _as("guia", user_id=GUIA_ID)

    e1 = str(uuid.uuid4())
    e2 = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()
    payload = {
        "eventos": [
            {"id": e1, "event_type": "inicio_recorrido", "occurred_at": now},
            {"id": e2, "event_type": "novedad", "note": "Lluvia leve", "occurred_at": now},
        ]
    }
    r = client.post(f"/salidas/{salida['id']}/eventos", json=payload)
    assert r.status_code == 200
    assert r.json() == {"received": 2, "inserted": 2}

    # Reintento del sync offline: mismos ids => 0 nuevos.
    r = client.post(f"/salidas/{salida['id']}/eventos", json=payload)
    assert r.json() == {"received": 2, "inserted": 0}


def test_salida_de_otro_tenant_no_existe(client):
    _as("gerente")
    salida = _create_salida(client)
    _as("gerente", tenant_id=OTHER_TENANT)
    r = client.get(f"/salidas/{salida['id']}")
    assert r.status_code == 404
