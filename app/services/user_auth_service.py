"""JWT login and refresh-token rotation."""

from datetime import datetime, timezone

from fastapi import HTTPException, status

from app.core.config import settings
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
    parse_expires_to_seconds,
    refresh_token_expiry,
)
from app.repositories import RefreshTokenRepository
from app.schemas import TokenPairResponse, UserPayload
from app.services.user_service import UserService


class UserAuthService:
    """Issues JWT access tokens and manages refresh-token rotation."""

    def __init__(
        self,
        user_service: UserService,
        refresh_token_repository: RefreshTokenRepository,
    ):
        self.user_service = user_service
        self.refresh_token_repository = refresh_token_repository

    def login(self, user: UserPayload) -> TokenPairResponse:
        return self._issue_token_pair(user)

    def refresh(self, refresh_token: str) -> TokenPairResponse:
        token_hash = hash_refresh_token(refresh_token)
        record = self.refresh_token_repository.find_by_hash(token_hash)
        if record is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or revoked refresh token",
            )

        if record.expires_at < datetime.now(timezone.utc):
            self.refresh_token_repository.delete(record)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired",
            )

        # One-time use: delete before issuing a new pair (rotation).
        self.refresh_token_repository.delete(record)
        user = UserPayload(
            id=record.user.id,
            email=record.user.email,
            roles=record.user.roles,
        )
        return self._issue_token_pair(user)

    def _issue_token_pair(self, user: UserPayload) -> TokenPairResponse:
        payload = {
            "sub": user.id,
            "email": user.email,
            "roles": user.roles,
            "type": "access",  # Distinguishes access tokens from any future JWT types
        }
        access_token = create_access_token(payload)
        refresh_token_raw = generate_refresh_token()
        refresh_token_hash = hash_refresh_token(refresh_token_raw)
        self.refresh_token_repository.create(
            user_id=user.id,
            token_hash=refresh_token_hash,
            expires_at=refresh_token_expiry(),
        )
        expires_in = parse_expires_to_seconds(settings.JWT_ACCESS_EXPIRES)
        return TokenPairResponse(
            access_token=access_token,
            refresh_token=refresh_token_raw,
            expires_in=expires_in,
        )
