"""Financial value service tests."""

import pytest

from app.core.exceptions import InvalidFinancialInputError
from app.services.financial_value_service import FinancialValueService


@pytest.fixture
def financial_service() -> FinancialValueService:
    return FinancialValueService()


def test_churn_probability(financial_service: FinancialValueService):
    result = financial_service.calculate_retention_financials(
        annual_customer_value=1_000_000.0,
        churn_score=60,
        expected_retention_uplift=0.2,
        estimated_offer_cost=10_000.0,
    )
    assert result.churn_probability == 0.6


def test_revenue_at_risk(financial_service: FinancialValueService):
    result = financial_service.calculate_retention_financials(
        annual_customer_value=1_000_000.0,
        churn_score=50,
        expected_retention_uplift=0.2,
        estimated_offer_cost=10_000.0,
    )
    assert result.revenue_at_risk == 500_000.0


def test_expected_gross_value(financial_service: FinancialValueService):
    result = financial_service.calculate_retention_financials(
        annual_customer_value=1_000_000.0,
        churn_score=50,
        expected_retention_uplift=0.2,
        estimated_offer_cost=10_000.0,
    )
    assert result.expected_gross_retention_value == 100_000.0


def test_expected_net_benefit(financial_service: FinancialValueService):
    result = financial_service.calculate_retention_financials(
        annual_customer_value=1_000_000.0,
        churn_score=50,
        expected_retention_uplift=0.2,
        estimated_offer_cost=10_000.0,
    )
    assert result.expected_net_benefit == 90_000.0
    assert result.financially_positive is True


def test_negative_net_benefit_remains_negative(financial_service: FinancialValueService):
    result = financial_service.calculate_retention_financials(
        annual_customer_value=100_000.0,
        churn_score=20,
        expected_retention_uplift=0.1,
        estimated_offer_cost=5_000.0,
    )
    assert result.expected_net_benefit < 0
    assert result.financially_positive is False


def test_invalid_negative_input_raises(financial_service: FinancialValueService):
    with pytest.raises(InvalidFinancialInputError):
        financial_service.calculate_retention_financials(
            annual_customer_value=-1.0,
            churn_score=20,
            expected_retention_uplift=0.1,
            estimated_offer_cost=100.0,
        )


def test_rounding(financial_service: FinancialValueService):
    result = financial_service.calculate_retention_financials(
        annual_customer_value=123_456.78,
        churn_score=33,
        expected_retention_uplift=0.17,
        estimated_offer_cost=1_234.56,
    )
    assert result.revenue_at_risk == round(123_456.78 * 0.33, 2)
    assert result.expected_net_benefit == round(
        result.expected_gross_retention_value - 1_234.56,
        2,
    )
