"""Único punto que habla con Supabase en el módulo inventory.

Las TABLAS (operational_items, item_evidence) usan el USER client => RLS por
tenant. El STORAGE de fotos usa el service client con ruta ``{tenant_id}/...``
(en cloud las policies SQL sobre storage.objects no aplican; el aislamiento lo
da la ruta, que sale del JWT). ``tenant_id`` siempre explícito.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from app.core.supabase import get_service_client, get_user_client

logger = logging.getLogger(__name__)

EVIDENCE_BUCKET = "evidence"
_ITEM_COLS = "id, category, name, attributes, created_at, updated_at"


# ---------------------------------------------------------------------------
# Ítems del inventario (tabla tenant-scoped => user client / RLS)
# ---------------------------------------------------------------------------


def list_items(tenant_id: str, token: str, category: str | None = None) -> list[dict]:
    client = get_user_client(token)
    query = (
        client.table("operational_items").select(_ITEM_COLS).eq("tenant_id", tenant_id)
    )
    if category:
        query = query.eq("category", category)
    return query.order("created_at", desc=True).execute().data or []


def get_item(tenant_id: str, item_id: str, token: str) -> dict | None:
    client = get_user_client(token)
    res = (
        client.table("operational_items")
        .select("id")
        .eq("tenant_id", tenant_id)
        .eq("id", item_id)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def create_item(tenant_id: str, data: dict, token: str) -> dict:
    client = get_user_client(token)
    return (
        client.table("operational_items")
        .insert({"tenant_id": tenant_id, **data})
        .execute()
        .data[0]
    )


def update_item(tenant_id: str, item_id: str, changes: dict, token: str) -> dict | None:
    client = get_user_client(token)
    payload = {**changes, "updated_at": datetime.now(UTC).isoformat()}
    res = (
        client.table("operational_items")
        .update(payload)
        .eq("tenant_id", tenant_id)
        .eq("id", item_id)
        .execute()
    )
    return res.data[0] if res.data else None


def delete_item(tenant_id: str, item_id: str, token: str) -> bool:
    """Borra el ítem y devuelve True si efectivamente borró una fila.

    PostgREST con ``return=representation`` (default de supabase-py en delete)
    devuelve las filas borradas en ``res.data``. Si RLS filtra la fila o el id
    no existe, ``res.data`` viene vacío y el borrado afectó 0 filas: hay que
    propagarlo para no responder 204 sobre un no-op.
    """
    client = get_user_client(token)
    res = (
        client.table("operational_items")
        .delete()
        .eq("tenant_id", tenant_id)
        .eq("id", item_id)
        .execute()
    )
    return bool(res.data)


def count_evidence(tenant_id: str, item_ids: list[str], token: str) -> dict[str, int]:
    if not item_ids:
        return {}
    client = get_user_client(token)
    res = (
        client.table("item_evidence")
        .select("item_id")
        .eq("tenant_id", tenant_id)
        .in_("item_id", item_ids)
        .execute()
    )
    counts: dict[str, int] = {}
    for row in res.data or []:
        counts[row["item_id"]] = counts.get(row["item_id"], 0) + 1
    return counts


# ---------------------------------------------------------------------------
# Evidencia: fila en item_evidence (user client) + foto en Storage (service)
# ---------------------------------------------------------------------------


def add_evidence_row(
    tenant_id: str, item_id: str, storage_path: str, caption: str | None, token: str
) -> dict:
    client = get_user_client(token)
    return (
        client.table("item_evidence")
        .insert(
            {
                "tenant_id": tenant_id,
                "item_id": item_id,
                "storage_path": storage_path,
                "caption": caption,
            }
        )
        .execute()
        .data[0]
    )


def list_evidence(tenant_id: str, item_id: str, token: str) -> list[dict]:
    client = get_user_client(token)
    return (
        client.table("item_evidence")
        .select("id, caption, storage_path, uploaded_at")
        .eq("tenant_id", tenant_id)
        .eq("item_id", item_id)
        .order("uploaded_at", desc=True)
        .execute()
        .data
        or []
    )


def upload_evidence_file(
    tenant_id: str, item_id: str, filename: str, content: bytes, content_type: str
) -> str:
    """Sube la foto al bucket privado con el service client. Ruta acotada al
    tenant (sale del JWT), así que un tenant nunca escribe en carpeta de otro."""
    path = f"{tenant_id}/{item_id}/{filename}"
    client = get_service_client()
    client.storage.from_(EVIDENCE_BUCKET).upload(
        path=path,
        file=content,
        file_options={"content-type": content_type, "upsert": "true"},
    )
    return path


def signed_evidence_url(storage_path: str, expires_in: int = 300) -> str | None:
    try:
        client = get_service_client()
        res = client.storage.from_(EVIDENCE_BUCKET).create_signed_url(
            storage_path, expires_in
        )
        return res.get("signedURL") or res.get("signedUrl")
    except Exception as exc:  # noqa: BLE001 - storage opcional
        logger.warning("No se pudo firmar la evidencia %s: %s", storage_path, exc)
        return None
