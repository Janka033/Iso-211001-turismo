"""Test de aislamiento RLS (NO negociable).

Prueba que, con el JWT del tenant A, NO se pueden leer filas del tenant B.
Es la prueba de que RLS protege de verdad cuando el backend usa el JWT del
usuario (no la service_role key).

Requiere un Supabase local con las migraciones aplicadas y el
custom_access_token_hook activo. Se salta salvo que RUN_DB_TESTS=1.

    supabase start
    RUN_DB_TESTS=1 pytest tests/auth/test_rls_integration.py
"""

import os
import uuid

import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS") != "1",
    reason="Integración con DB: define RUN_DB_TESTS=1 y un Supabase local con las migraciones.",
)


def _signin_token(email: str, password: str) -> str:
    from supabase import create_client

    from app.config import get_settings

    settings = get_settings()
    anon = create_client(settings.supabase_url, settings.supabase_anon_key)
    session = anon.auth.sign_in_with_password({"email": email, "password": password})
    return session.session.access_token


@pytest.mark.asyncio
async def test_tenant_cannot_read_other_tenant_rows():
    from app.core.supabase import get_user_client
    from app.modules.auth.repository import provision
    from app.modules.auth.schemas import SignupRequest

    suffix = uuid.uuid4().hex[:8]
    pwd = "passw0rd-test"

    a = await provision(
        SignupRequest(email=f"a-{suffix}@test.co", password=pwd, company_name=f"Empresa A {suffix}")
    )
    b = await provision(
        SignupRequest(email=f"b-{suffix}@test.co", password=pwd, company_name=f"Empresa B {suffix}")
    )

    token_a = _signin_token(f"a-{suffix}@test.co", pwd)
    client_a = get_user_client(token_a)

    # A solo ve su propia company.
    visible = client_a.table("companies").select("id, tenant_id").execute()
    tenant_ids = {row["tenant_id"] for row in visible.data}
    assert tenant_ids == {a.tenant_id}, "RLS roto: A ve filas de otro tenant"

    # A intenta leer la company de B por id explícito => RLS lo bloquea (vacío).
    leak = client_a.table("companies").select("id").eq("id", b.company_id).execute()
    assert leak.data == [], "RLS roto: A pudo leer una fila de B"
