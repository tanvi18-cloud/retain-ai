"""Shared API schema utilities, validators, and response envelopes."""

import math
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


def validate_score(value: float) -> float:
    """Validate a score is within the inclusive 0-100 range."""
    if value < 0 or value > 100:
        raise ValueError("Score must be between 0 and 100")
    return value


def validate_confidence(value: float) -> float:
    """Validate a confidence value is within the inclusive 0-1 range."""
    if value < 0 or value > 1:
        raise ValueError("Confidence must be between 0 and 1")
    return value


def validate_non_negative_amount(value: float) -> float:
    """Validate a monetary amount is non-negative."""
    if value < 0:
        raise ValueError("Monetary value must be non-negative")
    return value


def validate_email_address(value: str) -> str:
    """Validate a basic email address format."""
    normalized = value.strip()
    if "@" not in normalized or "." not in normalized.split("@")[-1]:
        raise ValueError("Invalid email address")
    return normalized


class APIModel(BaseModel):
    """Base Pydantic model for API schemas."""

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)


class PaginationParams(APIModel):
    """Validated pagination query parameters."""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class PaginatedResponse(APIModel, Generic[T]):
    """Standard paginated list response envelope."""

    items: list[T]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    pages: int = Field(ge=0)

    @classmethod
    def build(
        cls,
        *,
        items: list[T],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaginatedResponse[T]":
        """Build a paginated response with computed page count."""
        pages = math.ceil(total / page_size) if total > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )


class ApiError(APIModel):
    """Structured API error payload."""

    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ApiErrorResponse(APIModel):
    """Standard API error response envelope."""

    error: ApiError
