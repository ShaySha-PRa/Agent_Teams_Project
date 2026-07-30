"""Application configuration via pydantic-settings.

Environment variables are loaded from .env (or system env) and validated here.
Secrets (API keys, DB passwords) MUST be set via environment, never hardcoded.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralised, typed settings for the entire backend."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────
    APP_NAME: str = Field(default="Agent Document Review", alias="APP_NAME")
    APP_ENV: Literal["development", "staging", "production"] = Field(
        default="development", alias="APP_ENV"
    )
    APP_PORT: int = Field(default=8000, alias="APP_PORT")
    DEBUG: bool = Field(default=True, alias="DEBUG")

    # ── Database ─────────────────────────────────────────────────────
    DATABASE_URL: SecretStr = Field(
        default=SecretStr("sqlite+aiosqlite:///./docreview.db"),
        alias="DATABASE_URL",
    )

    @property
    def database_url(self) -> str:
        return self.DATABASE_URL.get_secret_value()

    # ── AI / LLM ─────────────────────────────────────────────────────
    # DeepSeek (primary model for all Agent calls)
    DEEPSEEK_API_KEY: SecretStr = Field(
        default=SecretStr(""),
        alias="DEEPSEEK_API_KEY",
    )
    DEEPSEEK_MODEL: str = Field(default="deepseek-chat", alias="DEEPSEEK_MODEL")
    DEEPSEEK_BASE_URL: str = Field(
        default="https://api.deepseek.com/v1", alias="DEEPSEEK_BASE_URL"
    )

    @property
    def deepseek_api_key(self) -> str:
        return self.DEEPSEEK_API_KEY.get_secret_value()

    # ── JWT / Auth ───────────────────────────────────────────────────
    JWT_SECRET_KEY: SecretStr = Field(
        default=SecretStr("dev-secret-change-in-production"),
        alias="JWT_SECRET_KEY",
    )
    JWT_ALGORITHM: str = Field(default="HS256", alias="JWT_ALGORITHM")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=1440, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    @property
    def jwt_secret_key(self) -> str:
        return self.JWT_SECRET_KEY.get_secret_value()

    # ── File Storage ─────────────────────────────────────────────────
    STORAGE_BACKEND: Literal["local", "s3"] = Field(
        default="local", alias="STORAGE_BACKEND"
    )
    STORAGE_LOCAL_PATH: Path = Field(
        default=Path("./storage"), alias="STORAGE_LOCAL_PATH"
    )
    MAX_FILE_SIZE_MB: int = Field(default=50, alias="MAX_FILE_SIZE_MB")
    MAX_PAGE_COUNT: int = Field(default=200, alias="MAX_PAGE_COUNT")

    # ── CORS ─────────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        alias="CORS_ORIGINS",
    )

    # ── LangGraph Checkpointer ────────────────────────────────────────
    CHECKPOINTER_DB_URL: SecretStr | None = Field(
        default=None, alias="CHECKPOINTER_DB_URL"
    )

    @property
    def checkpointer_db_url(self) -> str | None:
        if self.CHECKPOINTER_DB_URL is None:
            return None
        return self.CHECKPOINTER_DB_URL.get_secret_value()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton of Settings (reads .env once)."""
    return Settings()
