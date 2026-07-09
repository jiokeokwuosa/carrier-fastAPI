"""Database access for refresh tokens (stored as SHA-256 hashes)."""

from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models import RefreshToken, User


class RefreshTokenRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self, user_id: str, token_hash: str, expires_at: datetime
    ) -> RefreshToken:
        record = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        return record

    async def find_by_hash(self, token_hash: str) -> Optional[RefreshToken]:
        result = await self.db.execute(
            select(RefreshToken)
            .options(
                joinedload(RefreshToken.user).selectinload(User.roles),
            )
            .where(RefreshToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def delete(self, record: RefreshToken) -> None:
        await self.db.delete(record)
        await self.db.commit()
