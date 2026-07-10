"""Tests for application configuration."""

from app.core.config import Settings, get_settings


def test_settings_load_with_defaults() -> None:
    """Settings can be instantiated with default values."""
    settings = Settings()

    assert settings.app_name == "RetainAI"
    assert settings.app_env == "development"
    assert settings.frontend_origin == "http://localhost:5173"
    assert settings.mock_llm_mode is True


def test_get_settings_is_cached() -> None:
    """get_settings returns the same cached instance."""
    get_settings.cache_clear()
    first = get_settings()
    second = get_settings()
    assert first is second
