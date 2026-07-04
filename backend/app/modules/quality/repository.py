"""Único punto que habla con Supabase en el módulo quality.

Todo corre con el cliente del USUARIO (``get_user_client``) => RLS activo: las
lecturas y escrituras quedan acotadas al tenant del JWT. ``tenant_id`` se
recibe SIEMPRE como parámetro explícito (nunca se infiere).

La decisión del revisor está protegida también en DB: la policy de UPDATE de
``quality_reviews`` (migración 0018) exige rol admin/superadmin en el JWT.
"""

from __future__ import annotations

from app.core.supabase import get_user_client

# ---------------------------------------------------------------------------
# Lecturas: documento a evaluar + reglas de negocio (datos de producto)
# ---------------------------------------------------------------------------


def get_document(document_id: str, tenant_id: str, token: str) -> dict | None:
    """Documento generado del tenant. RLS + filtro explícito por tenant."""
    client = get_user_client(token)
    res = (
        client.table("documents")
        .select("id, document_type, version, variables_snapshot")
        .eq("id", document_id)
        .eq("tenant_id", tenant_id)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def get_active_quality_prompt(token: str) -> dict | None:
    """Prompt activo del módulo (uno solo, genérico para todos los tipos)."""
    client = get_user_client(token)
    res = (
        client.table("prompt_versions")
        .select("version, content")
        .eq("module", "quality")
        .eq("is_active", True)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def get_checklist(document_type: str, token: str) -> list[dict]:
    client = get_user_client(token)
    res = (
        client.table("extraction_checklist")
        .select("field_key, description, required, numeral")
        .eq("document_type", document_type)
        .execute()
    )
    return res.data or []


def get_generation_patterns(document_type: str, token: str) -> list[dict]:
    client = get_user_client(token)
    res = (
        client.table("generation_patterns")
        .select("pattern_type, description, numeral")
        .eq("document_type", document_type)
        .execute()
    )
    return res.data or []


def match_knowledge_chunks(
    embedding: list[float],
    numeral: str,
    token: str,
    limit: int = 5,
) -> list[dict]:
    """Paso RAG: contexto normativo del numeral para juzgar coherencia
    contra la norma real (todos los sources, como en generation)."""
    client = get_user_client(token)
    res = client.rpc(
        "match_knowledge_chunks",
        {
            "query_embedding": embedding,
            "match_count": limit,
            "filter_source": None,
            "filter_numeral": numeral,
        },
    ).execute()
    return res.data or []


def get_review(review_id: str, tenant_id: str, token: str) -> dict | None:
    """Evaluación del tenant, con el documento embebido vía FK (tipo y versión)."""
    client = get_user_client(token)
    res = (
        client.table("quality_reviews")
        .select("*, documents(document_type, version)")
        .eq("id", review_id)
        .eq("tenant_id", tenant_id)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


# ---------------------------------------------------------------------------
# Escrituras: evaluación + decisión del revisor
# ---------------------------------------------------------------------------


def insert_review(record: dict, token: str) -> dict:
    """Inserta la evaluación con su snapshot de reproducibilidad."""
    client = get_user_client(token)
    res = client.table("quality_reviews").insert(record).execute()
    return res.data[0]


def update_review_decision(
    review_id: str, tenant_id: str, fields: dict, token: str
) -> dict | None:
    """Aplica la decisión del revisor. Si la policy de UPDATE (rol revisor)
    filtra la fila, el update vuelve vacío y devolvemos None."""
    client = get_user_client(token)
    res = (
        client.table("quality_reviews")
        .update(fields)
        .eq("id", review_id)
        .eq("tenant_id", tenant_id)
        .execute()
    )
    return res.data[0] if res.data else None


def set_document_status(
    tenant_id: str, document_type: str, status: str, token: str
) -> None:
    """Refleja la decisión en el estado del documento.

    UPDATE (no upsert) a propósito: la fila la crea la generación y aquí no
    debe pisarse ``completeness`` ni crearse estado para documentos que nunca
    se generaron.
    """
    client = get_user_client(token)
    (
        client.table("document_status")
        .update({"status": status})
        .eq("tenant_id", tenant_id)
        .eq("document_type", document_type)
        .execute()
    )
