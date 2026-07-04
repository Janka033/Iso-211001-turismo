"""Único punto que habla con Supabase en el módulo generation.

Todo corre con el cliente del USUARIO (``get_user_client``) => RLS activo: las
lecturas y escrituras quedan acotadas al tenant del JWT. ``tenant_id`` se recibe
SIEMPRE como parámetro explícito (nunca se infiere).

La base de conocimiento, los prompts y la checklist son datos de producto
(globales) legibles por cualquier autenticado; igual pasan por aquí.
"""

from __future__ import annotations

import logging

from app.core.supabase import get_service_client, get_user_client

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
        # Solo la Parte A (transversal). Las filas por actividad (activity no
        # nulo) entran con la selección activity-aware de la Fase 2; hasta
        # entonces el cálculo de los 4 documentos queda idéntico.
        .is_("activity", "null")
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
    source: str | None = None,
    limit: int = 5,
) -> list[dict]:
    """Paso RAG: top-K chunks por similitud (RPC pgvector de 0006).

    ``source=None`` consulta TODOS los sources (norma + acotur + futuros como
    capacitaciones): las evidencias por numeral de ACOTUR son parte del
    contexto que el generador necesita.
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


_CONTENT_TYPE = {
    "docx": (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ),
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


def upload_document(
    tenant_id: str,
    document_type: str,
    version: int,
    content: bytes,
    token: str,
    engine: str = "docx",
) -> str | None:
    """Sube el documento a Storage. Usa el service client (Storage en cloud no
    aplica bien las policies SQL sobre storage.objects). El aislamiento por
    tenant lo garantiza la RUTA ``{tenant_id}/...``: ``tenant_id`` viene del JWT
    (get_tenant_id), nunca del cliente, así que un tenant nunca escribe en la
    carpeta de otro. Best-effort: si falla, None (el doc es regenerable).
    ``token`` se conserva por compatibilidad de firma."""
    path = f"{tenant_id}/{document_type}/v{version}.{engine}"
    try:
        client = get_service_client()
        client.storage.from_(STORAGE_BUCKET).upload(
            path=path,
            file=content,
            file_options={
                "content-type": _CONTENT_TYPE.get(engine, "application/octet-stream"),
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


def create_signed_url(
    tenant_id: str,
    document_type: str,
    version: int,
    engine: str,
    expires_in: int = 300,
) -> str | None:
    """URL firmada y temporal para descargar el documento. Service client; la
    ruta se arma con el tenant_id del JWT, así que solo firma docs del propio
    tenant. None si el archivo no existe en Storage."""
    path = f"{tenant_id}/{document_type}/v{version}.{engine}"
    try:
        client = get_service_client()
        res = client.storage.from_(STORAGE_BUCKET).create_signed_url(path, expires_in)
        return res.get("signedURL") or res.get("signedUrl")
    except Exception as exc:  # noqa: BLE001 - storage opcional
        logger.warning("No se pudo firmar la URL de %s: %s", path, exc)
        return None
