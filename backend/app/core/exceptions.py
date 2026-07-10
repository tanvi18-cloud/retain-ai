"""Domain-specific exception types."""

from typing import Any


class DomainError(Exception):
    """Base class for application domain errors."""

    def __init__(
        self,
        *,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
        status_code: int = 400,
    ) -> None:
        self.code = code
        self.message = message
        self.details = details or {}
        self.status_code = status_code
        super().__init__(message)


class ResourceNotFoundError(DomainError):
    """Raised when a requested resource does not exist."""

    def __init__(
        self,
        *,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(code=code, message=message, details=details, status_code=404)


class InvalidPaginationError(DomainError):
    """Raised when pagination parameters are invalid."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            code="INVALID_PAGINATION",
            message=message,
            details=details,
            status_code=400,
        )


class RepositoryError(DomainError):
    """Raised when a persistence operation fails unexpectedly."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            code="REPOSITORY_ERROR",
            message=message,
            details=details,
            status_code=500,
        )


class InvalidScoreInputError(DomainError):
    """Raised when scoring inputs are invalid."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            code="INVALID_SCORE_INPUT",
            message=message,
            details=details,
            status_code=400,
        )


class InvalidFinancialInputError(DomainError):
    """Raised when financial calculation inputs are invalid."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            code="INVALID_FINANCIAL_INPUT",
            message=message,
            details=details,
            status_code=400,
        )


class UnsupportedSortFieldError(DomainError):
    """Raised when an unsupported sort field is requested."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            code="UNSUPPORTED_SORT_FIELD",
            message=message,
            details=details,
            status_code=400,
        )


class UnsupportedFilterError(DomainError):
    """Raised when an unsupported filter value is requested."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            code="UNSUPPORTED_FILTER",
            message=message,
            details=details,
            status_code=400,
        )


class EventRetryNotAllowedError(DomainError):
    """Raised when an event cannot be retried."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            code="EVENT_RETRY_NOT_ALLOWED",
            message=message,
            details=details,
            status_code=400,
        )


class UnsupportedEventTypeError(DomainError):
    """Raised when an event type is not supported."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            code="UNSUPPORTED_EVENT_TYPE",
            message=message,
            details=details,
            status_code=422,
        )


class LLMConfigurationError(DomainError):
    """Raised when LLM configuration is invalid."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            code="LLM_CONFIGURATION_ERROR",
            message=message,
            details=details,
            status_code=500,
        )


class AgentExecutionError(DomainError):
    """Raised when an agent fails to produce valid structured output."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            code="AGENT_EXECUTION_ERROR",
            message=message,
            details=details,
            status_code=502,
        )


class AgentValidationFailedError(DomainError):
    """Raised when agent output fails policy validation."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            code="AGENT_VALIDATION_FAILED",
            message=message,
            details=details,
            status_code=422,
        )
