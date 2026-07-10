"""Tests for the shared LLM factory."""

from unittest.mock import patch

import pytest

from app.core.config import Settings, get_settings
from app.core.exceptions import LLMConfigurationError
from app.core.llm import (
    create_llm,
    get_llm_mode,
    get_llm_status,
    reset_llm_status_cache,
    sanitize_endpoint_host,
)
from app.schemas.llm import LLMMode


@pytest.fixture(autouse=True)
def _reset_status_cache():
    reset_llm_status_cache()
    get_settings.cache_clear()
    yield
    reset_llm_status_cache()
    get_settings.cache_clear()


def _qwen_settings(**overrides) -> Settings:
    base = Settings.model_construct(
        app_name="RetainAI",
        app_env="test",
        database_url="sqlite:///:memory:",
        mock_llm_mode=False,
        qwen_base_url="http://localhost:9000/v1",
        qwen_model="Qwen/Qwen3-8B",
        qwen_api_key="test-key",
        qwen_temperature=0.1,
        qwen_timeout_seconds=60,
        qwen_max_retries=2,
    )
    for key, value in overrides.items():
        setattr(base, key, value)
    return base


def test_mock_mode_creates_no_network_client():
    settings = Settings(mock_llm_mode=True, database_url="sqlite:///:memory:")
    assert create_llm(settings) is None
    assert get_llm_mode(settings) == LLMMode.MOCK


def test_qwen_mode_validates_required_configuration():
    settings = _qwen_settings(qwen_base_url="")
    with pytest.raises(LLMConfigurationError):
        create_llm(settings)


def test_api_key_not_exposed_in_status():
    settings = Settings(
        mock_llm_mode=True,
        database_url="sqlite:///:memory:",
        qwen_api_key="super-secret-key",
        qwen_base_url="http://localhost:9000/v1",
    )
    status = get_llm_status(settings)
    dumped = status.model_dump_json()
    assert "super-secret-key" not in dumped
    assert status.mode == LLMMode.MOCK


def test_endpoint_host_is_sanitized():
    host = sanitize_endpoint_host("http://user:pass@localhost:9000/v1")
    assert host == "localhost:9000"
    assert "user" not in host
    assert "pass" not in host


def test_timeout_and_retries_configured():
    settings = _qwen_settings()
    llm = create_llm(settings)
    assert llm is not None
    assert llm.temperature == 0.1
    assert llm.timeout == 60
    assert settings.qwen_max_retries == 2


def test_startup_remains_available_when_qwen_is_down():
    settings = _qwen_settings(qwen_base_url="http://127.0.0.1:1/v1")
    with patch("app.core.llm.check_qwen_availability", return_value=(False, "unavailable")):
        status = get_llm_status(settings, force_refresh=True)
    assert status.available is False
    assert status.error_message is not None
