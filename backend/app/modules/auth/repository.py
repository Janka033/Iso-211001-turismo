"""Único punto que habla con Supabase en el módulo auth.

Excepción de provisioning: ``provision`` usa el service client (salta RLS)
porque CREA el tenant — el claim tenant_id aún no existe. La fila de
user_profiles se crea aquí, server-side y ANTES del primer token, para que
el hook inyecte tenant_id/user_role desde el token #1.
"""

from app.core.supabase import get_service_client
from app.modules.auth.schemas import SignupRequest, SignupResponse


async def provision(payload: SignupRequest) -> SignupResponse:
    admin = get_service_client()

    # 1. Usuario en Supabase Auth.
    created = admin.auth.admin.create_user(
        {
            "email": payload.email,
            "password": payload.password,
            "email_confirm": True,
        }
    )
    user_id = created.user.id

    # 2. Tenant.
    tenant = admin.table("tenants").insert({"name": payload.company_name}).execute()
    tenant_id = tenant.data[0]["id"]

    # 3. Company (datos del cliente).
    company = (
        admin.table("companies")
        .insert(
            {
                "tenant_id": tenant_id,
                "name": payload.company_name,
                "nit": payload.nit,
                "contact_email": payload.email,
            }
        )
        .execute()
    )
    company_id = company.data[0]["id"]

    # 4. Perfil (mapeo usuario->tenant). Fuente del claim del hook.
    admin.table("user_profiles").insert(
        {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "role": "empresa",
        }
    ).execute()

    return SignupResponse(user_id=user_id, tenant_id=tenant_id, company_id=company_id)
