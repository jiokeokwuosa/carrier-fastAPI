"""User registration and credential validation."""

from typing import List, Optional

from fastapi import HTTPException, status

from app.core.security import hash_password, verify_password
from app.models import UserRole
from app.repositories import UserRepository
from app.schemas import UserPayload


class UserService:
    """CRUD and credential validation for application users."""

    def __init__(self, repository: UserRepository):
        self.repository = repository

    def register(
        self, email: str, password: str, roles: Optional[List[str]] = None
    ) -> UserPayload:
        if self.repository.find_by_email(email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists",
            )
        user = self.repository.create(
            email=email,
            password_hash=hash_password(password),
            roles=roles or [UserRole.USER.value],
        )
        return UserPayload(id=user.id, email=user.email, roles=user.roles)

    def validate_user(self, email: str, password: str) -> Optional[UserPayload]:
        user = self.repository.find_by_email(email)
        if user is None:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return UserPayload(id=user.id, email=user.email, roles=user.roles)

    def get_by_id(self, user_id: str) -> Optional[UserPayload]:
        user = self.repository.find_by_id(user_id)
        if user is None:
            return None
        return UserPayload(id=user.id, email=user.email, roles=user.roles)
