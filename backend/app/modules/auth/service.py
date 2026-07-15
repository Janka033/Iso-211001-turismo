"""Lógica de negocio del módulo auth. Llama al repository; nunca a Supabase directo."""

import httpx
from fastapi import HTTPException, status
from supabase_auth.errors import AuthApiError

from app.core.security import CurrentUser
from app.modules.auth import repository
from app.modules.auth.schemas import MeResponse, SignupRequest, SignupResponse


async def signup(payload: SignupRequest) -> SignupResponse:
    # El provisioning habla con Supabase Auth: sus errores NO deben salir como
    # 500. El correo repetido es un caso esperado (409) y una caída de red del
    # servicio de auth, un 503; ambos con mensaje claro para el usuario.
    try:
        return await repository.provision(payload)
    except AuthApiError as exc:
        detail = str(exc).lower()
        if "already" in detail and "registered" in detail:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe una cuenta con este correo.",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo crear la cuenta. Revisa el correo y la contraseña.",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El servicio de autenticación no está disponible. Intenta de nuevo.",
        ) from exc


async def me(user: CurrentUser) -> MeResponse:
    # get_tenant_id ya garantiza el claim; aquí solo se mapea.
    return MeResponse(
        user_id=user.user_id,
        email=user.email,
        tenant_id=user.tenant_id or "",
        role=user.role,
    )
