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
