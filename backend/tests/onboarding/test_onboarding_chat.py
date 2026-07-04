"""Tests de integración del onboarding conversacional (POST /onboarding/chat).

Herméticos: se mockean los bordes (Supabase vía repository, IA vía AIProvider).
Se ejercita el flujo real del service: checklist (universal + por actividad) →
IA extrae → merge → completitud dinámica → el BACKEND decide la próxima pregunta.
"""

import pytest

from app.modules.onboarding import repository, service

TENANT_A = "11111111-1111-1111-1111-111111111111"

_CATS = ("equipo", "competencias", "emergencias", "riesgos", "seguimiento")


def _checklist_for(activities: list[str]) -> list[dict]:
    """Simula la Parte B: 5 categorías por actividad elegida."""
    rows: list[dict] = []
    for act in activities:
        for cat in _CATS:
            rows.append(
                {"field_key": f"{cat}_{act}", "description": f"{cat} de {act}", "activity": act}
            )
    return rows


class FakeProvider:
    def __init__(self, output: dict):
        self._output = output

    async def embed(self, text: str) -> list[float]:
        return [0.0] * 768

    async def generate_json(self, prompt: str) -> dict:
        self.last_prompt = prompt
        return self._output


@pytest.fixture
def wire(monkeypatch):
    """Cablea repository + provider con dobles. Devuelve captura + estado guardado."""

    captured: dict = {}

    def setup(ai_output: dict | None = None, stored: dict | None = None):
        state = {"data": dict(stored or {})}
        captured["state"] = state

        if ai_output is not None:
            provider = FakeProvider(ai_output)
            captured["provider"] = provider
            monkeypatch.setattr(service, "get_ai_provider", lambda: provider)

        monkeypatch.setattr(
            repository, "get_onboarding", lambda tid, token: dict(state["data"])
        )
        monkeypatch.setattr(
            repository,
            "get_activity_checklist",
            lambda activities, token: _checklist_for(activities),
        )
        monkeypatch.setattr(
            repository,
            "get_active_onboarding_prompt",
            lambda token: {"version": "v1", "content": "PENDIENTES: <<PENDING_FIELDS>>"},
        )
        monkeypatch.setattr(
            repository, "match_knowledge_chunks", lambda emb, numeral, token: []
        )

        def fake_save(tid, data, token):
            state["data"] = data
            return data

        monkeypatch.setattr(repository, "save_onboarding", fake_save)
        return captured

    return setup


def _auth(make_token, tenant_id: str | None = TENANT_A):
    token = make_token(tenant_id=tenant_id)
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Primer turno: sin mensaje, el backend hace la primera pregunta (universal).
# ---------------------------------------------------------------------------


def test_first_turn_sets_activities_and_asks_first_universal(client, make_token, wire):
    wire(ai_output={})  # no se usa la IA en el primer turno (sin message)
    resp = client.post(
        "/onboarding/chat",
        json={"activities": ["rafting", "parapente", "buceo"], "message": None},
        headers=_auth(make_token),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    # 13 universales + 5*3 por actividad = 28 esperados; solo `activities` con dato.
    assert body["completeness"] == round(1 / 28 * 100, 2)
    assert body["completed"] is False
    assert body["next_field"]["field_key"] == "main_region"
    assert body["data"]["activities"] == ["rafting", "parapente", "buceo"]
    assert body["extracted"] == {}


# ---------------------------------------------------------------------------
# Turno con respuesta: la IA extrae varios campos; el backend avanza.
# ---------------------------------------------------------------------------


def test_extracts_multiple_universal_fields(client, make_token, wire):
    wire(
        ai_output={
            "extracted": {
                "main_region": "Santander",
                "locations": "río Suárez",
                "certified_guides": "8",
            },
            "next_field_key": "scope",
            "next_question": "¿Cuál es el alcance de su operación?",
            "completed": False,
        },
        stored={"activities": ["rafting"]},
    )
    resp = client.post(
        "/onboarding/chat",
        json={"message": "Operamos en Santander, en el río Suárez, con 8 guías."},
        headers=_auth(make_token),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["data"]["main_region"] == "Santander"
    assert body["data"]["locations"] == ["río Suárez"]  # campo de lista
    assert body["data"]["certified_guides"] == "8"
    assert body["extracted"]["main_region"] == "Santander"
    # La pregunta de la IA se usa porque coincide con el campo que eligió el backend.
    assert body["next_field"]["field_key"] == "scope"
    assert body["next_question"] == "¿Cuál es el alcance de su operación?"


def test_activity_field_goes_into_activity_fields(client, make_token, wire):
    wire(
        ai_output={
            "extracted": {"equipo_rafting": "Balsa, remos, chalecos, cascos"},
            "next_field_key": "competencias_rafting",
            "next_question": "¿Qué certificaciones tienen sus guías de rafting?",
            "completed": False,
        },
        stored={"activities": ["rafting"], "main_region": "Santander"},
    )
    resp = client.post(
        "/onboarding/chat",
        json={"message": "Tenemos balsas, remos, chalecos y cascos."},
        headers=_auth(make_token),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["data"]["activity_fields"]["equipo_rafting"] == "Balsa, remos, chalecos, cascos"


def test_staff_roles_captured_as_dict(client, make_token, wire):
    # El organigrama llega por el campo dedicado staff_roles (dict), no por el
    # mapa `extracted` de strings. Alimenta MA-02.
    wire(
        ai_output={
            "extracted": {},
            "staff_roles": {"gerente": "1", "coordinador": "2", "guia": "6"},
            "next_field_key": "legal_representative",
            "next_question": "¿Quién es el representante legal?",
            "completed": False,
        },
        stored={"activities": ["rafting"], "certified_guides": "6"},
    )
    resp = client.post(
        "/onboarding/chat",
        json={"message": "Somos un gerente, dos coordinadores y seis guías."},
        headers=_auth(make_token),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["data"]["staff_roles"] == {"gerente": "1", "coordinador": "2", "guia": "6"}


def test_invented_keys_are_dropped(client, make_token, wire):
    wire(
        ai_output={
            "extracted": {"main_region": "Meta", "campo_inventado": "x", "equipo_kayak": "y"},
            "next_field_key": "scope",
            "next_question": "¿Alcance?",
            "completed": False,
        },
        stored={"activities": ["rafting"]},  # kayak NO fue elegida
    )
    resp = client.post(
        "/onboarding/chat",
        json={"message": "Estamos en el Meta."},
        headers=_auth(make_token),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["data"]["main_region"] == "Meta"
    assert "campo_inventado" not in body["extracted"]
    # equipo_kayak no aplica (kayak no elegida) => descartado.
    assert "equipo_kayak" not in (body["data"].get("activity_fields") or {})


def test_backend_overrides_ai_next_field(client, make_token, wire):
    # La IA no extrae nada y propone 'nit', pero el primer pendiente real es
    # 'main_region' => manda el backend (pregunta de fallback).
    wire(
        ai_output={
            "extracted": {},
            "next_field_key": "nit",
            "next_question": "¿Cuál es el NIT?",
            "completed": True,
        },
        stored={"activities": ["rafting"]},
    )
    resp = client.post(
        "/onboarding/chat",
        json={"message": "No estoy seguro."},
        headers=_auth(make_token),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["next_field"]["field_key"] == "main_region"
    assert body["next_question"] != "¿Cuál es el NIT?"
    assert body["completed"] is False  # el backend reconfirma, no confía en la IA


def test_invalid_ai_json_is_502(client, make_token, wire):
    wire(ai_output={"extracted": "no-soy-un-dict"}, stored={"activities": ["rafting"]})
    resp = client.post(
        "/onboarding/chat",
        json={"message": "hola"},
        headers=_auth(make_token),
    )
    assert resp.status_code == 502


def test_requires_tenant_claim(client, make_token, wire):
    wire(ai_output={})
    resp = client.post(
        "/onboarding/chat",
        json={"activities": ["rafting"], "message": None},
        headers=_auth(make_token, tenant_id=None),
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# FASE 4 — escenario "empresa con 3 actividades distintas" (determinista,
# sin IA): el flujo debe generar preguntas específicas de CADA actividad y el
# universo de campos esperados debe superar los 5.
# ---------------------------------------------------------------------------

_ALL_UNIVERSAL = {
    "activities": ["rafting", "parapente", "buceo"],
    "main_region": "Santander",
    "locations": ["río Suárez"],
    "scope": "Rafting y parapente en Santander",
    "certified_guides": "8",
    "staff_roles": {"gerente": "1", "guia": "5"},
    "legal_representative": "María Gómez",
    "nit": "900123456-7",
    "rnt_status": "Vigente",
    "rnt_number": "12345",
    "emergency_contacts": ["Bomberos 119"],
    "existing_controls": "Chequeo de equipo",
    "management_commitment": "La dirección prioriza la seguridad",
}


def test_three_activities_produce_activity_specific_pending():
    activities = ["rafting", "parapente", "buceo"]
    checklist = _checklist_for(activities)
    # Todos los universales ya respondidos => los pendientes son SOLO por actividad.
    pending = service._pending_fields(_ALL_UNIVERSAL, checklist)

    assert len(pending) == 15  # 5 categorías × 3 actividades
    assert all(p["activity"] in activities for p in pending)
    # Cubre las 3 actividades y arranca por una pregunta específica de actividad.
    assert {p["activity"] for p in pending} == set(activities)
    assert pending[0]["activity"] is not None


def test_three_activities_expected_fields_exceed_five():
    activities = ["rafting", "parapente", "buceo"]
    checklist = _checklist_for(activities)
    pct, completed = service._measure_dynamic(_ALL_UNIVERSAL, checklist)

    # 13 universales + 15 por actividad = 28 esperados (mucho más que 5).
    # Con 13 respondidos: 13/28.
    assert pct == round(13 / 28 * 100, 2)
    assert completed is False


def test_full_capture_completes():
    activities = ["rafting"]
    checklist = _checklist_for(activities)
    data = dict(_ALL_UNIVERSAL)
    data["activities"] = activities
    data["activity_fields"] = {row["field_key"]: "ok" for row in checklist}

    pending = service._pending_fields(data, checklist)
    pct, completed = service._measure_dynamic(data, checklist)
    assert pending == []
    assert pct == 100.0
    assert completed is True
