"""Lógica de negocio del inventario operativo.

Llama al repository (síncrono => hilo con anyio). Valida las fotos de evidencia
(tipo y tamaño) antes de subirlas.
"""

from __future__ import annotations

import functools
import uuid
from collections.abc import Callable
from typing import TypeVar

import anyio
from fastapi import HTTPException, UploadFile, status

from app.modules.inventory import repository
from app.modules.inventory.schemas import (
    EvidenceOut,
    ItemCreate,
    ItemOut,
    ItemUpdate,
)

T = TypeVar("T")

_MAX_EVIDENCE_BYTES = 8 * 1024 * 1024  # 8 MB
_ALLOWED_IMAGE = {"image/jpeg", "image/png", "image/webp", "image/heic"}


async def _run(fn: Callable[..., T], *args: object) -> T:
    return await anyio.to_thread.run_sync(functools.partial(fn, *args))


def _to_item_out(row: dict, evidence_count: int = 0) -> ItemOut:
    return ItemOut(
        id=row["id"],
        category=row["category"],
        name=row["name"],
        attributes=row.get("attributes") or {},
        evidence_count=evidence_count,
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


async def list_items(
    tenant_id: str, token: str, category: str | None = None
) -> list[ItemOut]:
    rows = await _run(repository.list_items, tenant_id, token, category)
    counts = await _run(
        repository.count_evidence, tenant_id, [r["id"] for r in rows], token
    )
    return [_to_item_out(r, counts.get(r["id"], 0)) for r in rows]


async def create_item(payload: ItemCreate, tenant_id: str, token: str) -> ItemOut:
    row = await _run(repository.create_item, tenant_id, payload.model_dump(), token)
    return _to_item_out(row)


async def update_item(
    item_id: str, payload: ItemUpdate, tenant_id: str, token: str
) -> ItemOut:
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Nada que actualizar."
        )
    row = await _run(repository.update_item, tenant_id, item_id, changes, token)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ítem no encontrado."
        )
    return _to_item_out(row)


async def delete_item(item_id: str, tenant_id: str, token: str) -> None:
    deleted = await _run(repository.delete_item, tenant_id, item_id, token)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ítem no encontrado."
        )


async def add_evidence(
    item_id: str,
    file: UploadFile,
    caption: str | None,
    tenant_id: str,
    token: str,
) -> EvidenceOut:
    # RLS ya aísla, pero damos un 404 claro si el ítem no es del tenant.
    item = await _run(repository.get_item, tenant_id, item_id, token)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ítem no encontrado."
        )
    if file.content_type not in _ALLOWED_IMAGE:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Solo se aceptan imágenes (jpg, png, webp, heic).",
        )
    content = await file.read()
    if len(content) > _MAX_EVIDENCE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="La imagen supera el límite de 8 MB.",
        )
    ext = (file.filename or "foto").rsplit(".", 1)[-1][:8].lower() or "jpg"
    filename = f"{uuid.uuid4().hex}.{ext}"
    path = await _run(
        repository.upload_evidence_file,
        tenant_id,
        item_id,
        filename,
        content,
        file.content_type,
    )
    row = await _run(
        repository.add_evidence_row, tenant_id, item_id, path, caption, token
    )
    url = await _run(repository.signed_evidence_url, path)
    return EvidenceOut(
        id=row["id"], caption=row.get("caption"), url=url, uploaded_at=row["uploaded_at"]
    )


async def list_evidence(item_id: str, tenant_id: str, token: str) -> list[EvidenceOut]:
    rows = await _run(repository.list_evidence, tenant_id, item_id, token)
    out: list[EvidenceOut] = []
    for r in rows:
        url = await _run(repository.signed_evidence_url, r["storage_path"])
        out.append(
            EvidenceOut(
                id=r["id"],
                caption=r.get("caption"),
                url=url,
                uploaded_at=r["uploaded_at"],
            )
        )
    return out
