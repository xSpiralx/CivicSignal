from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"), env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "CivicSignal API"
    environment: str = "development"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000"
    max_request_bytes: int = 1_048_576
    emergency_message: str = "Call 911 for immediate danger."
    session_cookie_name: str = "civicsignal_admin_session"
    session_absolute_seconds: int = 28_800
    session_idle_seconds: int = 1_800
    cookie_secure: bool = False
    database_url: str = Field(
        default="postgresql+asyncpg://civicsignal:local-development-only@localhost:5432/civicsignal"
    )

    @property
    def allowed_origins(self) -> list[str]:
        return [value.strip() for value in self.cors_origins.split(",") if value.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
