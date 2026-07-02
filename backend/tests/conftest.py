import os
from pathlib import Path

import jwt
import pytest

# Secreto de fallback SOLO si no hay .env (p.ej. CI sin Supabase local).
FALLBACK_JWT_SECRET = "test-secret-test-secret-test-secret-1234"


@pytest.fixture(scope="session", autouse=True)
def _env() -> None:
    # Los tests firman sus tokens con HS256: se fuerza esa rama aunque el .env
    # del desarrollador tenga SUPABASE_JWKS_URL (la CLI moderna firma ES256).
    # os.environ tiene precedencia sobre el env_file en pydantic-settings.
    os.environ["SUPABASE_JWKS_URL"] = ""

    # Si no hay backend/.env (p.ej. CI sin Supabase local), defaults de prueba.
    backend_env = Path(__file__).resolve().parents[1] / ".env"
    if not backend_env.exists():
        os.environ.setdefault("SUPABASE_JWT_SECRET", FALLBACK_JWT_SECRET)
        os.environ.setdefault("SUPABASE_URL", "http://127.0.0.1:54321")
        os.environ.setdefault("SUPABASE_ANON_KEY", "anon-test-key")
        os.environ.setdefault("SUPABASE_JWT_AUDIENCE", "authenticated")

    from app.config import get_settings

    get_settings.cache_clear()
    yield


@pytest.fixture
def make_token():
    # Firma con el MISMO secreto que la app verifica (real local o fallback).
    from app.config import get_settings

    secret = get_settings().supabase_jwt_secret
    audience = get_settings().supabase_jwt_audience

    def _make(
        tenant_id: str | None = None,
        role: str = "empresa",
        sub: str = "00000000-0000-0000-0000-0000000000aa",
        email: str = "tester@coladventure.co",
    ) -> str:
        claims = {"sub": sub, "email": email, "aud": audience, "user_role": role}
        if tenant_id:
            claims["tenant_id"] = tenant_id
        return jwt.encode(claims, secret, algorithm="HS256")

    return _make


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    return TestClient(app)
