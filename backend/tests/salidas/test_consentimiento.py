"""Tests del flujo de consentimiento informado (texto versionado + firma).

Cubren: lectura pública del texto vigente, firma del adulto y del acudiente
(menor), doble firma, validaciones del trazo PNG, aceptaciones obligatorias,
y el versionado de plantillas por el gerente.
"""

from __future__ import annotations

import base64
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.core.security import CurrentUser, get_current_user
from app.main import app
from app.modules.salidas import repository

FAKE_TENANT = "11111111-1111-1111-1111-111111111111"
ACTIVITY_ID = "aaaaaaaa-0000-0000-0000-000000000001"
SALIDA_ID = "dddddddd-0000-0000-0000-000000000001"
TEMPLATE_ID = "eeeeeeee-0000-0000-0000-000000000001"
PUBLIC_TOKEN = "token-de-prueba-suficientemente-largo-123456"

# PNG mínimo válido (cabecera real de 1x1 px) con relleno para superar el
# mínimo del schema — un trazo real pesa varios KB.
_PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
    "YPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
) + b"\x00" * 256
_PNG_B64 = base64.b64encode(_PNG_BYTES).decode()


def _hash(token: str) -> str:
    import hashlib

    return hashlib.sha256(token.encode()).hexdigest()


@pytest.fixture
def state() -> dict:
    start = datetime.now(UTC) + timedelta(hours=12)
    return {
        "activities": {
            ACTIVITY_ID: {
                "id": ACTIVITY_ID,
                "name": "Tour ATV Salento",
                "min_age": 10,
                "max_age": 70,
                "participant_form_fields": [],
            }
        },
        "salidas": {
            SALIDA_ID: {
                "id": SALIDA_ID,
                "tenant_id": FAKE_TENANT,
                "activity_profile_id": ACTIVITY_ID,
                "scheduled_start": start.isoformat(),
                "capacity": 10,
                "status": "programada",
                "qr_token_hash": _hash(PUBLIC_TOKEN),
                "qr_token_expires_at": (start + timedelta(hours=24)).isoformat(),
            }
        },
        "templates": {
            TEMPLATE_ID: {
                "id": TEMPLATE_ID,
                "tenant_id": FAKE_TENANT,
                "version": 1,
                "body_md": "# CONSENTIMIENTO\n\nTexto de prueba " + "x" * 200,
                "content_hash": "abc123",
                "effective_from": datetime.now(UTC).isoformat(),
            }
        },
        "participantes": {},
        "consentimientos": {},
        "uploads": {},
    }


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, state: dict):
    def fake_get_salida_by_token_hash(token_hash):
        for r in state["salidas"].values():
            if r["qr_token_hash"] == token_hash:
                return r
        return None

    def fake_get_activity_profile_public(activity_profile_id):
        return state["activities"].get(activity_profile_id)

    def fake_get_latest_consent_template_public(tenant_id):
        rows = [
            t for t in state["templates"].values() if t["tenant_id"] == tenant_id
        ]
        return max(rows, key=lambda t: t["version"]) if rows else None

    def fake_get_participante_public(participante_id):
        return state["participantes"].get(participante_id)

    def fake_upload_signature_public(tenant_id, participante_id, content):
        path = f"{tenant_id}/firmas/{participante_id}.png"
        state["uploads"][path] = content
        return path

    def fake_insert_consentimiento_public(data):
        pid = data["participante_id"]
        if any(
            c["participante_id"] == pid for c in state["consentimientos"].values()
        ):
            from postgrest.exceptions import APIError

            raise APIError(
                {"message": "duplicate", "code": "23505", "details": "", "hint": ""}
            )
        cid = str(uuid.uuid4())
        row = {"id": cid, **data}
        state["consentimientos"][cid] = row
        return row

    def fake_update_participante_status_public(participante_id, new_status):
        state["participantes"][participante_id]["status"] = new_status

    def fake_list_consent_templates(tenant_id, token):
        return sorted(
            (t for t in state["templates"].values() if t["tenant_id"] == tenant_id),
            key=lambda t: -t["version"],
        )

    def fake_insert_consent_template(tenant_id, data, token):
        tid = str(uuid.uuid4())
        row = {
            "id": tid,
            "tenant_id": tenant_id,
            "effective_from": datetime.now(UTC).isoformat(),
            **data,
        }
        state["templates"][tid] = row
        return row

    for name, fn in {
        "get_salida_by_token_hash": fake_get_salida_by_token_hash,
        "get_activity_profile_public": fake_get_activity_profile_public,
        "get_latest_consent_template_public": fake_get_latest_consent_template_public,
        "get_participante_public": fake_get_participante_public,
        "upload_signature_public": fake_upload_signature_public,
        "insert_consentimiento_public": fake_insert_consentimiento_public,
        "update_participante_status_public": fake_update_participante_status_public,
        "list_consent_templates": fake_list_consent_templates,
        "insert_consent_template": fake_insert_consent_template,
    }.items():
        monkeypatch.setattr(repository, name, fn)

    yield TestClient(app)
    app.dependency_overrides.clear()


def _participante(state: dict, birth_date: str = "1994-05-20", guardian=None) -> str:
    pid = str(uuid.uuid4())
    state["participantes"][pid] = {
        "id": pid,
        "tenant_id": FAKE_TENANT,
        "salida_id": SALIDA_ID,
        "full_name": "Turista de Prueba",
        "document_type": "CC",
        "document_number": "1094123456",
        "birth_date": birth_date,
        "guardian": guardian,
        "status": "registrado",
    }
    return pid


def _firma_payload(pid: str, **overrides) -> dict:
    payload = {
        "participante_id": pid,
        "accepted_privacy": True,
        "accepted_risk_info": True,
        "signature_png_base64": _PNG_B64,
    }
    payload.update(overrides)
    return payload


def _as(role: str) -> None:
    def _override() -> CurrentUser:
        return CurrentUser(
            user_id="u1", email="s@t.co", tenant_id=FAKE_TENANT, role=role, token="tok"
        )

    app.dependency_overrides[get_current_user] = _override


# ---------------------------------------------------------------------------
# Lectura pública del texto
# ---------------------------------------------------------------------------


def test_turista_lee_el_texto_vigente(client):
    r = client.get(f"/public/salidas/{PUBLIC_TOKEN}/consentimiento")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["template_version"] == 1
    assert body["activity_name"] == "Tour ATV Salento"
    assert "CONSENTIMIENTO" in body["body_md"]


def test_token_invalido_404(client):
    assert client.get("/public/salidas/token-malo/consentimiento").status_code == 404


def test_sin_plantilla_publicada_409(client, state):
    state["templates"].clear()
    r = client.get(f"/public/salidas/{PUBLIC_TOKEN}/consentimiento")
    assert r.status_code == 409


# ---------------------------------------------------------------------------
# Firma
# ---------------------------------------------------------------------------


def test_firma_adulto_feliz(client, state):
    pid = _participante(state)
    r = client.post(
        f"/public/salidas/{PUBLIC_TOKEN}/consentimientos", json=_firma_payload(pid)
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["signed_by_guardian"] is False
    assert body["participante_status"] == "firmado"
    assert state["participantes"][pid]["status"] == "firmado"
    # El trazo quedó en el bucket y la fila amarra al firmante.
    row = next(iter(state["consentimientos"].values()))
    assert row["signature_path"] == f"{FAKE_TENANT}/firmas/{pid}.png"
    assert row["signer_document"] == "1094123456"
    assert row["tenant_id"] == FAKE_TENANT  # derivado del token, no del body


def test_menor_firma_su_acudiente(client, state):
    hoy = datetime.now(UTC).date()
    nacimiento_menor = hoy.replace(year=hoy.year - 12).isoformat()
    pid = _participante(
        state,
        birth_date=nacimiento_menor,
        guardian={
            "nombre": "Acudiente Prueba",
            "documento": "52123456",
            "parentesco": "Madre",
            "telefono": "3010000000",
        },
    )
    r = client.post(
        f"/public/salidas/{PUBLIC_TOKEN}/consentimientos", json=_firma_payload(pid)
    )
    assert r.status_code == 201, r.text
    assert r.json()["signed_by_guardian"] is True
    row = next(iter(state["consentimientos"].values()))
    assert row["signer_name"] == "Acudiente Prueba"
    assert row["signer_document"] == "52123456"


def test_doble_firma_409(client, state):
    pid = _participante(state)
    url = f"/public/salidas/{PUBLIC_TOKEN}/consentimientos"
    assert client.post(url, json=_firma_payload(pid)).status_code == 201
    assert client.post(url, json=_firma_payload(pid)).status_code == 409


def test_firma_de_participante_de_otra_salida_404(client, state):
    pid = _participante(state)
    state["participantes"][pid]["salida_id"] = str(uuid.uuid4())
    r = client.post(
        f"/public/salidas/{PUBLIC_TOKEN}/consentimientos", json=_firma_payload(pid)
    )
    assert r.status_code == 404


def test_firma_no_png_422(client, state):
    pid = _participante(state)
    jpeg_b64 = base64.b64encode(b"\xff\xd8\xff" + b"0" * 200).decode()
    r = client.post(
        f"/public/salidas/{PUBLIC_TOKEN}/consentimientos",
        json=_firma_payload(pid, signature_png_base64=jpeg_b64),
    )
    assert r.status_code == 422


def test_aceptaciones_obligatorias_422(client, state):
    pid = _participante(state)
    r = client.post(
        f"/public/salidas/{PUBLIC_TOKEN}/consentimientos",
        json=_firma_payload(pid, accepted_privacy=False),
    )
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Plantillas (staff)
# ---------------------------------------------------------------------------


def test_gerente_publica_nueva_version(client):
    _as("gerente")
    r = client.post(
        "/consent-templates",
        json={"body_md": "# CONSENTIMIENTO v2\n\n" + "Texto nuevo. " * 30},
    )
    assert r.status_code == 201, r.text
    assert r.json()["version"] == 2  # siguiente a la v1 sembrada

    listado = client.get("/consent-templates").json()
    assert [t["version"] for t in listado] == [2, 1]


def test_guia_no_publica_plantillas(client):
    _as("guia")
    r = client.post(
        "/consent-templates",
        json={"body_md": "# Intento\n\n" + "Texto. " * 50},
    )
    assert r.status_code == 403


def test_rol_legado_empresa_publica(client):
    _as("empresa")
    r = client.post(
        "/consent-templates",
        json={"body_md": "# CONSENTIMIENTO propio\n\n" + "Texto propio. " * 30},
    )
    assert r.status_code == 201
