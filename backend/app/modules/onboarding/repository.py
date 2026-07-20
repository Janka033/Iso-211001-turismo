"""Único punto que habla con Supabase en el módulo onboarding.

Todo corre con el cliente del USUARIO (``get_user_client``) => RLS activo: las
lecturas y escrituras quedan acotadas al tenant del JWT. ``tenant_id`` se recibe
SIEMPRE como parámetro explícito. Mantiene un único registro de
``onboarding_data`` por tenant (lo que asume el módulo generation al leerlo).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

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


def get_roadmap(token: str) -> list[dict]:
    """Los pasos habilitados de la ruta guiada, en orden (config global, 0045)."""
    client = get_user_client(token)
    res = (
        client.table("document_roadmap")
        .select("step_order, document_type, title, numeral, generator_ready")
        .eq("enabled", True)
        .order("step_order")
        .execute()
    )
    return res.data or []


def get_document_statuses(tenant_id: str, token: str) -> list[dict]:
    """Estado de generación por document_type del tenant (document_status)."""
    client = get_user_client(token)
    res = (
        client.table("document_status")
        .select("document_type, status, completeness")
        .eq("tenant_id", tenant_id)
        .execute()
    )
    return res.data or []


def get_latest_review_scores(tenant_id: str, token: str) -> list[dict]:
    """Reviews de calidad del tenant (score + document_type), recientes primero.

    El service se queda con el primer score por document_type (el más nuevo).
    """
    client = get_user_client(token)
    res = (
        client.table("quality_reviews")
        .select("score, created_at, documents!inner(document_type)")
        .eq("tenant_id", tenant_id)
        .order("created_at", desc=True)
        .execute()
    )
    return res.data or []


def get_chat_messages(tenant_id: str, token: str) -> list[dict]:
    """Historial persistido del chat de onboarding del tenant, en orden.

    ``chat_messages`` ya existe con RLS por tenant (0002/0003). Hoy el
    onboarding es su ÚNICO escritor, así que se filtra solo por tenant; cuando
    exista el módulo assistant habrá que añadir una columna ``context`` para no
    mezclar hilos.
    """
    client = get_user_client(token)
    res = (
        client.table("chat_messages")
        .select("role, content, created_at")
        .eq("tenant_id", tenant_id)
        .order("created_at")
        .execute()
    )
    return res.data or []


def save_chat_messages(tenant_id: str, rows: list[dict], token: str) -> None:
    """Inserta los mensajes de un turno (user + assistant) en ``chat_messages``.

    Cada fila: ``{"role": "user"|"assistant", "content": str}``. RLS garantiza
    que solo se escribe en el tenant del JWT.

    ``created_at`` se fija EXPLÍCITO y estrictamente creciente por fila: el
    default ``now()`` es el timestamp de la transacción —idéntico para todas las
    filas de un mismo insert—, así que ordenar por él dejaría el orden user↔
    assistant indefinido y el transcript podría invertirse. El offset por índice
    garantiza que la pregunta/respuesta conserven su orden al releer.
    """
    if not rows:
        return
    client = get_user_client(token)
    now = datetime.now(UTC)
    payload = [
        {
            "tenant_id": tenant_id,
            "role": row["role"],
            "content": row["content"],
            "created_at": (now + timedelta(microseconds=i)).isoformat(),
        }
        for i, row in enumerate(rows)
    ]
    client.table("chat_messages").insert(payload).execute()


def get_onboarding(tenant_id: str, token: str) -> dict:
    # `order` por updated_at desc: si por una carrera hubiera más de una fila
    # para el tenant (sin constraint único), SIEMPRE se lee la más reciente. Sin
    # el orden, `limit(1)` devolvía una fila arbitraria y una corrección podía
    # "no pegarse" (se leía una copia vieja distinta a la que se escribió).
    client = get_user_client(token)
    res = (
        client.table("onboarding_data")
        .select("data")
        .eq("tenant_id", tenant_id)
        .order("updated_at", desc=True)
        .limit(1)
        .execute()
    )
    return res.data[0]["data"] if res.data else {}


def save_onboarding(tenant_id: str, data: dict, token: str) -> dict:
    """Upsert del registro único de onboarding del tenant.

    Con el constraint único en ``tenant_id`` (migración 0064) se usa
    ``upsert(on_conflict="tenant_id")``: idempotente y SIN carrera —dos
    peticiones concurrentes (p. ej. el doble montaje de React en dev) ya no
    crean filas duplicadas, la segunda ACTUALIZA en vez de insertar—. En el
    conflicto conserva ``id``/``created_at`` y refresca ``data``/``updated_at``.
    RLS garantiza que solo se toca la fila del tenant del JWT.
    """
    client = get_user_client(token)
    res = (
        client.table("onboarding_data")
        .upsert(
            {
                "tenant_id": tenant_id,
                "data": data,
                "updated_at": datetime.now(UTC).isoformat(),
            },
            on_conflict="tenant_id",
        )
        .execute()
    )
    return res.data[0]["data"] if res.data else data
