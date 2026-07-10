"""Shared repository utilities."""

from sqlmodel import Session, func, select

from app.core.exceptions import InvalidPaginationError


def validate_pagination(page: int, page_size: int) -> None:
    """Validate pagination inputs and raise a domain error when invalid."""
    if page < 1 or page_size < 1:
        raise InvalidPaginationError(
            message="Page and page_size must be positive integers",
            details={"page": page, "page_size": page_size},
        )


def paginate_offset(page: int, page_size: int) -> int:
    """Return the SQL offset for a page."""
    validate_pagination(page, page_size)
    return (page - 1) * page_size


def count_query(session: Session, statement) -> int:
    """Count rows for a select statement."""
    count_statement = select(func.count()).select_from(statement.subquery())
    result = session.exec(count_statement).one()
    return int(result)
