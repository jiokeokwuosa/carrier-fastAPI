"""User management endpoints."""

from fastapi import APIRouter, Depends, status

from app.api.deps import get_user_service
from app.schemas import RegisterRequest, UserPayload
from app.services import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/register", response_model=UserPayload, status_code=status.HTTP_201_CREATED)
def register(
    body: RegisterRequest,
    user_service: UserService = Depends(get_user_service),
):
    return user_service.register(body.email, body.password, body.roles)
