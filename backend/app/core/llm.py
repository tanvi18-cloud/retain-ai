"""Shared LLM factory, availability checks, and structured agent execution."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any, TypeVar
from urllib.parse import urlparse

import httpx
from crewai import LLM, Agent, Crew, Task
from pydantic import BaseModel

from app.core.config import Settings, get_settings
from app.core.exceptions import AgentExecutionError, LLMConfigurationError
from app.schemas.llm import LLMMode, LLMStatus

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

_STATUS_CACHE: LLMStatus | None = None
_STATUS_CACHE_AT: datetime | None = None
_STATUS_CACHE_TTL_SECONDS = 30


def _utc_now() -> datetime:
    return datetime.now(UTC)


def sanitize_endpoint_host(base_url: str) -> str:
    """Return a safe host:port string without credentials or path secrets."""
    parsed = urlparse(base_url)
    host = parsed.hostname or "unknown"
    if parsed.port is not None:
        return f"{host}:{parsed.port}"
    return host


def get_llm_mode(settings: Settings | None = None) -> LLMMode:
    """Return the active LLM operating mode."""
    resolved = settings or get_settings()
    return LLMMode.MOCK if resolved.mock_llm_mode else LLMMode.QWEN


def create_llm(settings: Settings | None = None) -> LLM | None:
    """Create a CrewAI LLM instance or None in mock mode."""
    resolved = settings or get_settings()
    if resolved.mock_llm_mode:
        return None

    if not resolved.qwen_base_url.strip():
        raise LLMConfigurationError(
            message="QWEN_BASE_URL is required when MOCK_LLM_MODE=false",
            details={"mock_llm_mode": resolved.mock_llm_mode},
        )
    if not resolved.qwen_model.strip():
        raise LLMConfigurationError(
            message="QWEN_MODEL is required when MOCK_LLM_MODE=false",
            details={"mock_llm_mode": resolved.mock_llm_mode},
        )

    return LLM(
        model=resolved.qwen_model,
        base_url=resolved.qwen_base_url,
        api_key=resolved.qwen_api_key or "not-set",
        temperature=resolved.qwen_temperature,
        timeout=resolved.qwen_timeout_seconds,
        max_retries=resolved.qwen_max_retries,
    )


def check_qwen_availability(settings: Settings | None = None) -> tuple[bool, str | None]:
    """Perform a lightweight availability check against the Qwen endpoint."""
    resolved = settings or get_settings()
    if resolved.mock_llm_mode:
        return True, None

    url = resolved.qwen_base_url.rstrip("/")
    probe_url = f"{url}/models"
    headers = {"Authorization": f"Bearer {resolved.qwen_api_key}"}
    try:
        with httpx.Client(timeout=resolved.qwen_timeout_seconds) as client:
            response = client.get(probe_url, headers=headers)
            if response.status_code < 500:
                return True, None
            return False, f"Endpoint returned HTTP {response.status_code}"
    except httpx.TimeoutException:
        return False, "Qwen endpoint timed out"
    except httpx.HTTPError as exc:
        return False, f"Qwen endpoint unavailable: {exc.__class__.__name__}"


def get_llm_status(settings: Settings | None = None, *, force_refresh: bool = False) -> LLMStatus:
    """Return cached or freshly checked LLM status without exposing secrets."""
    global _STATUS_CACHE, _STATUS_CACHE_AT

    resolved = settings or get_settings()
    now = _utc_now()
    if (
        not force_refresh
        and _STATUS_CACHE is not None
        and _STATUS_CACHE_AT is not None
        and (now - _STATUS_CACHE_AT).total_seconds() < _STATUS_CACHE_TTL_SECONDS
    ):
        return _STATUS_CACHE

    mode = get_llm_mode(resolved)
    available = True
    error_message: str | None = None
    if mode == LLMMode.QWEN:
        available, error_message = check_qwen_availability(resolved)

    crewai_version: str | None = None
    try:
        import crewai

        crewai_version = crewai.__version__
    except Exception:
        crewai_version = None

    status = LLMStatus(
        mode=mode,
        configured_model=resolved.qwen_model,
        endpoint_host=sanitize_endpoint_host(resolved.qwen_base_url),
        available=available,
        last_checked_at=now,
        error_message=error_message,
        crewai_version=crewai_version,
    )
    _STATUS_CACHE = status
    _STATUS_CACHE_AT = now
    return status


def create_agent(
    *,
    role: str,
    goal: str,
    backstory: str,
    tools: list[Any],
    settings: Settings | None = None,
) -> Agent:
    """Create a CrewAI agent configured for RetainAI guardrails."""
    resolved = settings or get_settings()
    llm = create_llm(resolved)
    return Agent(
        role=role,
        goal=goal,
        backstory=backstory,
        tools=tools,
        llm=llm,
        verbose=resolved.agent_verbose,
        max_iter=resolved.agent_max_iterations,
        allow_delegation=False,
    )


def execute_structured_task(
    *,
    agent: Agent,
    description: str,
    expected_output: str,
    output_model: type[T],
    inputs: dict[str, Any] | None = None,
    settings: Settings | None = None,
) -> T:
    """Run a single-agent CrewAI task and parse structured Pydantic output."""
    resolved = settings or get_settings()
    task = Task(
        description=description,
        expected_output=expected_output,
        agent=agent,
        output_pydantic=output_model,
    )
    crew = Crew(
        agents=[agent],
        tasks=[task],
        verbose=resolved.agent_verbose,
    )
    try:
        result = crew.kickoff(inputs=inputs or {})
    except Exception as exc:
        logger.exception("CrewAI agent execution failed")
        raise AgentExecutionError(
            message="Agent execution failed after retries",
            details={"error_type": exc.__class__.__name__},
        ) from exc

    parsed = getattr(result, "pydantic", None)
    if parsed is not None:
        return parsed

    tasks_output = getattr(result, "tasks_output", None) or []
    if tasks_output:
        first = tasks_output[0]
        task_pydantic = getattr(first, "pydantic", None)
        if task_pydantic is not None:
            return task_pydantic
        raw_json = getattr(first, "json_dict", None)
        if raw_json:
            return output_model.model_validate(raw_json)

    raw = getattr(result, "raw", None)
    if raw:
        try:
            return output_model.model_validate_json(str(raw))
        except Exception as exc:
            raise AgentExecutionError(
                message="Unable to parse structured agent output",
                details={"raw_preview": str(raw)[:200]},
            ) from exc

    raise AgentExecutionError(
        message="Agent did not return structured output",
        details={"output_model": output_model.__name__},
    )


def reset_llm_status_cache() -> None:
    """Clear cached LLM status (used in tests)."""
    global _STATUS_CACHE, _STATUS_CACHE_AT
    _STATUS_CACHE = None
    _STATUS_CACHE_AT = None
