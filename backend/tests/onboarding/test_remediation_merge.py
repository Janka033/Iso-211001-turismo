"""Tests unitarios de onboarding.service.apply_remediation.

Verifican las reglas de destino del merge (las mismas del chat): campos
universales arriba (con coerción a lista), field_key de actividad en
``activity_fields`` y el resto en ``remediation_fields`` — sin perder lo que
ya había en ``onboarding_data``.
"""

import pytest

from app.modules.onboarding import repository, service

TENANT_A = "11111111-1111-1111-1111-111111111111"

EXISTING = {
    "activities": ["rafting"],
    "scope": "alcance viejo",
    "activity_fields": {"equipo_rafting": "cascos"},
    "document_codes": {"politica_seguridad": "PO-01"},
}

ACTIVITY_ROWS = [
    {
        "field_key": "equipo_rafting",
        "description": "Equipos",
        "activity": "rafting",
        "required": True,
    },
]


@pytest.fixture
def wire(monkeypatch):
    captured: dict = {}

    monkeypatch.setattr(
        repository, "get_onboarding", lambda tid, token: dict(EXISTING)
    )
    monkeypatch.setattr(
        repository, "get_activity_checklist", lambda acts, token: ACTIVITY_ROWS
    )

    def fake_save(tenant_id, data, token):
        captured["tenant_id"] = tenant_id
        captured["data"] = data
        return data

    monkeypatch.setattr(repository, "save_onboarding", fake_save)
    return captured


async def test_merge_routes_each_key_to_its_home(wire):
    saved = await service.apply_remediation(
        {
            "main_region": "  Antioquia.  ",  # universal escalar
            "organismos_apoyo": "Cruz Roja, Bomberos Cocorná",  # universal lista
            # universal lista
            "safety_objectives": "Reducir incidentes 20%; cero accidentes graves",
            "equipo_rafting": "cascos y remos nuevos",  # Parte B (actividad)
            "legal_commitment": "Cumplir la Ley 300 y el RNT.",  # variable de documento
            "vacio": "   ",  # sin dato: se descarta
        },
        TENANT_A,
        "token",
    )

    assert saved == [
        "equipo_rafting",
        "legal_commitment",
        "main_region",
        "organismos_apoyo",
        "safety_objectives",
    ]
    data = wire["data"]
    assert wire["tenant_id"] == TENANT_A
    assert data["main_region"] == "Antioquia."
    assert data["organismos_apoyo"] == ["Cruz Roja", "Bomberos Cocorná"]
    assert data["safety_objectives"] == [
        "Reducir incidentes 20%",
        "cero accidentes graves",
    ]
    assert data["activity_fields"] == {"equipo_rafting": "cascos y remos nuevos"}
    assert data["remediation_fields"] == {
        "legal_commitment": "Cumplir la Ley 300 y el RNT."
    }
    # Lo que no se tocó, se conserva.
    assert data["activities"] == ["rafting"]
    assert data["document_codes"] == {"politica_seguridad": "PO-01"}


async def test_staff_roles_as_text_does_not_clobber_dict(wire):
    """staff_roles es dict (cargo -> nº); un texto libre va a remediation_fields."""
    await service.apply_remediation(
        {"staff_roles": "un gerente y cinco guías"}, TENANT_A, "token"
    )
    data = wire["data"]
    assert data["remediation_fields"] == {
        "staff_roles": "un gerente y cinco guías"
    }
    # El campo tipado sigue siendo dict (default), no un string.
    assert isinstance(data["staff_roles"], dict)


async def test_all_empty_returns_empty_and_saves_nothing(wire):
    saved = await service.apply_remediation({"main_region": "   "}, TENANT_A, "token")
    assert saved == []
    assert "data" not in wire
