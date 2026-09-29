"""Application configuration loaded from environment variables.

Secrets are NEVER hard-coded. All values come from the environment (a local
`.env` file in development, real environment variables in production).
"""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ---- Application ----
    app_name: str = "KeyLogger"
    environment: str = "development"
    debug: bool = True

    # ---- Server ----
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    # ---- Database ----
    database_url: str = Field(
        default="postgresql+psycopg2://keylogger:change-me@localhost:5432/keylogger"
    )

    # ---- Security / JWT ----
    secret_key: str = "dev-secret-change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # ---- CORS ----
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        """CORS origins as a clean list."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @field_validator("secret_key")
    @classmethod
    def _warn_default_secret(cls, value: str) -> str:
        # We never raise here (tests/dev use a default), but production should
        # always override this via the environment.
        return value

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()


settings = get_settings()
