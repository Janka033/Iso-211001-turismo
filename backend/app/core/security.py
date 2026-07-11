"""Verificación del JWT de Supabase y dependencias de FastAPI.

El tenant_id y el rol de la app viajan como claims (``tenant_id`` y
``user_role``) inyectados por el ``custom_access_token_hook``. NUNCA se leen
del body del request.
"""

from functools import lru_cache

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from pydantic import BaseModel

from app.config import get_settings

_bearer = HTTPBearer(auto_error=True)

# Catálogo de roles de la app (claim user_role).
TENANT_ROLES = ("gerente", "coordinador", "recepcionista", "guia")
PLATFORM_ROLES = ("admin", "superadmin")
# 'empresa' es el rol legado pre-0031: es el dueño del tenant => gerente.
_LEGACY_ROLES = {"empresa": "gerente"}


def normalize_role(role: str) -> str:
    """Rol efectivo: mapea roles legados al catálogo vigente (espejo de la
    función SQL ``current_user_role()`` que usan las policies RLS)."""
    return _LEGACY_ROLES.get(role, role)


class CurrentUser(BaseModel):
    user_id: str
    email: str | None = None
    tenant_id: str | None = None
    role: str = "empresa"
    token: str


@lru_cache
def _jwk_client(jwks_url: str) -> PyJWKClient:
    return PyJWKClient(jwks_url)


def _decode(token: str) -> dict:
    settings = get_settings()
    audience = settings.supabase_jwt_audience or None
    try:
        if settings.supabase_jwks_url:
            signing_key = _jwk_client(settings.supabase_jwks_url).get_signing_key_from_jwt(token)
            return jwt.decode(
                token,
                signing_key.key,
                algorithms=["ES256", "RS256"],
                audience=audience,
            )
        # Fallback HS256: exige un secreto robusto. NUNCA validar con un
        # secreto vacío/débil (haría falsificable cualquier token HS256).
        if len(settings.supabase_jwt_secret) < 32:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Configuración de auth insegura: falta JWKS o un secreto JWT válido.",
            )
        return jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience=audience,
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido"
        ) from exc


async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
) -> CurrentUser:
    payload = _decode(creds.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token sin sub"
        )
    return CurrentUser(
        user_id=user_id,
        email=payload.get("email"),
        tenant_id=payload.get("tenant_id"),
        role=payload.get("user_role", "empresa"),
        token=creds.credentials,
    )


async def get_tenant_id(user: CurrentUser = Depends(get_current_user)) -> str:
    """tenant_id del JWT. 401 si falta el claim. Nunca del body."""
    if not user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="JWT sin claim tenant_id (perfil no provisionado)",
        )
    return user.tenant_id


def require_role(*roles: str):
    """Dependencia que exige uno de los roles dados (claim user_role).

    Compara roles NORMALIZADOS: un token legado con 'empresa' satisface
    ``require_role("gerente", ...)``.
    """
    allowed = {normalize_role(r) for r in roles}

    async def _checker(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if normalize_role(user.role) not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Rol no autorizado"
            )
        return user

    return _checker
