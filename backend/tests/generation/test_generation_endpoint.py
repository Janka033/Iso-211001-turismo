"""Tests de integración del endpoint de generación.

Se mockean los bordes externos (Supabase vía repository, IA vía AIProvider);
se ejercita el flujo real del service: RAG → prompt → validación Pydantic →
generador → snapshot.
"""

import pytest

from app.modules.generation import repository, service

TENANT_A = "11111111-1111-1111-1111-111111111111"

PROMPT_CONTENT = (
    "Extrae las variables.\n"
    "Empresa: <<COMPANY_CONTEXT>>\n"
    "Norma: <<NORM_CONTEXT>>\n"
    "Checklist: <<CHECKLIST>>\n"
    "Patrones: <<PATTERNS>>\n"
    "Schema: <<JSON_SCHEMA>>"
)

CHECKLIST = [
    {"field_key": "company_name", "description": "Razón social", "required": True},
    {"field_key": "scope", "description": "Alcance", "required": True},
    {"field_key": "activities", "description": "Actividades", "required": True},
    {"field_key": "management_commitment", "description": "Compromiso", "required": True},
    {"field_key": "safety_objectives", "description": "Objetivos", "required": True},
    {"field_key": "legal_commitment", "description": "Legal", "required": True},
    {"field_key": "continuous_improvement", "description": "Mejora", "required": True},
    {"field_key": "nit", "description": "NIT", "required": False},
]

FULL_OUTPUT = {
    "company_name": "Aventura Andina SAS",
    "nit": "900.123.456-7",
    "scope": "Rafting y canopy en Santander.",
    "activities": ["Rafting", "Canopy"],
    "management_commitment": "La dirección se compromete con la seguridad.",
    "safety_objectives": ["Cero accidentes graves"],
    "legal_commitment": "Cumplir la normativa de turismo.",
    "continuous_improvement": "Revisión semestral.",
    "communication": "Publicada en la sede.",
    "legal_representative": "María Gómez",
    "approval_date": "2026-06-18",
}


class FakeProvider:
    def __init__(self, output: dict):
        self._output = output

    async def embed(self, text: str) -> list[float]:
        return [0.0] * 768

    async def generate_json(self, prompt: str) -> dict:
        # Guardamos el prompt para inspección si hiciera falta.
        self.last_prompt = prompt
        return self._output


@pytest.fixture
def wire(monkeypatch):
    """Cablea el repository y el provider con dobles. Devuelve un dict de captura."""

    captured: dict = {}

    def setup(ai_output: dict):
        provider = FakeProvider(ai_output)
        monkeypatch.setattr(service, "get_ai_provider", lambda: provider)

        monkeypatch.setattr(
            repository, "get_active_prompt",
            lambda dt, token: {"version": "v1", "content": PROMPT_CONTENT},
        )
        monkeypatch.setattr(
            repository, "get_company",
            lambda tid, token: {"name": "Aventura Andina SAS", "nit": "900.123.456-7"},
        )
        monkeypatch.setattr(
            repository, "get_onboarding_data",
            lambda tid, token: {"actividades": ["rafting"]},
        )
        monkeypatch.setattr(repository, "get_checklist", lambda dt, token: CHECKLIST)
        monkeypatch.setattr(repository, "get_generation_patterns", lambda dt, token: [])
        monkeypatch.setattr(
            repository, "match_knowledge_chunks",
            lambda emb, numeral, token, **kw: [
                {"id": "aaaaaaaa-0000-0000-0000-000000000001",
                 "source": "norma", "numeral": "5.2", "content": "La política..."},
            ],
        )
        monkeypatch.setattr(repository, "next_version", lambda tid, dt, token: 1)
        monkeypatch.setattr(
            repository, "upload_document",
            lambda tid, dt, v, content, token, engine="docx": f"{tid}/{dt}/v{v}.{engine}",
        )

        def fake_insert(record, token):
            captured["record"] = record
            return {"id": "doc-0001", **record}

        monkeypatch.setattr(repository, "insert_document", fake_insert)

        def fake_status(tid, dt, st, comp, token):
            captured["status"] = {"status": st, "completeness": comp}

        monkeypatch.setattr(repository, "upsert_document_status", fake_status)
        return captured

    return setup


def _auth(make_token):
    token = make_token(tenant_id=TENANT_A, role="empresa")
    return {"Authorization": f"Bearer {token}"}


def test_generate_full_document(client, make_token, wire):
    captured = wire(FULL_OUTPUT)
    resp = client.post("/generation/politica_seguridad", headers=_auth(make_token))

    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["document_id"] == "doc-0001"
    assert body["version"] == 1
    assert body["status"] == "generated"
    assert body["completeness"] == 100.0
    assert body["pending_fields"] == []
    assert body["storage_path"].endswith("v1.docx")

    # Snapshot de reproducibilidad completo.
    record = captured["record"]
    assert record["prompt_version"] == "v1"
    assert record["template_version"] == "politica-seguridad-docx-v1"
    assert record["prompt_hash"]
    assert record["rag_chunks_ids"] == ["aaaaaaaa-0000-0000-0000-000000000001"]
    assert record["variables_snapshot"]["company_name"] == "Aventura Andina SAS"


def test_generate_partial_marks_pending(client, make_token, wire):
    wire({"company_name": "Sin Datos SAS"})  # faltan los obligatorios
    resp = client.post("/generation/politica_seguridad", headers=_auth(make_token))

    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert "scope" in body["pending_fields"]
    assert "activities" in body["pending_fields"]
    assert body["completeness"] < 100.0


def test_invalid_ai_json_is_502(client, make_token, wire):
    # activities debe ser lista; un str rompe la validación Pydantic.
    wire({"company_name": "X", "activities": "no-soy-lista"})
    resp = client.post("/generation/politica_seguridad", headers=_auth(make_token))
    assert resp.status_code == 502


def test_unknown_document_type_is_404(client, make_token, wire):
    wire(FULL_OUTPUT)
    resp = client.post("/generation/documento_inexistente", headers=_auth(make_token))
    assert resp.status_code == 404


def test_requires_tenant_claim(client, make_token, wire):
    wire(FULL_OUTPUT)
    token = make_token(tenant_id=None)  # JWT sin tenant_id
    resp = client.post(
        "/generation/politica_seguridad",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 401


def test_list_document_types(client, make_token):
    resp = client.get("/generation/document-types", headers=_auth(make_token))
    assert resp.status_code == 200
    assert "politica_seguridad" in resp.json()
