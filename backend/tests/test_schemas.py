"""Schema validation tests."""

import pytest
from pydantic import ValidationError

from app.core.exceptions import InvalidPaginationError
from app.schemas.common import PaginatedResponse, PaginationParams
from app.services.repository_utils import validate_pagination


def test_pagination_params_require_positive_values() -> None:
    """PaginationParams rejects non-positive page values."""
    with pytest.raises(ValidationError):
        PaginationParams(page=0, page_size=20)


def test_paginated_response_builds_page_count() -> None:
    """PaginatedResponse computes total pages from total and page size."""
    response = PaginatedResponse.build(
        items=["a", "b"],
        total=45,
        page=2,
        page_size=20,
    )

    assert response.items == ["a", "b"]
    assert response.total == 45
    assert response.page == 2
    assert response.page_size == 20
    assert response.pages == 3


def test_validate_pagination_raises_domain_error() -> None:
    """Repository pagination validation raises InvalidPaginationError."""
    with pytest.raises(InvalidPaginationError) as exc_info:
        validate_pagination(page=0, page_size=10)

    assert exc_info.value.code == "INVALID_PAGINATION"
