"""Endpoints del módulo generation.

El router solo recibe el request, toma ``tenant_id``/``token`` del JWT (nunca
del body) y delega en el service. Sin lógica de negocio ni acceso a DB aquí.
"""

from fastapi import APIRouter, Depends, status

from app.core.security import CurrentUser, get_current_user, get_tenant_id
from app.modules.generation import service
from app.modules.generation.generators.factory import supported_types
from app.modules.generation.schemas import (
    DownloadResponse,
    GeneratedDocument,
    GenerateRequest,
)

router = APIRouter(prefix="/generation", tags=["generation"])


@router.get("/document-types")
async def list_document_types(
    _user: CurrentUser = Depends(get_current_user),
) -> list[str]:
    """Tipos de documento que el motor sabe generar hoy."""
    return supported_types()


@router.post(
    "/{document_type}",
    response_model=GeneratedDocument,
    status_code=status.HTTP_201_CREATED,
)
async def generate_document(
    document_type: str,
    payload: GenerateRequest = GenerateRequest(),
    user: CurrentUser = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),  # 401 si el JWT no trae el claim
) -> GeneratedDocument:
    return await service.generate(document_type, tenant_id, user.token, payload)


@router.get("/{document_type}/download", response_model=DownloadResponse)
async def download_document(
    document_type: str,
    version: int,
    _user: CurrentUser = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),  # 401 si el JWT no trae el claim
) -> DownloadResponse:
    """Devuelve una URL firmada y temporal para descargar el documento."""
    return await service.download_url(document_type, version, tenant_id)
