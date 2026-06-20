"""Endpoints del módulo inventory (inventario operativo + evidencia).

El router toma ``tenant_id``/``token`` del JWT (nunca del body) y delega en el
service. Sin lógica de negocio ni acceso a DB aquí.
"""

from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from app.core.security import CurrentUser, get_current_user, get_tenant_id
from app.modules.inventory import service
from app.modules.inventory.schemas import (
    EvidenceOut,
    ItemCreate,
    ItemOut,
    ItemUpdate,
)

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("", response_model=list[ItemOut])
async def list_items(
    category: str | None = None,
    user: CurrentUser = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
) -> list[ItemOut]:
    return await service.list_items(tenant_id, user.token, category)


@router.post("", response_model=ItemOut, status_code=status.HTTP_201_CREATED)
async def create_item(
    payload: ItemCreate,
    user: CurrentUser = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
) -> ItemOut:
    return await service.create_item(payload, tenant_id, user.token)


@router.put("/{item_id}", response_model=ItemOut)
async def update_item(
    item_id: str,
    payload: ItemUpdate,
    user: CurrentUser = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
) -> ItemOut:
    return await service.update_item(item_id, payload, tenant_id, user.token)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: str,
    user: CurrentUser = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
) -> None:
    await service.delete_item(item_id, tenant_id, user.token)


@router.post(
    "/{item_id}/evidence",
    response_model=EvidenceOut,
    status_code=status.HTTP_201_CREATED,
)
async def upload_evidence(
    item_id: str,
    file: UploadFile = File(...),
    caption: str | None = Form(default=None),
    user: CurrentUser = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
) -> EvidenceOut:
    return await service.add_evidence(item_id, file, caption, tenant_id, user.token)


@router.get("/{item_id}/evidence", response_model=list[EvidenceOut])
async def list_evidence(
    item_id: str,
    user: CurrentUser = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
) -> list[EvidenceOut]:
    return await service.list_evidence(item_id, tenant_id, user.token)
