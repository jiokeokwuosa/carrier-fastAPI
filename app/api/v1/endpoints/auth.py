"""User authentication endpoints — login, token refresh, and profile."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user, get_user_auth_service, get_user_service
from app.schemas import (
    LoginRequest,
    RefreshRequest,
    TokenPairResponse,
    UserPayload,
)
from app.services import UserAuthService, UserService

router = APIRouter(prefix="/auth", tags=["User Auth"])


@router.post("/login", response_model=TokenPairResponse)
async def login(
    body: LoginRequest,
    user_service: UserService = Depends(get_user_service),
    auth_service: UserAuthService = Depends(get_user_auth_service),
):
    user = await user_service.validate_user(body.email, body.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    return await auth_service.login(user)


@router.post("/refresh", response_model=TokenPairResponse)
async def refresh(
    body: RefreshRequest,
    auth_service: UserAuthService = Depends(get_user_auth_service),
):
    return await auth_service.refresh(body.refresh_token)


@router.get("/me", response_model=UserPayload)
async def me(current_user: UserPayload = Depends(get_current_user)):
    return current_user
