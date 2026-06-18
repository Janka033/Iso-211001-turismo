"""Único punto que habla con Supabase en el módulo generation.

Todo corre con el cliente del USUARIO (``get_user_client``) => RLS activo: las
lecturas y escrituras quedan acotadas al tenant del JWT. ``tenant_id`` se recibe
SIEMPRE como parámetro explícito (nunca se infiere).

La base de conocimiento, los prompts y la checklist son datos de producto
(globales) legibles por cualquier autenticado; igual pasan por aquí.
"""

from __future__ import annotations

import logging

from app.core.supabase import get_user_client

logger = logging.getLogger(__name__)

STORAGE_BUCKET = "documents"


# ---------------------------------------------------------------------------
# Lecturas: contexto del tenant
# ---------------------------------------------------------------------------


def get_company(tenant_id: str, token: str) -> dict | None:
    client = get_user_client(token)
    res = (
        client.table("companies")
        .select("name, nit, rnt, legal_representative, contact_email")
        .eq("tenant_id", tenant_id)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def get_onboarding_data(tenant_id: str, token: str) -> dict:
    client = get_user_client(token)
    res = (
        client.table("onboarding_data")
        .select("data")
        .eq("tenant_id", tenant_id)
        .limit(1)
        .execute()
    )
    return res.data[0]["data"] if res.data else {}


# ---------------------------------------------------------------------------
# Lecturas: configuración de producto (global)
# ---------------------------------------------------------------------------


def get_active_prompt(document_type: str, token: str) -> dict | None:
    client = get_user_client(token)
    res = (
        client.table("prompt_versions")
        .select("version, content")
        .eq("module", "generation")
        .eq("document_type", document_type)
        .eq("is_active", True)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def get_checklist(document_type: str, token: str) -> list[dict]:
    client = get_user_client(token)
    res = (
        client.table("extraction_checklist")
        .select("field_key, description, required")
        .eq("document_type", document_type)
        .execute()
    )
    return res.data or []


def get_generation_patterns(document_type: str, token: str) -> list[dict]:
    client = get_user_client(token)
    res = (
        client.table("generation_patterns")
        .select("pattern_type, description")
        .eq("document_type", document_type)
        .execute()
    )
    return res.data or []


def match_knowledge_chunks(
    embedding: list[float],
    numeral: str,
    token: str,
    source: str = "norma",
    limit: int = 5,
) -> list[dict]:
    """Paso RAG: top-K chunks por similitud (RPC pgvector de 0006)."""
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


# ---------------------------------------------------------------------------
# Escrituras: documento generado + estado
# ---------------------------------------------------------------------------


def next_version(tenant_id: str, document_type: str, token: str) -> int:
    client = get_user_client(token)
    res = (
        client.table("documents")
        .select("version")
        .eq("tenant_id", tenant_id)
        .eq("document_type", document_type)
        .order("version", desc=True)
        .limit(1)
        .execute()
    )
    return (res.data[0]["version"] + 1) if res.data else 1


def upload_document(
    tenant_id: str,
    document_type: str,
    version: int,
    content: bytes,
    token: str,
) -> str | None:
    """Sube el .docx a Storage. Best-effort: si el bucket/policies no están
    configurados, devolvemos None y seguimos. El snapshot reproducible queda
    igual en ``documents``, así que el archivo es regenerable."""
    path = f"{tenant_id}/{document_type}/v{version}.docx"
    try:
        client = get_user_client(token)
        client.storage.from_(STORAGE_BUCKET).upload(
            path=path,
            file=content,
            file_options={
                "content-type": (
                    "application/vnd.openxmlformats-officedocument."
                    "wordprocessingml.document"
                ),
                "upsert": "true",
            },
        )
        return path
    except Exception as exc:  # noqa: BLE001 - storage opcional en el MVP
        logger.warning("No se pudo subir el documento a Storage (%s): %s", path, exc)
        return None


def insert_document(record: dict, token: str) -> dict:
    """Inserta la fila de ``documents`` con el snapshot de reproducibilidad."""
    client = get_user_client(token)
    res = client.table("documents").insert(record).execute()
    return res.data[0]


def upsert_document_status(
    tenant_id: str,
    document_type: str,
    status: str,
    completeness: float,
    token: str,
) -> None:
    client = get_user_client(token)
    client.table("document_status").upsert(
        {
            "tenant_id": tenant_id,
            "document_type": document_type,
            "status": status,
            "completeness": completeness,
        },
        on_conflict="tenant_id,document_type",
    ).execute()
