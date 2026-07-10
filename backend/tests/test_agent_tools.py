"""Tests for read-only CrewAI tools."""

import json

from sqlmodel import select

from app.models.customer import Customer
from app.models.offer import Offer
from app.tools.customer_tools import get_customer_360
from app.tools.interaction_tools import get_customer_financial_options, get_customer_interactions
from app.tools.offer_tools import get_eligible_offers, get_offer_by_id
from app.tools.portfolio_tools import get_portfolio_metrics, get_priority_customers
from app.tools.scoring_tools import get_calculated_scores


def test_customer_360_tool(agent_seeded_engine):
    payload = json.loads(get_customer_360.run("C001"))
    assert payload["customer_id"] == "C001"
    assert payload["account_count"] >= 1
    assert "data_warnings" in payload


def test_scoring_tool(agent_seeded_engine):
    payload = json.loads(get_calculated_scores.run("C001"))
    assert payload["customer_id"] == "C001"
    assert 0 <= payload["churn_score"] <= 100
    assert payload["decision"] in {"RETAIN", "REVIEW", "MONITOR", "NO_ACTION"}


def test_eligible_offers_tool(agent_seeded_engine):
    payload = json.loads(get_eligible_offers.run("C001"))
    assert payload["customer_id"] == "C001"
    assert isinstance(payload["eligible_offers"], list)


def test_offer_lookup_tool(agent_seeded_engine):
    payload = json.loads(get_offer_by_id.run("OFFER-HL-FEE"))
    assert payload["offer_id"] == "OFFER-HL-FEE"
    assert payload["active"] is True


def test_interactions_tool(agent_seeded_engine):
    payload = json.loads(get_customer_interactions.run("C001"))
    assert payload["customer_id"] == "C001"
    assert isinstance(payload["interactions"], list)


def test_portfolio_metrics_tool(agent_seeded_engine):
    payload = json.loads(get_portfolio_metrics.run())
    assert payload["total_customers"] == 10
    assert payload["total_revenue_at_risk"] >= 0


def test_priority_customers_tool(agent_seeded_engine):
    payload = json.loads(get_priority_customers.run(5))
    assert len(payload["customers"]) == 5
    assert payload["customers"][0]["priority_score"] >= payload["customers"][-1]["priority_score"]


def test_financial_options_tool(agent_seeded_engine):
    payload = json.loads(get_customer_financial_options.run("C001"))
    assert payload["customer_id"] == "C001"
    assert isinstance(payload["options"], list)


def test_missing_customer_returns_error(agent_seeded_engine):
    payload = json.loads(get_customer_360.run("C999"))
    assert "error" in payload


def test_missing_offer_returns_error(agent_seeded_engine):
    payload = json.loads(get_offer_by_id.run("OFFER-MISSING"))
    assert "error" in payload


def test_tools_do_not_mutate_database(agent_seeded_engine, agent_seeded_session):
    before_customers = agent_seeded_session.exec(select(Customer)).all()
    before_offers = agent_seeded_session.exec(select(Offer)).all()

    get_customer_360.run("C001")
    get_calculated_scores.run("C001")
    get_eligible_offers.run("C001")
    get_portfolio_metrics.run()

    after_customers = agent_seeded_session.exec(select(Customer)).all()
    after_offers = agent_seeded_session.exec(select(Offer)).all()
    assert len(before_customers) == len(after_customers)
    assert len(before_offers) == len(after_offers)
