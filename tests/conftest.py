"""Shared test fixtures."""

from collections.abc import Generator
from unittest.mock import patch

import pytest

from enterprise_ai.core.config import Settings


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Provide test settings (no real DB needed for unit tests)."""
    return Settings(
        app_name="Test Platform",
        app_env="development",
        app_debug=True,
        db_host="localhost",
        db_port=5433,
        db_user="test_user",
        db_password="test_password",
        db_name="test_db",
        jwt_secret_key="test-jwt-secret",
        app_secret_key="test-app-secret",
        _env_file=None,
    )


@pytest.fixture
def mock_settings(test_settings: Settings) -> Generator[Settings, None, None]:
    """Patch get_settings to return test settings."""
    with patch("enterprise_ai.core.config.get_settings", return_value=test_settings):
        yield test_settings
