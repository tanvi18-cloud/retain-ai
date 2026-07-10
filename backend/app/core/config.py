"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app import __version__

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    """RetainAI backend settings sourced from environment or .env files."""

    model_config = SettingsConfigDict(
        env_file=(REPO_ROOT / ".env", BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(default="RetainAI", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=False, alias="DEBUG")
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    database_url: str = Field(default="sqlite:///./retain_ai.db", alias="DATABASE_URL")
    frontend_origin: str = Field(default="http://localhost:5173", alias="FRONTEND_ORIGIN")

    mock_llm_mode: bool = Field(default=True, alias="MOCK_LLM_MODE")
    qwen_base_url: str = Field(default="http://localhost:9000/v1", alias="QWEN_BASE_URL")
    qwen_api_key: str = Field(default="not-required-for-local", alias="QWEN_API_KEY")
    qwen_model: str = Field(default="Qwen/Qwen3-8B", alias="QWEN_MODEL")

    smtp_host: str = Field(default="localhost", alias="SMTP_HOST")
    smtp_port: int = Field(default=1025, alias="SMTP_PORT")
    smtp_username: str = Field(default="", alias="SMTP_USERNAME")
    smtp_password: str = Field(default="", alias="SMTP_PASSWORD")
    smtp_from: str = Field(default="retainai@example.local", alias="SMTP_FROM")
    rm_email: str = Field(default="rm@example.local", alias="RM_EMAIL")

    alert_priority_threshold: int = Field(default=70, alias="ALERT_PRIORITY_THRESHOLD")
    review_priority_threshold: int = Field(default=50, alias="REVIEW_PRIORITY_THRESHOLD")
    queue_worker_count: int = Field(default=1, alias="QUEUE_WORKER_COUNT")
    event_max_retries: int = Field(default=2, alias="EVENT_MAX_RETRIES")
    event_shutdown_timeout_seconds: int = Field(
        default=10,
        alias="EVENT_SHUTDOWN_TIMEOUT_SECONDS",
    )
    email_notifications_enabled: bool = Field(default=True, alias="EMAIL_NOTIFICATIONS_ENABLED")
    smtp_use_tls: bool = Field(default=False, alias="SMTP_USE_TLS")
    smtp_timeout_seconds: int = Field(default=10, alias="SMTP_TIMEOUT_SECONDS")
    websocket_heartbeat_seconds: int = Field(default=30, alias="WEBSOCKET_HEARTBEAT_SECONDS")

    core_banking_stale_hours: int = Field(default=72, alias="CORE_BANKING_STALE_HOURS")
    credit_profile_stale_hours: int = Field(default=168, alias="CREDIT_PROFILE_STALE_HOURS")
    bureau_trigger_stale_hours: int = Field(default=720, alias="BUREAU_TRIGGER_STALE_HOURS")
    transaction_feature_stale_hours: int = Field(
        default=48,
        alias="TRANSACTION_FEATURE_STALE_HOURS",
    )

    churn_priority_weight: float = Field(default=0.55, alias="CHURN_PRIORITY_WEIGHT")
    value_priority_weight: float = Field(default=0.45, alias="VALUE_PRIORITY_WEIGHT")
    decision_monitor_threshold: int = Field(default=30, alias="DECISION_MONITOR_THRESHOLD")

    @property
    def api_version(self) -> str:
        """Application version exposed via health and OpenAPI metadata."""
        return __version__


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
