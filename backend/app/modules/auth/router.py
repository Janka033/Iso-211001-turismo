from fastapi import APIRouter, Depends, status

from app.core.security import CurrentUser, get_current_user, get_tenant_id
from app.modules.auth import service
from app.modules.auth.schemas import MeResponse, SignupRequest, SignupResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
async def signup(payload: SignupRequest) -> SignupResponse:
    return await service.signup(payload)


@router.get("/me", response_model=MeResponse)
async def me(
    user: CurrentUser = Depends(get_current_user),
    _tenant: str = Depends(get_tenant_id),  # 401 si el JWT no trae tenant_id
) -> MeResponse:
    return await service.me(user)
