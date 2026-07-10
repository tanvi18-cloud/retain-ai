"""Customer persistence operations."""

from sqlalchemy import or_
from sqlmodel import Session, select

from app.core.exceptions import ResourceNotFoundError
from app.models.customer import Customer
from app.models.enums import CustomerSegment
from app.schemas.common import PaginatedResponse
from app.schemas.customers import CustomerDetail, CustomerSummary
from app.services.repository_utils import count_query, paginate_offset, validate_pagination


def _to_summary(customer: Customer) -> CustomerSummary:
    return CustomerSummary.model_validate(customer)


def _to_detail(customer: Customer) -> CustomerDetail:
    return CustomerDetail.model_validate(customer)


class CustomerRepository:
    """Data access for customer records."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, customer_id: str) -> CustomerDetail:
        """Return a customer by ID or raise when not found."""
        customer = self.session.get(Customer, customer_id)
        if customer is None:
            raise ResourceNotFoundError(
                code="CUSTOMER_NOT_FOUND",
                message=f"Customer {customer_id} was not found",
            )
        return _to_detail(customer)

    def count_customers(
        self,
        *,
        segment: CustomerSegment | None = None,
        search: str | None = None,
    ) -> int:
        """Count customers matching optional filters."""
        statement = select(Customer)
        statement = self._apply_filters(statement, segment=segment, search=search)
        return count_query(self.session, statement)

    def list_customers(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        segment: CustomerSegment | None = None,
        search: str | None = None,
    ) -> PaginatedResponse[CustomerSummary]:
        """Return a paginated list of customers."""
        validate_pagination(page, page_size)
        statement = select(Customer).order_by(Customer.customer_id)
        statement = self._apply_filters(statement, segment=segment, search=search)
        total = count_query(self.session, statement)
        customers = self.session.exec(
            statement.offset(paginate_offset(page, page_size)).limit(page_size)
        ).all()
        return PaginatedResponse.build(
            items=[_to_summary(customer) for customer in customers],
            total=total,
            page=page,
            page_size=page_size,
        )

    @staticmethod
    def _apply_filters(statement, *, segment: CustomerSegment | None, search: str | None):
        if segment is not None:
            statement = statement.where(Customer.segment == segment)
        if search:
            trimmed = search.strip()
            statement = statement.where(
                or_(
                    Customer.customer_id.contains(trimmed),
                    Customer.full_name.ilike(f"%{trimmed}%"),
                )
            )
        return statement
