"""Tests for LLM status system API."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.core.llm import reset_llm_status_cache
from app.schemas.llm import LLMMode


def test_mock_llm_status(seeded_client: TestClient, test_settings: Settings):
    response = seeded_client.get("/api/v1/system/llm-status")
    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == LLMMode.MOCK.value
    assert payload["available"] is True
    assert "super-secret" not in str(payload)


def test_safe_qwen_unavailable_response(client: TestClient, test_settings: Settings):
    reset_llm_status_cache()
    qwen_settings = test_settings.model_copy(update={"mock_llm_mode": False})
    client.app.dependency_overrides[get_settings] = lambda: qwen_settings
    with patch("app.core.llm.check_qwen_availability", return_value=(False, "Connection refused")):
        response = client.get("/api/v1/system/llm-status")
    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == LLMMode.QWEN.value
    assert payload["available"] is False
    assert payload["error_message"] is not None
    reset_llm_status_cache()


def test_no_credential_leakage(client: TestClient, test_settings: Settings):
    secret_settings = test_settings.model_copy(
        update={
            "mock_llm_mode": True,
            "qwen_api_key": "must-not-appear",
        }
    )
    client.app.dependency_overrides[get_settings] = lambda: secret_settings
    response = client.get("/api/v1/system/llm-status")
    assert "must-not-appear" not in response.text
