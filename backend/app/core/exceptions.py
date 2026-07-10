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
