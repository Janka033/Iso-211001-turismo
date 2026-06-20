"""Endpoints del módulo onboarding.

El router solo recibe el request, toma ``tenant_id``/``token`` del JWT (nunca del
body) y delega en el service. Sin lógica de negocio ni acceso a DB aquí.
"""

from fastapi import APIRouter, Depends

from app.core.security import CurrentUser, get_current_user, get_tenant_id
from app.modules.onboarding import service
from app.modules.onboarding.schemas import OnboardingPayload, OnboardingState

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.get("", response_model=OnboardingState)
async def read_onboarding(
    user: CurrentUser = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),  # 401 si el JWT no trae el claim
) -> OnboardingState:
    return await service.get_state(tenant_id, user.token)


@router.put("", response_model=OnboardingState)
async def update_onboarding(
    payload: OnboardingPayload,
    user: CurrentUser = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id),  # 401 si el JWT no trae el claim
) -> OnboardingState:
    return await service.save(payload, tenant_id, user.token)
