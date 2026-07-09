"""Database access for cached carrier OAuth tokens (one row per platform)."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CarrierToken


class CarrierTokenRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_by_platform(self, platform: str) -> Optional[CarrierToken]:
        result = await self.db.execute(
            select(CarrierToken).where(CarrierToken.platform == platform)
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        platform: str,
        token_type: str,
        issued_at: str,
        client_id: str,
        access_token: str,
        expires_in: str,
    ) -> CarrierToken:
        existing = await self.find_by_platform(platform)
        if existing:
            existing.token_type = token_type
            existing.issued_at = issued_at
            existing.client_id = client_id
            existing.access_token = access_token
            existing.expires_in = expires_in
            await self.db.commit()
            await self.db.refresh(existing)
            return existing

        token = CarrierToken(
            platform=platform,
            token_type=token_type,
            issued_at=issued_at,
            client_id=client_id,
            access_token=access_token,
            expires_in=expires_in,
        )
        self.db.add(token)
        await self.db.commit()
        await self.db.refresh(token)
        return token
