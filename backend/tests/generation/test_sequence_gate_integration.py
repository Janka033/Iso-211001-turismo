"""El endpoint de generación respeta el gate de secuencia (defensa en
profundidad): si ``check_generatable`` dice que no, responde 409 y no genera.

El ``conftest`` de generación saltea el gate por defecto; aquí se re-monkeypatchea
para forzar el bloqueo.
"""

from app.modules.onboarding import service as onboarding_service

TENANT_A = "11111111-1111-1111-1111-111111111111"


def _auth(make_token):
    return {"Authorization": f"Bearer {make_token(tenant_id=TENANT_A, role='empresa')}"}


def test_generate_out_of_order_returns_409(client, make_token, monkeypatch):
    async def _blocked(document_type, tenant_id, token):
        return False, "Debes generar los documentos de los pasos anteriores antes de este."

    monkeypatch.setattr(onboarding_service, "check_generatable", _blocked)
    resp = client.post("/generation/matriz_riesgos", headers=_auth(make_token))
    assert resp.status_code == 409, resp.text
    assert "pasos anteriores" in resp.json()["detail"]
