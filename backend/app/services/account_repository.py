"""Account persistence operations."""

from sqlmodel import Session, select

from app.models.account import Account
from app.schemas.accounts import AccountDetail


def _to_detail(account: Account) -> AccountDetail:
    return AccountDetail(
        account_id=account.id,
        customer_id=account.customer_id,
        account_type=account.account_type,
        current_balance=account.current_balance,
        average_balance_90d=account.average_balance_90d,
        salary_account=account.salary_account,
        status=account.status,
        fixed_deposit_maturity_date=account.fixed_deposit_maturity_date,
        created_at=account.created_at,
        updated_at=account.updated_at,
    )


class AccountRepository:
    """Data access for customer account records."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def list_by_customer(self, customer_id: str) -> list[AccountDetail]:
        """Return all accounts for a customer ordered by account type."""
        statement = (
            select(Account)
            .where(Account.customer_id == customer_id)
            .order_by(Account.account_type)
        )
        accounts = self.session.exec(statement).all()
        return [_to_detail(account) for account in accounts]
