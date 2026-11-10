"""Validated application configuration loaded from environment variables."""

from functools import lru_cache
from typing import Literal
from urllib.parse import quote

from pydantic import AliasChoices, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings; secret values are masked in model representations."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_ignore_empty=True,
        populate_by_name=True,
    )

    app_name: str = "Enterprise GenAI Data Intelligence Platform"
    app_env: Literal["development", "staging", "production"] = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = Field(default=8000, ge=1, le=65535)
    app_log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"
    app_secret_key: SecretStr = Field(default=SecretStr(""), repr=False)

    database_url_override: SecretStr | None = Field(
        default=None,
        validation_alias="DATABASE_URL",
        repr=False,
    )
    db_host: str = "localhost"
    db_port: int = Field(default=5433, ge=1, le=65535)
    db_user: str = "genai_user"
    db_password: SecretStr = Field(default=SecretStr(""), repr=False)
    db_name: str = "genai_platform"
    db_pool_size: int = Field(default=5, ge=1)
    db_max_overflow: int = Field(default=10, ge=0)

    storage_backend: Literal["local", "s3"] = "local"
    storage_local_path: str = "./data/uploads"
    aws_s3_bucket: str | None = None
    aws_region: str = "us-east-1"

    llm_provider: Literal["ollama", "openai", "bedrock", "gemini"] = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_chat_model: str = "llama3.2:1b"
    openai_api_key: SecretStr | None = Field(default=None, repr=False)
    google_api_key: SecretStr | None = Field(default=None, repr=False)

    embedding_provider: Literal["ollama", "bedrock", "openai", "google"] = "ollama"
    embedding_model: str = Field(
        default="nomic-embed-text",
        validation_alias=AliasChoices("OLLAMA_EMBEDDING_MODEL", "EMBEDDING_MODEL"),
    )
    embedding_dimension: int = Field(default=768, ge=1)

    rag_chunk_size: int = Field(default=1000, ge=1)
    rag_chunk_overlap: int = Field(default=200, ge=0)
    rag_top_k: int = Field(default=10, ge=1)
    rag_rerank_top_n: int = Field(default=5, ge=1)

    jwt_secret_key: SecretStr = Field(default=SecretStr(""), repr=False)
    jwt_algorithm: Literal["HS256", "HS384", "HS512"] = "HS256"
    jwt_access_token_expire_minutes: int = Field(default=30, ge=1)
    jwt_refresh_token_expire_days: int = Field(default=7, ge=1)

    pii_detection_enabled: bool = True
    pii_masking_enabled: bool = True

    @property
    def database_url(self) -> str:
        """Build the async database URL; callers must treat the result as secret."""
        if self.database_url_override:
            url = self.database_url_override.get_secret_value()
            if url.startswith("postgres://"):
                return url.replace("postgres://", "postgresql+asyncpg://", 1)
            if url.startswith("postgresql://"):
                return url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return url

        username = quote(self.db_user, safe="")
        password = quote(self.db_password.get_secret_value(), safe="")
        database = quote(self.db_name, safe="")
        return f"postgresql+asyncpg://{username}:{password}@{self.db_host}:{self.db_port}/{database}"

    @property
    def database_url_sync(self) -> str:
        """Return the synchronous PostgreSQL URL used by migration tooling."""
        return self.database_url.replace("postgresql+asyncpg://", "postgresql://", 1)

    @property
    def is_production(self) -> bool:
        """Whether the application is running in production mode."""
        return self.app_env == "production"

    @field_validator("app_env", mode="before")
    @classmethod
    def normalize_app_env(cls, value: object) -> object:
        """Normalize the environment name before literal validation."""
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator("app_log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        """Normalize and validate the configured standard-library log level."""
        normalized = value.upper()
        if normalized not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError("app_log_level must be DEBUG, INFO, WARNING, ERROR, or CRITICAL")
        return normalized

    @field_validator("ollama_base_url")
    @classmethod
    def validate_ollama_base_url(cls, value: str) -> str:
        """Require an HTTP(S) base URL for the local Ollama service."""
        if not value.startswith(("http://", "https://")):
            raise ValueError("ollama_base_url must use http or https")
        return value.rstrip("/")

    @field_validator("database_url_override")
    @classmethod
    def validate_database_url(cls, value: SecretStr | None) -> SecretStr | None:
        """Accept PostgreSQL URLs only when a complete URL override is supplied."""
        if value is not None and value.get_secret_value():
            if not value.get_secret_value().startswith(("postgres://", "postgresql://", "postgresql+asyncpg://")):
                raise ValueError("DATABASE_URL must be a PostgreSQL connection URL")
        return value

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        """Reject missing or weak JWT secrets in production."""
        if self.is_production and len(self.jwt_secret_key.get_secret_value()) < 32:
            raise ValueError("JWT_SECRET_KEY must contain at least 32 characters in production")
        return self


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide validated settings instance."""
    return Settings()
