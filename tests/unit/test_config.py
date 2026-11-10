"""Tests for core configuration."""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from enterprise_ai.core.config import Settings


class TestSettings:
    """Tests for the Settings class."""

    def test_default_settings(self):
        """Test that default settings load correctly."""
        settings = Settings(
            _env_file=None,  # Don't read .env file during tests
        )
        assert settings.app_name == "Enterprise GenAI Data Intelligence Platform"
        assert settings.app_env == "development"
        assert settings.app_debug is True
        assert settings.db_host == "localhost"
        assert settings.db_port == 5433

    def test_database_url_async(self):
        """Test async database URL generation."""
        settings = Settings(
            db_user="myuser",
            db_password="mypass",
            db_host="myhost",
            db_port=5433,
            db_name="mydb",
            _env_file=None,
        )
        assert settings.database_url == "postgresql+asyncpg://myuser:mypass@myhost:5433/mydb"

    def test_database_url_sync(self):
        """Test sync database URL generation."""
        settings = Settings(
            db_user="myuser",
            db_password="mypass",
            db_host="myhost",
            db_port=5433,
            db_name="mydb",
            _env_file=None,
        )
        assert settings.database_url_sync == "postgresql://myuser:mypass@myhost:5433/mydb"

    def test_database_url_override_is_normalized_and_masked(self):
        """Normalize standard PostgreSQL URLs and keep passwords out of reprs."""
        secret_url = "postgresql://user:top-secret@db.example/test"
        settings = Settings(DATABASE_URL=secret_url, _env_file=None)
        assert settings.database_url == "postgresql+asyncpg://user:top-secret@db.example/test"
        assert "top-secret" not in repr(settings)

    def test_invalid_database_url_override(self):
        """Reject non-PostgreSQL database connection URLs."""
        with pytest.raises(ValidationError):
            Settings(DATABASE_URL="sqlite:///tmp/test.db", _env_file=None)

    def test_is_production(self):
        """Test production detection."""
        dev = Settings(app_env="development", _env_file=None)
        assert dev.is_production is False

        prod = Settings(app_env="production", jwt_secret_key="x" * 32, _env_file=None)
        assert prod.is_production is True

    def test_invalid_app_env(self):
        """Test that invalid app_env raises ValidationError."""
        with pytest.raises(ValidationError):
            Settings(app_env="invalid", _env_file=None)

    def test_invalid_log_level(self):
        """Test that invalid log level raises ValidationError."""
        with pytest.raises(ValidationError):
            Settings(app_log_level="INVALID", _env_file=None)

    def test_valid_log_levels(self):
        """Test all valid log levels."""
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            settings = Settings(app_log_level=level, _env_file=None)
            assert settings.app_log_level == level

    def test_log_level_case_insensitive(self):
        """Test that log level validation is case-insensitive."""
        settings = Settings(app_log_level="debug", _env_file=None)
        assert settings.app_log_level == "DEBUG"

    def test_app_env_is_case_insensitive(self):
        """Normalize environment values before validating supported choices."""
        settings = Settings(app_env=" Production ", jwt_secret_key="x" * 32, _env_file=None)
        assert settings.app_env == "production"

    def test_production_requires_strong_jwt_secret(self):
        """Reject missing or short JWT secrets in production."""
        with pytest.raises(ValidationError):
            Settings(app_env="production", _env_file=None)
        with pytest.raises(ValidationError):
            Settings(app_env="production", jwt_secret_key="short", _env_file=None)

    def test_env_override(self):
        """Test that environment variables override defaults."""
        with patch.dict(os.environ, {"APP_NAME": "Custom App", "DB_PORT": "5433"}):
            settings = Settings(_env_file=None)
            assert settings.app_name == "Custom App"
            assert settings.db_port == 5433

    def test_optional_fields_none(self):
        """Test that optional fields default to None."""
        settings = Settings(_env_file=None)
        assert settings.openai_api_key is None
        assert settings.google_api_key is None
        assert settings.aws_s3_bucket is None

    def test_embedding_defaults(self):
        """Test embedding configuration defaults."""
        settings = Settings(_env_file=None)
        assert settings.embedding_provider == "ollama"
        assert settings.embedding_model == "nomic-embed-text"
        assert settings.embedding_dimension == 768

    def test_embedding_model_environment_override(self):
        """Support the explicit Ollama embedding variable."""
        with patch.dict(os.environ, {"OLLAMA_EMBEDDING_MODEL": "custom-embed"}):
            settings = Settings(_env_file=None)
        assert settings.embedding_model == "custom-embed"

    def test_rag_defaults(self):
        """Test RAG configuration defaults."""
        settings = Settings(_env_file=None)
        assert settings.rag_chunk_size == 1000
        assert settings.rag_chunk_overlap == 200
        assert settings.rag_top_k == 10
        assert settings.rag_rerank_top_n == 5

    def test_jwt_defaults(self):
        """Test JWT configuration defaults."""
        settings = Settings(_env_file=None)
        assert settings.jwt_algorithm == "HS256"
        assert settings.jwt_access_token_expire_minutes == 30
        assert settings.jwt_refresh_token_expire_days == 7
