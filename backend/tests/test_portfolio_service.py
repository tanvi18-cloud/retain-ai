"""Portfolio service tests."""

import pytest
from sqlmodel import Session

from app.models.enums import RecommendationDecision
from app.seed.seed_database import seed_database
from app.services.portfolio_service import PortfolioService


@pytest.fixture
def seeded_portfolio_session(db_session: Session) -> Session:
    seed_database(db_session, skip_if_complete=False)
    return db_session


@pytest.fixture
def portfolio_service(seeded_portfolio_session: Session) -> PortfolioService:
    return PortfolioService(seeded_portfolio_session)


def test_summary_has_ten_customers(portfolio_service: PortfolioService):
    summary = portfolio_service.get_summary()
    assert summary.total_customers == 10
    total_decisions = (
        summary.immediate_intervention_count
        + summary.review_count
        + summary.monitor_count
        + summary.no_action_count
    )
    assert total_decisions == 10


def test_portfolio_sorting(portfolio_service: PortfolioService):
    result = portfolio_service.list_customers(sort_by="priority_score", sort_order="desc")
    scores = [row.priority_score for row in result.items]
    assert scores == sorted(scores, reverse=True)


def test_portfolio_filter_decision(portfolio_service: PortfolioService):
    result = portfolio_service.list_customers(decision=RecommendationDecision.NO_ACTION)
    assert all(row.decision == RecommendationDecision.NO_ACTION for row in result.items)
    assert any(row.customer_id == "C010" for row in result.items)


def test_portfolio_minimum_priority(portfolio_service: PortfolioService):
    result = portfolio_service.list_customers(minimum_priority=70)
    assert all(row.priority_score >= 70 for row in result.items)


def test_portfolio_pagination(portfolio_service: PortfolioService):
    result = portfolio_service.list_customers(page=1, page_size=3)
    assert len(result.items) == 3
    assert result.total == 10
    assert result.pages == 4


def test_portfolio_search(portfolio_service: PortfolioService):
    result = portfolio_service.list_customers(search="Ananya")
    assert result.total == 1
    assert result.items[0].customer_id == "C001"


def test_revenue_totals_non_negative(portfolio_service: PortfolioService):
    summary = portfolio_service.get_summary()
    assert summary.total_revenue_at_risk >= 0
