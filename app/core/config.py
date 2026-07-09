"""Application settings loaded from environment variables and .env file."""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    DATABASE_URL: str

    UPS_API_BASE_URL: str
    UPS_OAUTH_URL: Optional[str] = None
    UPS_RATING_API_VERSION: str = "v2409"
    UPS_USERNAME: str
    UPS_PASSWORD: str
    UPS_MERCHANT_ID: str = ""
    UPS_TRANSACTION_SRC: str = "testing"

    JWT_ACCESS_SECRET: str
    JWT_ACCESS_EXPIRES: str = "15m"
    JWT_REFRESH_DAYS: int = 7

    # Connection pool tuning (PostgreSQL / CockroachDB only).
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_RECYCLE: int = 3600

    # Optional Redis URL for carrier-token caching (falls back to DB if unset).
    REDIS_URL: Optional[str] = None

    @property
    def async_database_url(self) -> str:
        url = self.DATABASE_URL
        if "+asyncpg" in url or "+aiosqlite" in url:
            return url
        if url.startswith("sqlite://"):
            return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url

    @property
    def sync_database_url(self) -> str:
        """Sync driver URL for Alembic migrations."""
        url = self.DATABASE_URL
        if url.startswith("sqlite+aiosqlite://"):
            return url.replace("sqlite+aiosqlite://", "sqlite://", 1)
        if url.startswith("postgresql+asyncpg://"):
            return url.replace("postgresql+asyncpg://", "postgresql://", 1)
        return url

    @property
    def ups_oauth_url(self) -> str:
        # UPS_OAUTH_URL can override the default path derived from UPS_API_BASE_URL.
        if self.UPS_OAUTH_URL:
            return self.UPS_OAUTH_URL
        return f"{self.UPS_API_BASE_URL}/security/v1/oauth/token"


@lru_cache()
def get_settings() -> Settings:
    # Cached so settings are read once per process.
    return Settings()


settings = get_settings()
