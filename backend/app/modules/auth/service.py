"""Lógica de negocio del módulo auth. Llama al repository; nunca a Supabase directo."""

from app.core.security import CurrentUser
from app.modules.auth import repository
from app.modules.auth.schemas import MeResponse, SignupRequest, SignupResponse


async def signup(payload: SignupRequest) -> SignupResponse:
    return await repository.provision(payload)


async def me(user: CurrentUser) -> MeResponse:
    # get_tenant_id ya garantiza el claim; aquí solo se mapea.
    return MeResponse(
        user_id=user.user_id,
        email=user.email,
        tenant_id=user.tenant_id or "",
        role=user.role,
    )
