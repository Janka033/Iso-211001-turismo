"""Tests del veredicto de preparación documental (GET /quality/readiness).

Herméticos: se mockea onboarding_service.get_roadmap (la fuente del estado por
tenant). Se verifica la agregación: bloqueadores, conteo y veredicto.
"""

import pytest

from app.modules.onboarding import service as onboarding_service
from app.modules.onboarding.schemas import RoadmapResponse, RoadmapStep

TENANT_A = "11111111-1111-1111-1111-111111111111"


def _auth(make_token):
    return {"Authorization": f"Bearer {make_token(tenant_id=TENANT_A)}"}


def _step(
    order, dtype, *, status="pendiente", completeness=None, score=None, generator_ready=True
):
    return RoadmapStep(
        step_order=order,
        document_type=dtype,
        title=f"Documento {dtype}",
        numeral="4.3",
        generator_ready=generator_ready,
        status=status,
        completeness=completeness,
        last_score=score,
    )


@pytest.fixture
def wire_roadmap(monkeypatch):
    def setup(steps):
        async def fake(tid, token):
            return RoadmapResponse(steps=steps, current_step=None, total=len(steps))

        monkeypatch.setattr(onboarding_service, "get_roadmap", fake)

    return setup


def test_not_ready_lists_each_blocker(client, make_token, wire_roadmap):
    wire_roadmap(
        [
            _step(1, "alcance", status="generated", completeness=100.0, score=85),
            _step(2, "partes", status="pendiente"),  # falta generar
            _step(4, "politica", status="generated", completeness=100.0, score=65),
        ]
    )
    resp = client.get("/quality/readiness", headers=_auth(make_token))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["ready"] is False
    assert body["ready_count"] == 1
    assert body["total"] == 3
    assert len(body["blockers"]) == 2
    assert any("partes" in b for b in body["blockers"])
    assert any("65" in b for b in body["blockers"])  # score bajo aparece


def test_ready_when_all_pass_threshold(client, make_token, wire_roadmap):
    wire_roadmap(
        [
            _step(1, "a", status="generated", completeness=100.0, score=85),
            _step(2, "b", status="approved", completeness=100.0),  # aprobado por revisor
        ]
    )
    body = client.get("/quality/readiness", headers=_auth(make_token)).json()
    assert body["ready"] is True
    assert body["blockers"] == []
    assert "listo para presentar" in body["summary"].lower()


def test_states_incomplete_unevaluated_and_correction(client, make_token, wire_roadmap):
    wire_roadmap(
        [
            _step(1, "a", status="generated", completeness=80.0, score=90),  # [PENDIENTE]
            _step(2, "b", status="generated", completeness=100.0),  # sin evaluar
            _step(3, "c", status="needs_correction", completeness=100.0, score=70),
        ]
    )
    body = client.get("/quality/readiness", headers=_auth(make_token)).json()
    states = {i["document_type"]: i["state"] for i in body["items"]}
    assert states["a"] == "incomplete"
    assert states["b"] == "unevaluated"
    assert states["c"] == "below_threshold"
    assert body["ready"] is False


def test_coming_soon_step_does_not_block(client, make_token, wire_roadmap):
    """Un documento 'próximamente' (sin generador aún) no cuenta ni bloquea:
    el veredicto solo agrega lo que el cliente puede preparar hoy."""
    wire_roadmap(
        [
            _step(1, "a", status="approved", completeness=100.0),
            _step(2, "futuro", status="pendiente", generator_ready=False),
        ]
    )
    body = client.get("/quality/readiness", headers=_auth(make_token)).json()
    assert body["total"] == 1
    assert body["ready"] is True
    assert body["blockers"] == []
    assert all(i["document_type"] != "futuro" for i in body["items"])


def test_readiness_requires_auth(client):
    assert client.get("/quality/readiness").status_code in (401, 403)
