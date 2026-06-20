"""Único punto que habla con Supabase en el módulo onboarding.

Todo corre con el cliente del USUARIO (``get_user_client``) => RLS activo: las
lecturas y escrituras quedan acotadas al tenant del JWT. ``tenant_id`` se recibe
SIEMPRE como parámetro explícito. Mantiene un único registro de
``onboarding_data`` por tenant (lo que asume el módulo generation al leerlo).
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.core.supabase import get_user_client


def get_onboarding(tenant_id: str, token: str) -> dict:
    client = get_user_client(token)
    res = (
        client.table("onboarding_data")
        .select("data")
        .eq("tenant_id", tenant_id)
        .limit(1)
        .execute()
    )
    return res.data[0]["data"] if res.data else {}


def save_onboarding(tenant_id: str, data: dict, token: str) -> dict:
    """Upsert del registro único de onboarding del tenant.

    Sin constraint único en ``tenant_id``: buscamos la fila y hacemos UPDATE,
    o INSERT si no existe. RLS garantiza que solo se toca la fila del tenant.
    """
    client = get_user_client(token)
    existing = (
        client.table("onboarding_data")
        .select("id")
        .eq("tenant_id", tenant_id)
        .limit(1)
        .execute()
    )
    if existing.data:
        res = (
            client.table("onboarding_data")
            .update(
                {"data": data, "updated_at": datetime.now(UTC).isoformat()}
            )
            .eq("id", existing.data[0]["id"])
            .execute()
        )
    else:
        res = (
            client.table("onboarding_data")
            .insert({"tenant_id": tenant_id, "data": data})
            .execute()
        )
    return res.data[0]["data"] if res.data else data
