"""LLM configuration and status schemas."""

from datetime import datetime
from enum import StrEnum

from app.schemas.common import APIModel


class LLMMode(StrEnum):
    """Active LLM operating mode."""

    MOCK = "MOCK"
    QWEN = "QWEN"


class LLMStatus(APIModel):
    """Safe LLM subsystem status for operators."""

    mode: LLMMode
    configured_model: str
    endpoint_host: str
    available: bool
    last_checked_at: datetime
    error_message: str | None = None
    crewai_version: str | None = None
