"""User registration and credential validation."""

import asyncio
from typing import Optional

from fastapi import HTTPException, status

from app.core.security import hash_password, verify_password
from app.models import UserRole, role_names
from app.repositories import UserRepository
from app.schemas import UserPayload


class UserService:
    """CRUD and credential validation for application users."""

    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def register(self, email: str, password: str) -> UserPayload:
        if await self.repository.find_by_email(email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists",
            )
        password_hash = await asyncio.to_thread(hash_password, password)
        user = await self.repository.create(
            email=email,
            password_hash=password_hash,
            roles=[UserRole.USER.value],
        )
        return UserPayload(id=user.id, email=user.email, roles=role_names(user))

    async def validate_user(self, email: str, password: str) -> Optional[UserPayload]:
        user = await self.repository.find_by_email(email)
        if user is None:
            return None
        valid = await asyncio.to_thread(verify_password, password, user.password_hash)
        if not valid:
            return None
        return UserPayload(id=user.id, email=user.email, roles=role_names(user))

    async def get_by_id(self, user_id: str) -> Optional[UserPayload]:
        user = await self.repository.find_by_id(user_id)
        if user is None:
            return None
        return UserPayload(id=user.id, email=user.email, roles=role_names(user))
