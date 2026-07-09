"""Database access for User records."""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Role, User, UserRole, role_names


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _with_roles(self):
        return select(User).options(selectinload(User.roles))

    async def find_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(
            self._with_roles().where(User.email == email.lower())
        )
        return result.scalar_one_or_none()

    async def find_by_id(self, user_id: str) -> Optional[User]:
        result = await self.db.execute(self._with_roles().where(User.id == user_id))
        return result.scalar_one_or_none()

    async def create(
        self, email: str, password_hash: str, roles: Optional[List[str]] = None
    ) -> User:
        role_names_to_assign = roles or [UserRole.USER.value]
        result = await self.db.execute(
            select(Role).where(Role.name.in_(role_names_to_assign))
        )
        role_objects = result.scalars().all()
        user = User(
            email=email.lower(),
            password_hash=password_hash,
            roles=role_objects,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return await self.find_by_id(user.id)  # type: ignore[return-value]
