"""Tests de integración del módulo de calidad.

Se mockean los bordes externos (Supabase vía repository, IA vía AIProvider);
se ejercita el flujo real del service: documento + reglas de negocio → prompt →
IA → validación Pydantic → persistencia con snapshot → decisión del revisor.
"""

import pytest

from app.modules.quality import repository, service

TENANT_A = "11111111-1111-1111-1111-111111111111"
DOC_ID = "dddddddd-0000-0000-0000-000000000001"
REVIEW_ID = "eeeeeeee-0000-0000-0000-000000000001"

PROMPT_CONTENT = (
    "Evalúa <<DOCUMENT_TITLE>> (numeral <<NUMERAL>>) "
    "tipo <<DOCUMENT_TYPE>> v<<DOCUMENT_VERSION>>.\n"
    "Contenido: <<DOCUMENT_VARIABLES>>\n"
    "Checklist: <<CHECKLIST>>\n"
    "Patrones: <<PATTERNS>>\n"
    "Norma: <<NORM_CONTEXT>>\n"
    "Schema: <<JSON_SCHEMA>>"
)

DOCUMENT = {
    "id": DOC_ID,
    "document_type": "politica_seguridad",
    "version": 3,
    "variables_snapshot": {
        "company_name": "Aventura Andina SAS",
        "scope": None,  # faltante: la evaluación debe reportarlo
        "activities": ["Rafting"],
    },
}

CHECKLIST = [
    {
        "field_key": "company_name",
        "description": "Razón social",
        "required": True,
        "numeral": "5.2",
    },
    {"field_key": "scope", "description": "Alcance", "required": True, "numeral": "5.2"},
]

PATTERNS = [
    {"pattern_type": "rechazo", "description": "Política sin alcance definido", "numeral": "5.2"},
]

EVALUATION = {
    "score": 55.0,
    "completeness": {
        "missing_required_fields": ["scope"],
        "missing_optional_fields": [],
        "comment": "Falta el alcance.",
    },
    "coherence": {"coherent": False, "issues": ["El numeral 5.2 exige un alcance definido."]},
    "alerts": [
        {
            "pattern_type": "rechazo",
            "pattern": "Política sin alcance definido",
            "detail": "El campo scope está vacío.",
        }
    ],
    "observations": ["Completar el alcance antes de presentar a auditoría."],
    "suggested_corrections": [
        {"field": "scope", "issue": "Sin dato", "suggestion": "Definir actividades y sedes."}
    ],
}


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
    """Cablea repository y provider con dobles. Devuelve un dict de captura."""

    captured: dict = {}

    def setup(ai_output: dict, document: dict | None = DOCUMENT):
        provider = FakeProvider(ai_output)
        captured["provider"] = provider
        monkeypatch.setattr(service, "get_ai_provider", lambda: provider)

        monkeypatch.setattr(
            repository, "get_document", lambda doc_id, tid, token: document
        )
        monkeypatch.setattr(
            repository, "get_active_quality_prompt",
            lambda token: {"version": "v1", "content": PROMPT_CONTENT},
        )
        monkeypatch.setattr(repository, "get_checklist", lambda dt, token: CHECKLIST)
        monkeypatch.setattr(
            repository, "get_generation_patterns", lambda dt, token: PATTERNS
        )
        monkeypatch.setattr(
            repository, "match_knowledge_chunks",
            lambda emb, numeral, token, **kw: [
                {"id": "aaaaaaaa-0000-0000-0000-000000000001",
                 "source": "norma", "numeral": "5.2",
                 "content": "La política debe definir el alcance."},
            ],
        )

        def fake_insert(record, token):
            captured["record"] = record
            return {
                "id": REVIEW_ID,
                "review_status": "pending_review",
                "created_at": "2026-07-02T00:00:00+00:00",
                **record,
            }

        monkeypatch.setattr(repository, "insert_review", fake_insert)
        return captured

    return setup


@pytest.fixture
def wire_decision(monkeypatch):
    """Cablea el flujo de decisión del revisor con dobles."""

    captured: dict = {}

    def setup(found: bool = True):
        review = (
            {
                "id": REVIEW_ID,
                "document_id": DOC_ID,
                "review_status": "pending_review",
                "documents": {"document_type": "politica_seguridad", "version": 3},
            }
            if found
            else None
        )
        monkeypatch.setattr(repository, "get_review", lambda rid, tid, token: review)

        def fake_update(rid, tid, fields, token):
            captured["fields"] = fields
            return {**(review or {}), **fields}

        monkeypatch.setattr(repository, "update_review_decision", fake_update)

        def fake_status(tid, dt, st, token):
            captured["status"] = {"document_type": dt, "status": st}

        monkeypatch.setattr(repository, "set_document_status", fake_status)
        return captured

    return setup


def _auth(make_token, role: str = "empresa"):
    token = make_token(tenant_id=TENANT_A, role=role)
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# POST /quality/evaluations/{document_id}
# ---------------------------------------------------------------------------


def test_evaluate_document_persists_snapshot(client, make_token, wire):
    captured = wire(EVALUATION)
    resp = client.post(f"/quality/evaluations/{DOC_ID}", headers=_auth(make_token))

    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["review_id"] == REVIEW_ID
    assert body["document_type"] == "politica_seguridad"
    assert body["document_version"] == 3
    assert body["score"] == 55.0
    assert body["review_status"] == "pending_review"
    assert body["evaluation"]["completeness"]["missing_required_fields"] == ["scope"]
    assert body["evaluation"]["alerts"][0]["pattern"] == "Política sin alcance definido"

    # Snapshot de reproducibilidad completo (regla de oro 6).
    record = captured["record"]
    assert record["tenant_id"] == TENANT_A
    assert record["document_id"] == DOC_ID
    assert record["prompt_version"] == "v1"
    assert record["prompt_hash"]
    assert record["model_version"]

    # El prompt se ensambló con el contenido REAL y las reglas ya existentes.
    prompt = captured["provider"].last_prompt
    assert "Aventura Andina SAS" in prompt                    # variables_snapshot
    assert "Política sin alcance definido" in prompt          # generation_patterns
    assert "scope: Alcance (obligatorio)" in prompt           # extraction_checklist
    assert "La política debe definir el alcance." in prompt   # RAG (norma)
    assert "v3" in prompt                                     # versión del documento


def test_invalid_ai_json_is_502(client, make_token, wire):
    # score debe ser numérico 0-100; un string rompe la validación Pydantic.
    wire({"score": "no-soy-numero"})
    resp = client.post(f"/quality/evaluations/{DOC_ID}", headers=_auth(make_token))
    assert resp.status_code == 502


def test_document_not_found_is_404(client, make_token, wire):
    wire(EVALUATION, document=None)
    resp = client.post(f"/quality/evaluations/{DOC_ID}", headers=_auth(make_token))
    assert resp.status_code == 404


def test_requires_tenant_claim(client, make_token, wire):
    wire(EVALUATION)
    token = make_token(tenant_id=None)  # JWT sin tenant_id
    resp = client.post(
        f"/quality/evaluations/{DOC_ID}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# POST /quality/reviews/{review_id}/decision
# ---------------------------------------------------------------------------


def test_admin_approves_review(client, make_token, wire_decision):
    captured = wire_decision()
    resp = client.post(
        f"/quality/reviews/{REVIEW_ID}/decision",
        json={"decision": "approved", "notes": "Listo para auditoría."},
        headers=_auth(make_token, role="admin"),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["review_status"] == "approved"
    assert body["document_status"] == "approved"
    assert captured["fields"]["review_status"] == "approved"
    assert captured["fields"]["reviewed_by"]
    assert captured["status"] == {
        "document_type": "politica_seguridad",
        "status": "approved",
    }


def test_needs_correction_maps_document_status(client, make_token, wire_decision):
    captured = wire_decision()
    resp = client.post(
        f"/quality/reviews/{REVIEW_ID}/decision",
        json={"decision": "needs_correction", "notes": "Falta el alcance."},
        headers=_auth(make_token, role="admin"),
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["document_status"] == "needs_correction"
    assert captured["status"]["status"] == "needs_correction"


def test_empresa_cannot_decide(client, make_token, wire_decision):
    wire_decision()
    resp = client.post(
        f"/quality/reviews/{REVIEW_ID}/decision",
        json={"decision": "approved"},
        headers=_auth(make_token, role="empresa"),
    )
    assert resp.status_code == 403


def test_unknown_review_is_404(client, make_token, wire_decision):
    wire_decision(found=False)
    resp = client.post(
        f"/quality/reviews/{REVIEW_ID}/decision",
        json={"decision": "approved"},
        headers=_auth(make_token, role="admin"),
    )
    assert resp.status_code == 404


def test_invalid_decision_is_422(client, make_token, wire_decision):
    wire_decision()
    resp = client.post(
        f"/quality/reviews/{REVIEW_ID}/decision",
        json={"decision": "tal_vez"},
        headers=_auth(make_token, role="admin"),
    )
    assert resp.status_code == 422
