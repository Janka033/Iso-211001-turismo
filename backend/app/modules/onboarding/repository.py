"""Único punto que habla con Supabase en el módulo onboarding.

Todo corre con el cliente del USUARIO (``get_user_client``) => RLS activo: las
lecturas y escrituras quedan acotadas al tenant del JWT. ``tenant_id`` se recibe
SIEMPRE como parámetro explícito. Mantiene un único registro de
``onboarding_data`` por tenant (lo que asume el módulo generation al leerlo).
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.core.supabase import get_user_client


def get_active_onboarding_prompt(token: str) -> dict | None:
    """Prompt activo del módulo onboarding (datos, no código). Único por módulo."""
    client = get_user_client(token)
    res = (
        client.table("prompt_versions")
        .select("version, content")
        .eq("module", "onboarding")
        .eq("is_active", True)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def get_activity_checklist(activities: list[str], token: str) -> list[dict]:
    """Filas Parte B (por actividad) de las actividades elegidas.

    Devuelve ``field_key``/``description``/``activity``/``required``
    deduplicados por ``field_key`` (un mismo requisito puede alimentar 2
    documentos y aparecer dos veces). Si CUALQUIERA de las filas duplicadas es
    ``required``, el campo queda ``required``: un campo obligatorio para un
    documento no se vuelve opcional por el orden en que llegan las filas. Las
    filas universales (Parte A) NO salen de aquí: las preguntas transversales
    las gobierna el service.
    """
    if not activities:
        return []
    client = get_user_client(token)
    res = (
        client.table("extraction_checklist")
        .select("field_key, description, activity, required")
        .in_("activity", activities)
        .execute()
    )
    by_key: dict[str, dict] = {}
    out: list[dict] = []
    for row in res.data or []:
        prev = by_key.get(row["field_key"])
        if prev is None:
            row = dict(row)
            by_key[row["field_key"]] = row
            out.append(row)
        elif row.get("required", True) and not prev.get("required", True):
            prev["required"] = True
    return out


def match_knowledge_chunks(
    embedding: list[float],
    numeral: str | None,
    token: str,
    source: str | None = None,
    limit: int = 3,
) -> list[dict]:
    """Paso RAG por actividad: top-K chunks por similitud (RPC pgvector de 0006).

    ``numeral=None`` no filtra por numeral: para una actividad el contexto
    relevante puede estar en varios numerales, así que dejamos que mande la
    similitud. Copia deliberada de la de generation: un módulo no importa el
    repository de otro.
    """
    client = get_user_client(token)
    res = client.rpc(
        "match_knowledge_chunks",
        {
            "query_embedding": embedding,
            "match_count": limit,
            "filter_source": source,
            "filter_numeral": numeral,
        },
    ).execute()
    return res.data or []


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
