import httpx
from supabase_auth.errors import AuthApiError

from app.modules.auth import repository as auth_repo

TENANT_A = "11111111-1111-1111-1111-111111111111"

_SIGNUP_BODY = {"email": "nuevo@empresa.co", "password": "secret123", "company_name": "ACME SAS"}


def test_signup_email_ya_registrado_es_409(client, monkeypatch):
    async def _boom(payload):
        raise AuthApiError(
            "A user with this email address has already been registered", 422,
            "user_already_exists",
        )

    monkeypatch.setattr(auth_repo, "provision", _boom)
    r = client.post("/auth/signup", json=_SIGNUP_BODY)
    assert r.status_code == 409
    assert "correo" in r.json()["detail"].lower()


def test_signup_error_auth_generico_es_400(client, monkeypatch):
    async def _boom(payload):
        raise AuthApiError("Password should be at least 6 characters", 400, "weak_password")

    monkeypatch.setattr(auth_repo, "provision", _boom)
    r = client.post("/auth/signup", json=_SIGNUP_BODY)
    assert r.status_code == 400


def test_signup_auth_caido_es_503(client, monkeypatch):
    async def _boom(payload):
        raise httpx.ConnectTimeout("timed out")

    monkeypatch.setattr(auth_repo, "provision", _boom)
    r = client.post("/auth/signup", json=_SIGNUP_BODY)
    assert r.status_code == 503


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_me_with_valid_jwt(client, make_token):
    token = make_token(tenant_id=TENANT_A, role="empresa")
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["tenant_id"] == TENANT_A
    assert body["role"] == "empresa"
    assert body["email"] == "tester@coladventure.co"


def test_me_without_tenant_claim_is_401(client, make_token):
    # Un JWT válido pero sin el claim tenant_id (perfil no provisionado) => 401.
    token = make_token(tenant_id=None)
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_me_without_token_is_rejected(client):
    response = client.get("/auth/me")
    assert response.status_code in (401, 403)


def test_me_with_garbage_token_is_401(client):
    response = client.get("/auth/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert response.status_code == 401
