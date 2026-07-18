"""Tests de GET /onboarding/roadmap (Fase 1 de la ruta guiada).

Herméticos: se mockea el repository. Se verifica el orden, la derivación del
estado por tenant (document_status + score de calidad más reciente) y el
cálculo del paso actual.
"""

import pytest

from app.modules.onboarding import repository

TENANT_A = "11111111-1111-1111-1111-111111111111"

_ROADMAP_ROWS = [
    {
        "step_order": 1,
        "document_type": "alcance_sgsta",
        "title": "Alcance del SGSTA",
        "numeral": "4.3",
        "generator_ready": False,
    },
    {
        "step_order": 4,
        "document_type": "politica_seguridad",
        "title": "Política de seguridad",
        "numeral": "5.2",
        "generator_ready": True,
    },
    {
        "step_order": 7,
        "document_type": "matriz_riesgos",
        "title": "Matriz de riesgos y oportunidades",
        "numeral": "6.1.1",
        "generator_ready": True,
    },
]


@pytest.fixture
def wire_roadmap(monkeypatch):
    def setup(statuses: list[dict] | None = None, reviews: list[dict] | None = None):
        monkeypatch.setattr(repository, "get_roadmap", lambda token: list(_ROADMAP_ROWS))
        monkeypatch.setattr(
            repository, "get_document_statuses", lambda tid, token: list(statuses or [])
        )
        monkeypatch.setattr(
            repository,
            "get_latest_review_scores",
            lambda tid, token: list(reviews or []),
        )

    return setup


def _auth(make_token, tenant_id: str | None = TENANT_A):
    return {"Authorization": f"Bearer {make_token(tenant_id=tenant_id)}"}


def test_roadmap_all_pending(client, make_token, wire_roadmap):
    wire_roadmap()
    resp = client.get("/onboarding/roadmap", headers=_auth(make_token))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 3
    # El actual es el primero sin documento CUYO GENERADOR EXISTE: el paso 1
    # (generator_ready=false, "próximamente") se salta — el chat tampoco lo
    # pregunta y el mapa quedaría sin nodo accionable.
    assert body["current_step"] == 4
    assert [s["step_order"] for s in body["steps"]] == [1, 4, 7]
    assert all(s["status"] == "pendiente" for s in body["steps"])
    assert all(s["last_score"] is None for s in body["steps"])


def test_roadmap_merges_status_and_latest_score(client, make_token, wire_roadmap):
    wire_roadmap(
        statuses=[
            {"document_type": "politica_seguridad", "status": "generated", "completeness": 100.0}
        ],
        # Dos reviews de la política: gana la más reciente (vienen desc).
        reviews=[
            {
                "score": 85,
                "created_at": "2026-07-17",
                "documents": {"document_type": "politica_seguridad"},
            },
            {
                "score": 60,
                "created_at": "2026-07-10",
                "documents": {"document_type": "politica_seguridad"},
            },
        ],
    )
    resp = client.get("/onboarding/roadmap", headers=_auth(make_token))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    by_type = {s["document_type"]: s for s in body["steps"]}
    politica = by_type["politica_seguridad"]
    assert politica["status"] == "generated"
    assert politica["completeness"] == 100.0
    assert politica["last_score"] == 85.0
    # El paso 4 tiene documento y el 1 no tiene generador: el actual es el 7.
    assert body["current_step"] == 7
    assert by_type["matriz_riesgos"]["status"] == "pendiente"


def test_roadmap_current_step_advances_past_generated(client, make_token, wire_roadmap):
    wire_roadmap(
        statuses=[
            {"document_type": "alcance_sgsta", "status": "generated", "completeness": 90.0},
            {"document_type": "politica_seguridad", "status": "approved", "completeness": 100.0},
        ]
    )
    resp = client.get("/onboarding/roadmap", headers=_auth(make_token))
    body = resp.json()
    assert body["current_step"] == 7  # los pasos 1 y 4 ya tienen documento


def test_roadmap_requires_auth(client):
    assert client.get("/onboarding/roadmap").status_code in (401, 403)
