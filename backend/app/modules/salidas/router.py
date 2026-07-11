"""Endpoints del módulo salidas.

Dos routers:
- ``router`` (staff, JWT): gestión de salidas, guías, manifiesto y sync de
  eventos. tenant_id/token SIEMPRE del JWT.
- ``public_router`` (turista, sin auth): registro vía token del QR. El token
  identifica la salida y de ella se deriva el tenant; el rate limiting global
  por IP (main.py) también cubre esta ruta.
"""

from fastapi import APIRouter, Depends, status

from app.core.security import CurrentUser, get_current_user, get_tenant_id, require_role
from app.modules.salidas import service
from app.modules.salidas.schemas import (
    EventosSyncIn,
    EventosSyncOut,
    GuiaAssignIn,
    GuiaOut,
    ManifiestoOut,
    RegistroTuristaIn,
    RegistroTuristaOut,
    SalidaCreate,
    SalidaCreatedOut,
    SalidaOut,
    SalidaStatus,
    SalidaStatusUpdate,
)

router = APIRouter(prefix="/salidas", tags=["salidas"])
public_router = APIRouter(prefix="/public/salidas", tags=["public"])


@router.post("", response_model=SalidaCreatedOut, status_code=status.HTTP_201_CREATED)
async def create_salida(
    payload: SalidaCreate,
    user: CurrentUser = Depends(require_role("gerente", "coordinador")),
    tenant_id: str = Depends(get_tenant_id),
) -> SalidaCreatedOut:
    return await service.create_salida(payload, tenant_id, user.user_id, user.token)


@router.get("", response_model=list[SalidaOut])
async def list_salidas(
    status_filter: SalidaStatus | None = None,
    user: CurrentUser = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
) -> list[SalidaOut]:
    # Todos los roles del tenant listan; RLS acota al guía a SUS salidas.
    return await service.list_salidas(tenant_id, user.token, status_filter)


@router.get("/{salida_id}", response_model=SalidaOut)
async def get_salida(
    salida_id: str,
    user: CurrentUser = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
) -> SalidaOut:
    return await service.get_salida(salida_id, tenant_id, user.token)


@router.patch("/{salida_id}/estado", response_model=SalidaOut)
async def update_status(
    salida_id: str,
    payload: SalidaStatusUpdate,
    user: CurrentUser = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
) -> SalidaOut:
    # Gerente/coordinador o el guía asignado (lo resuelve RLS): iniciar y
    # finalizar en terreno nunca se bloquea por suscripción vencida.
    return await service.update_status(salida_id, payload, tenant_id, user.token)


@router.post(
    "/{salida_id}/guias", response_model=GuiaOut, status_code=status.HTTP_201_CREATED
)
async def assign_guia(
    salida_id: str,
    payload: GuiaAssignIn,
    user: CurrentUser = Depends(require_role("gerente", "coordinador")),
    tenant_id: str = Depends(get_tenant_id),
) -> GuiaOut:
    return await service.assign_guia(salida_id, payload, tenant_id, user.token)


@router.delete(
    "/{salida_id}/guias/{guia_user_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_guia(
    salida_id: str,
    guia_user_id: str,
    user: CurrentUser = Depends(require_role("gerente", "coordinador")),
    tenant_id: str = Depends(get_tenant_id),
) -> None:
    await service.remove_guia(salida_id, guia_user_id, tenant_id, user.token)


@router.get("/{salida_id}/manifiesto", response_model=ManifiestoOut)
async def manifiesto(
    salida_id: str,
    user: CurrentUser = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
) -> ManifiestoOut:
    # RLS gradúa la respuesta: recepcionista ve identidad + alerta sin salud;
    # el guía asignado y gerente/coordinador ven el detalle de salud.
    return await service.manifiesto(salida_id, tenant_id, user.token)


@router.post("/{salida_id}/eventos", response_model=EventosSyncOut)
async def sync_eventos(
    salida_id: str,
    payload: EventosSyncIn,
    user: CurrentUser = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),
) -> EventosSyncOut:
    return await service.sync_eventos(
        salida_id, payload, tenant_id, user.user_id, user.token
    )


# ---------------------------------------------------------------------------
# Público (turista)
# ---------------------------------------------------------------------------


@public_router.post(
    "/{public_token}/registro",
    response_model=RegistroTuristaOut,
    status_code=status.HTTP_201_CREATED,
)
async def registro_turista(
    public_token: str, payload: RegistroTuristaIn
) -> RegistroTuristaOut:
    return await service.registro_publico(public_token, payload)
