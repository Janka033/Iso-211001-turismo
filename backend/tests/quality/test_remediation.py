"""Tests de integración del flujo de subsanación (POST /quality/reviews/{id}/remediation).

Se mockean los bordes: repository de quality y los SERVICES de onboarding y
generation (la frontera correcta entre módulos). Se ejercita el service real:
review → validación de estado y claves → merge en onboarding → regeneración.
"""

import pytest

from app.modules.generation.schemas import GeneratedDocument
from app.modules.quality import repository, service

TENANT_A = "11111111-1111-1111-1111-111111111111"
DOC_ID = "dddddddd-0000-0000-0000-000000000001"
REVIEW_ID = "eeeeeeee-0000-0000-0000-000000000001"

EVALUATION = {
    "score": 55.0,
    "completeness": {
        "missing_required_fields": ["scope"],
        "missing_optional_fields": ["nit"],
        "comment": "Falta el alcance.",
    },
    "coherence": {"coherent": False, "issues": ["El numeral 5.2 exige un alcance."]},
    "alerts": [],
    "observations": [],
    "suggested_corrections": [
        {"field": "safety_objectives", "issue": "Objetivo no medible", "suggestion": None}
    ],
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

REGENERATED = GeneratedDocument(
    document_id="dddddddd-0000-0000-0000-000000000002",
    document_type="politica_seguridad",
    version=4,
    status="generated",
    storage_path="t/politica_seguridad/v4.docx",
    completeness=100.0,
    pending_fields=[],
    prompt_version="v1",
    template_version="v3",
)


@pytest.fixture
def wire_remediation(monkeypatch):
    """Cablea review + checklist + services de onboarding/generation con dobles."""

    captured: dict = {}

    def setup(
        review_status: str = "needs_correction",
        found: bool = True,
    ):
        review = (
            {
                "id": REVIEW_ID,
                "document_id": DOC_ID,
                "review_status": review_status,
                "evaluation": EVALUATION,
                "documents": {"document_type": "politica_seguridad", "version": 3},
            }
            if found
            else None
        )
        monkeypatch.setattr(repository, "get_review", lambda rid, tid, token: review)
        monkeypatch.setattr(repository, "get_checklist", lambda dt, token: CHECKLIST)

        async def fake_apply(answers, tenant_id, token):
            captured["answers"] = answers
            captured["merge_tenant"] = tenant_id
            return sorted(k for k, v in answers.items() if v.strip())

        monkeypatch.setattr(
            service.onboarding_service, "apply_remediation", fake_apply
        )

        async def fake_generate(document_type, tenant_id, token, payload):
            captured["generated"] = {
                "document_type": document_type,
                "tenant_id": tenant_id,
                "regenerate": payload.regenerate,
            }
            return REGENERATED

        monkeypatch.setattr(service.generation_service, "generate", fake_generate)
        return captured

    return setup


def _auth(make_token, role: str = "empresa"):
    token = make_token(tenant_id=TENANT_A, role=role)
    return {"Authorization": f"Bearer {token}"}


def test_remediation_saves_and_regenerates(client, make_token, wire_remediation):
    captured = wire_remediation()
    resp = client.post(
        f"/quality/reviews/{REVIEW_ID}/remediation",
        json={
            "answers": {
                "scope": "Rafting y rapel en el cañón del Melcocho.",
                "safety_objectives": "Reducir incidentes 20% en 2026.",
            }
        },
        headers=_auth(make_token),  # la empresa subsana: no exige rol revisor
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["review_id"] == REVIEW_ID
    assert body["document_type"] == "politica_seguridad"
    assert body["saved_fields"] == ["safety_objectives", "scope"]
    assert body["regenerated"] is True
    assert body["document"]["version"] == 4
    assert body["document"]["document_id"] == REGENERATED.document_id

    # El merge fue con los datos crudos y el tenant del JWT (nunca del body).
    assert captured["answers"]["scope"].startswith("Rafting")
    assert captured["merge_tenant"] == TENANT_A
    # La regeneración fue del tipo correcto y como versión nueva.
    assert captured["generated"] == {
        "document_type": "politica_seguridad",
        "tenant_id": TENANT_A,
        "regenerate": True,
    }


def test_remediation_without_regenerate_only_saves(
    client, make_token, wire_remediation
):
    captured = wire_remediation()
    resp = client.post(
        f"/quality/reviews/{REVIEW_ID}/remediation",
        json={"answers": {"scope": "Nuevo alcance."}, "regenerate": False},
        headers=_auth(make_token),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["regenerated"] is False
    assert body["document"] is None
    assert "generated" not in captured


def test_unknown_field_key_is_422(client, make_token, wire_remediation):
    wire_remediation()
    resp = client.post(
        f"/quality/reviews/{REVIEW_ID}/remediation",
        json={"answers": {"campo_inventado": "dato"}},
        headers=_auth(make_token),
    )
    assert resp.status_code == 422
    assert "campo_inventado" in resp.json()["detail"]


def test_pending_review_is_409(client, make_token, wire_remediation):
    wire_remediation(review_status="pending_review")
    resp = client.post(
        f"/quality/reviews/{REVIEW_ID}/remediation",
        json={"answers": {"scope": "dato"}},
        headers=_auth(make_token),
    )
    assert resp.status_code == 409


def test_rejected_is_remediable(client, make_token, wire_remediation):
    wire_remediation(review_status="rejected")
    resp = client.post(
        f"/quality/reviews/{REVIEW_ID}/remediation",
        json={"answers": {"scope": "dato"}},
        headers=_auth(make_token),
    )
    assert resp.status_code == 200, resp.text


def test_unknown_review_is_404(client, make_token, wire_remediation):
    wire_remediation(found=False)
    resp = client.post(
        f"/quality/reviews/{REVIEW_ID}/remediation",
        json={"answers": {"scope": "dato"}},
        headers=_auth(make_token),
    )
    assert resp.status_code == 404


def test_all_empty_answers_is_422(client, make_token, wire_remediation):
    wire_remediation()
    resp = client.post(
        f"/quality/reviews/{REVIEW_ID}/remediation",
        json={"answers": {"scope": "   "}},
        headers=_auth(make_token),
    )
    assert resp.status_code == 422


def test_requires_tenant_claim(client, make_token, wire_remediation):
    wire_remediation()
    token = make_token(tenant_id=None)
    resp = client.post(
        f"/quality/reviews/{REVIEW_ID}/remediation",
        json={"answers": {"scope": "dato"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 401
