"""Database access for refresh tokens (stored as SHA-256 hashes)."""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session, joinedload

from app.models import RefreshToken


class RefreshTokenRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: str, token_hash: str, expires_at: datetime) -> RefreshToken:
        record = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def find_by_hash(self, token_hash: str) -> Optional[RefreshToken]:
        return (
            self.db.query(RefreshToken)
            .options(joinedload(RefreshToken.user))  # Needed when rotating tokens
            .filter(RefreshToken.token_hash == token_hash)
            .first()
        )

    def delete(self, record: RefreshToken) -> None:
        self.db.delete(record)
        self.db.commit()
