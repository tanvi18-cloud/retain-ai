"""Safe chat tool tests."""

import pytest
from sqlmodel import Session

from app.core.exceptions import ResourceNotFoundError
from app.tools import chat_tools


def test_get_chat_customer_summary(agent_seeded_session: Session):
    summary = chat_tools.get_chat_customer_summary(agent_seeded_session, "C001")
    assert summary.customer_id == "C001"
    assert summary.priority_score >= 0


def test_get_chat_customer_risk_explanation(agent_seeded_session: Session):
    risk = chat_tools.get_chat_customer_risk_explanation(agent_seeded_session, "C001")
    assert risk.churn_score >= 0
    assert risk.primary_signal


def test_get_chat_customer_eligibility_c004(agent_seeded_session: Session):
    elig = chat_tools.get_chat_customer_eligibility(agent_seeded_session, "C004")
    rejected_ids = {item["offer_id"] for item in elig.rejected_offers}
    assert "OFFER-HL-FEE" in rejected_ids


def test_compare_customers(agent_seeded_session: Session):
    rows = chat_tools.compare_customers(agent_seeded_session, ["C001", "C008"])
    assert len(rows) == 2
    assert {row.customer_id for row in rows} == {"C001", "C008"}


def test_search_home_loan_triggers(agent_seeded_session: Session):
    matches = chat_tools.search_customers_by_trigger(agent_seeded_session, "HOME_LOAN")
    assert any(match.customer_id == "C001" for match in matches)


def test_priority_customers_excludes_no_action(agent_seeded_session: Session):
    customers = chat_tools.get_chat_priority_customers(agent_seeded_session, limit=10)
    assert all(item.decision != "NO_ACTION" for item in customers)


def test_missing_customer(agent_seeded_session: Session):
    with pytest.raises(ResourceNotFoundError):
        chat_tools.get_chat_customer_summary(agent_seeded_session, "C999")


def test_portfolio_summary(agent_seeded_session: Session):
    summary = chat_tools.get_chat_portfolio_summary(agent_seeded_session)
    assert summary.total_customers == 10
    assert summary.total_revenue_at_risk >= 0


def test_data_freshness(agent_seeded_session: Session):
    freshness = chat_tools.get_customer_data_freshness(agent_seeded_session, "C001")
    assert "core_banking" in freshness.sources
