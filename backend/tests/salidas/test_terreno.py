"""Tests de integración del sprint terreno 1 (router→service, repo mockeado).

Cubren: sync idempotente de revisiones pre/post de equipos, reporte e
investigación de incidentes (pre-llenado, transiciones de estado, edición),
los nuevos tipos de evento (inducción y PON de emergencia) y el campo ARL
del registro público.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.core.security import CurrentUser, get_current_user
from app.main import app
from app.modules.salidas import repository

FAKE_TENANT = "11111111-1111-1111-1111-111111111111"
ACTIVITY_ID = "aaaaaaaa-0000-0000-0000-000000000001"
ITEM_ID = "cccccccc-0000-0000-0000-000000000001"
SALIDA_ID = "dddddddd-0000-0000-0000-000000000001"


@pytest.fixture
def state() -> dict:
    start = datetime.now(UTC) + timedelta(hours=12)
    return {
        "activities": {
            ACTIVITY_ID: {
                "id": ACTIVITY_ID,
                "name": "Tour ATV Salento",
                "is_active": True,
                "min_age": 10,
                "max_age": 70,
            }
        },
        "salidas": {
            SALIDA_ID: {
                "id": SALIDA_ID,
                "tenant_id": FAKE_TENANT,
                "activity_profile_id": ACTIVITY_ID,
                "route_name": "Ruta vereda El Cañón",
                "scheduled_start": start.isoformat(),
                "capacity": 10,
                "status": "programada",
                "qr_token_hash": "x" * 64,
                "qr_token_expires_at": (start + timedelta(hours=24)).isoformat(),
                "started_at": None,
                "finished_at": None,
                "created_at": datetime.now(UTC).isoformat(),
            }
        },
        "checks": {},
        "incidents": {},
        "eventos": {},
    }


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, state: dict):
    def fake_get_salida(tenant_id, salida_id, token):
        r = state["salidas"].get(salida_id)
        return r if r and r["tenant_id"] == tenant_id else None

    def fake_get_activity_profile(tenant_id, activity_profile_id, token):
        return state["activities"].get(activity_profile_id)

    def fake_insert_equipment_checks(rows, token):
        inserted = 0
        for r in rows:
            if r["id"] not in state["checks"]:
                state["checks"][r["id"]] = r
                inserted += 1
        return inserted

    def fake_list_equipment_checks(tenant_id, salida_id, token, phase=None):
        return [
            c
            for c in state["checks"].values()
            if c["tenant_id"] == tenant_id
            and c["salida_id"] == salida_id
            and (phase is None or c["phase"] == phase)
        ]

    def fake_list_general_equipment_checks(tenant_id, token, desde=None, hasta=None):
        return [
            c
            for c in state["checks"].values()
            if c["tenant_id"] == tenant_id
            and c["salida_id"] is None
            and (desde is None or c["checked_at"] >= desde)
            and (hasta is None or c["checked_at"] <= hasta)
        ]

    def fake_insert_incident(tenant_id, data, token):
        iid = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()
        row = {
            "id": iid,
            "tenant_id": tenant_id,
            "status": "borrador",
            "lead_guide_name": None,
            "lead_guide_phone": None,
            "other_staff": [],
            "witnesses": [],
            "environmental_conditions": None,
            "equipment_state": None,
            "probable_causes": None,
            "consequences": None,
            "action_plan": None,
            "info_source": None,
            "risk_was_identified": None,
            "investigators": [],
            "observations": None,
            "created_at": now,
            "updated_at": now,
            **data,
        }
        state["incidents"][iid] = row
        return row

    def fake_get_incident(tenant_id, incident_id, token):
        r = state["incidents"].get(incident_id)
        return r if r and r["tenant_id"] == tenant_id else None

    def fake_list_incidents(tenant_id, token, status=None):
        return [
            r
            for r in state["incidents"].values()
            if r["tenant_id"] == tenant_id and (status is None or r["status"] == status)
        ]

    def fake_update_incident(tenant_id, incident_id, changes, token):
        r = fake_get_incident(tenant_id, incident_id, token)
        if not r:
            return None
        r.update(changes)
        return r

    def fake_insert_eventos(rows, token):
        inserted = 0
        for r in rows:
            if r["id"] not in state["eventos"]:
                state["eventos"][r["id"]] = r
                inserted += 1
        return inserted

    def fake_upload_salida_evidence(tenant_id, salida_id, filename, content, content_type):
        path = f"{tenant_id}/salidas/{salida_id}/{filename}"
        state.setdefault("uploads", {})[path] = content
        return path

    for name, fn in {
        "get_salida": fake_get_salida,
        "get_activity_profile": fake_get_activity_profile,
        "insert_equipment_checks": fake_insert_equipment_checks,
        "list_equipment_checks": fake_list_equipment_checks,
        "list_general_equipment_checks": fake_list_general_equipment_checks,
        "insert_incident": fake_insert_incident,
        "get_incident": fake_get_incident,
        "list_incidents": fake_list_incidents,
        "update_incident": fake_update_incident,
        "insert_eventos": fake_insert_eventos,
        "upload_salida_evidence": fake_upload_salida_evidence,
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


def _check_payload(**overrides) -> dict:
    check = {
        "id": uuid.uuid4().hex,
        "item_id": ITEM_ID,
        "phase": "pre",
        "status": "B",
        "note": "Casco sin fisuras, correas OK",
        "evidence_paths": [f"{FAKE_TENANT}/checks/casco-01.jpg"],
        "checked_at": datetime.now(UTC).isoformat(),
    }
    check.update(overrides)
    return check


def _incident_payload(**overrides) -> dict:
    payload = {
        "occurred_at": datetime.now(UTC).isoformat(),
        "location": "Km 3 vereda El Cañón",
        "circumstances": "Volcamiento leve de ATV en curva con gravilla suelta.",
        "involved_participants": [
            {"nombre": "Turista de Prueba", "telefono": "3001234567"}
        ],
        "emergency_response": "Atención prehospitalaria del guía; sin traslado.",
        "evidence_paths": [f"{FAKE_TENANT}/incidentes/foto-1.jpg"],
    }
    payload.update(overrides)
    return payload


# ---------------------------------------------------------------------------
# Revisión pre/post de equipos
# ---------------------------------------------------------------------------


def test_sync_checks_es_idempotente(client, state):
    _as("coordinador")
    check = _check_payload()
    r1 = client.post(f"/salidas/{SALIDA_ID}/equipos/revisiones", json={"checks": [check]})
    assert r1.status_code == 200, r1.text
    assert r1.json() == {"received": 1, "inserted": 1}

    # Reintento del dispositivo tras perder señal: mismo id, no duplica.
    r2 = client.post(f"/salidas/{SALIDA_ID}/equipos/revisiones", json={"checks": [check]})
    assert r2.json() == {"received": 1, "inserted": 0}
    assert len(state["checks"]) == 1


def test_sync_checks_servidor_impone_autoria_y_salida(client, state):
    _as("guia", user_id="guia-77")
    check = _check_payload(phase="post", status="MC", note="Freno trasero esponjoso")
    r = client.post(f"/salidas/{SALIDA_ID}/equipos/revisiones", json={"checks": [check]})
    assert r.status_code == 200, r.text
    row = state["checks"][check["id"]]
    assert row["checked_by"] == "guia-77"
    assert row["salida_id"] == SALIDA_ID
    assert row["tenant_id"] == FAKE_TENANT


def test_sync_checks_salida_inexistente_404(client):
    _as("coordinador")
    r = client.post(
        f"/salidas/{uuid.uuid4()}/equipos/revisiones",
        json={"checks": [_check_payload()]},
    )
    assert r.status_code == 404


def test_checks_estado_invalido_es_422(client):
    _as("coordinador")
    r = client.post(
        f"/salidas/{SALIDA_ID}/equipos/revisiones",
        json={"checks": [_check_payload(status="X")]},
    )
    assert r.status_code == 422


def test_list_checks_filtra_por_fase(client):
    _as("coordinador")
    client.post(
        f"/salidas/{SALIDA_ID}/equipos/revisiones",
        json={"checks": [_check_payload(phase="pre"), _check_payload(phase="post")]},
    )
    r = client.get(f"/salidas/{SALIDA_ID}/equipos/revisiones", params={"phase": "post"})
    assert r.status_code == 200
    assert [c["phase"] for c in r.json()] == ["post"]


def test_revision_matinal_general_no_requiere_salida(client, state):
    # La operación diaria existe haya o no salidas (retroalimentación Felipe).
    _as("coordinador", user_id="mecanico-1")
    check = _check_payload()
    r = client.post("/equipos/revisiones", json={"checks": [check]})
    assert r.status_code == 200, r.text
    row = state["checks"][check["id"]]
    assert row["salida_id"] is None
    assert row["checked_by"] == "mecanico-1"

    # Reintento idempotente también sin salida.
    r2 = client.post("/equipos/revisiones", json={"checks": [check]})
    assert r2.json() == {"received": 1, "inserted": 0}


def test_list_revisiones_generales_solo_sin_salida(client):
    _as("coordinador")
    client.post("/equipos/revisiones", json={"checks": [_check_payload()]})
    client.post(
        f"/salidas/{SALIDA_ID}/equipos/revisiones", json={"checks": [_check_payload()]}
    )
    r = client.get("/equipos/revisiones")
    assert r.status_code == 200
    assert len(r.json()) == 1  # la de la salida no aparece en las generales


# ---------------------------------------------------------------------------
# Incidentes: reporte e investigación
# ---------------------------------------------------------------------------


def test_create_incident_prellena_actividad_y_autor(client, state):
    _as("guia", user_id="guia-77")
    r = client.post(f"/salidas/{SALIDA_ID}/incidentes", json=_incident_payload())
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] == "borrador"
    assert body["activity_type"] == "Tour ATV Salento"  # del server, no del body
    assert body["reported_by"] == "guia-77"
    assert body["salida_id"] == SALIDA_ID


def test_update_incident_investigacion_y_cierre(client):
    _as("guia", user_id="guia-77")
    iid = client.post(
        f"/salidas/{SALIDA_ID}/incidentes", json=_incident_payload()
    ).json()["id"]

    _as("coordinador")
    r = client.patch(
        f"/incidentes/{iid}",
        json={
            "status": "en_investigacion",
            "probable_causes": "Gravilla suelta no señalizada en la curva 3.",
            "risk_was_identified": True,
            "investigators": [{"nombre": "Coord. Prueba", "cargo": "Coordinador"}],
        },
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "en_investigacion"
    assert r.json()["risk_was_identified"] is True

    r2 = client.patch(
        f"/incidentes/{iid}",
        json={"status": "cerrado", "action_plan": "Señalizar curva; briefing con foto."},
    )
    assert r2.json()["status"] == "cerrado"


def test_incident_cerrado_no_se_reabre(client):
    _as("coordinador")
    iid = client.post(
        f"/salidas/{SALIDA_ID}/incidentes", json=_incident_payload()
    ).json()["id"]
    client.patch(f"/incidentes/{iid}", json={"status": "cerrado"})
    r = client.patch(f"/incidentes/{iid}", json={"status": "en_investigacion"})
    assert r.status_code == 409


def test_update_sin_cambios_es_422(client):
    _as("coordinador")
    iid = client.post(
        f"/salidas/{SALIDA_ID}/incidentes", json=_incident_payload()
    ).json()["id"]
    r = client.patch(f"/incidentes/{iid}", json={})
    assert r.status_code == 422


def test_list_incidents_filtra_por_estado(client):
    _as("coordinador")
    client.post(f"/salidas/{SALIDA_ID}/incidentes", json=_incident_payload())
    iid = client.post(
        f"/salidas/{SALIDA_ID}/incidentes", json=_incident_payload()
    ).json()["id"]
    client.patch(f"/incidentes/{iid}", json={"status": "cerrado"})

    r = client.get("/incidentes", params={"status_filter": "borrador"})
    assert r.status_code == 200
    assert {i["status"] for i in r.json()} == {"borrador"}


def test_incident_inexistente_404(client):
    _as("coordinador")
    assert client.get(f"/incidentes/{uuid.uuid4()}").status_code == 404


# ---------------------------------------------------------------------------
# Nuevos eventos de terreno: inducción y PON de emergencia
# ---------------------------------------------------------------------------


def test_eventos_induccion_y_pon_aceptados(client, state):
    _as("guia", user_id="guia-77")
    eventos = [
        {
            "id": uuid.uuid4().hex,
            "event_type": t,
            "occurred_at": datetime.now(UTC).isoformat(),
            "note": nota,
        }
        for t, nota in [
            ("induccion", "Briefing de riesgos ATV al grupo"),
            ("emergencia_activada", "PON incidente/accidente"),
            ("pon_paso", "Atención prehospitalaria iniciada"),
            ("emergencia_cerrada", "Participante estable, retorno"),
        ]
    ]
    r = client.post(f"/salidas/{SALIDA_ID}/eventos", json={"eventos": eventos})
    assert r.status_code == 200, r.text
    assert r.json() == {"received": 4, "inserted": 4}


def test_subir_evidencia_devuelve_ruta_del_bucket(client, state):
    _as("guia", user_id="guia-77")
    r = client.post(
        f"/salidas/{SALIDA_ID}/evidencias",
        files={"file": ("casco.jpg", b"\xff\xd8\xff" + b"0" * 100, "image/jpeg")},
    )
    assert r.status_code == 201, r.text
    path = r.json()["storage_path"]
    assert path.startswith(f"{FAKE_TENANT}/salidas/{SALIDA_ID}/")
    assert path.endswith("-casco.jpg")
    assert path in state["uploads"]


def test_evidencia_formato_no_permitido_422(client):
    _as("guia")
    r = client.post(
        f"/salidas/{SALIDA_ID}/evidencias",
        files={"file": ("nota.txt", b"hola", "text/plain")},
    )
    assert r.status_code == 422


def test_evento_tipo_invalido_es_422(client):
    _as("guia")
    r = client.post(
        f"/salidas/{SALIDA_ID}/eventos",
        json={
            "eventos": [
                {
                    "id": uuid.uuid4().hex,
                    "event_type": "tipo_inventado",
                    "occurred_at": datetime.now(UTC).isoformat(),
                }
            ]
        },
    )
    assert r.status_code == 422
