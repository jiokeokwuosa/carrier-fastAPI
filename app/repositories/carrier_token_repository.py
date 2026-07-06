"""Database access for cached carrier OAuth tokens (one row per platform)."""

from typing import Optional

from sqlalchemy.orm import Session

from app.models import CarrierToken


class CarrierTokenRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_by_platform(self, platform: str) -> Optional[CarrierToken]:
        return (
            self.db.query(CarrierToken)
            .filter(CarrierToken.platform == platform)
            .first()
        )

    def upsert(
        self,
        platform: str,
        token_type: str,
        issued_at: str,
        client_id: str,
        access_token: str,
        expires_in: str,
    ) -> CarrierToken:
        # One token per platform (e.g. "UPS"); update in place on refresh.
        existing = self.find_by_platform(platform)
        if existing:
            existing.token_type = token_type
            existing.issued_at = issued_at
            existing.client_id = client_id
            existing.access_token = access_token
            existing.expires_in = expires_in
            self.db.commit()
            self.db.refresh(existing)
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
        self.db.commit()
        self.db.refresh(token)
        return token
