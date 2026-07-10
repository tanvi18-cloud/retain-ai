"""Financial retention value calculations."""

from __future__ import annotations

from datetime import UTC, datetime

from app.core.exceptions import InvalidFinancialInputError
from app.schemas.analysis import RetentionFinancials

ASSUMPTIONS = [
    "Churn probability is estimated as churn_score divided by 100.",
    "Revenue at risk is estimated annual customer value multiplied by churn probability.",
    "Expected gross retention value is revenue at risk multiplied by expected retention uplift.",
    "Expected net benefit is expected gross retention value minus estimated offer cost.",
    "Financial projections are estimates and do not represent guaranteed revenue.",
]


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _round_money(value: float) -> float:
    return round(value, 2)


class FinancialValueService:
    """Calculate retention financial projections."""

    def calculate_retention_financials(
        self,
        *,
        annual_customer_value: float,
        churn_score: int,
        expected_retention_uplift: float,
        estimated_offer_cost: float,
    ) -> RetentionFinancials:
        """Calculate financial retention metrics with validated inputs."""
        if annual_customer_value < 0:
            raise InvalidFinancialInputError(
                message="Annual customer value must be non-negative",
                details={"annual_customer_value": annual_customer_value},
            )
        if churn_score < 0 or churn_score > 100:
            raise InvalidFinancialInputError(
                message="Churn score must be between 0 and 100",
                details={"churn_score": churn_score},
            )
        if expected_retention_uplift < 0 or expected_retention_uplift > 1:
            raise InvalidFinancialInputError(
                message="Expected retention uplift must be between 0 and 1",
                details={"expected_retention_uplift": expected_retention_uplift},
            )
        if estimated_offer_cost < 0:
            raise InvalidFinancialInputError(
                message="Estimated offer cost must be non-negative",
                details={"estimated_offer_cost": estimated_offer_cost},
            )

        churn_probability = churn_score / 100
        revenue_at_risk = _round_money(annual_customer_value * churn_probability)
        expected_gross_retention_value = _round_money(revenue_at_risk * expected_retention_uplift)
        expected_net_benefit = _round_money(expected_gross_retention_value - estimated_offer_cost)

        return RetentionFinancials(
            annual_customer_value=_round_money(annual_customer_value),
            churn_probability=churn_probability,
            revenue_at_risk=revenue_at_risk,
            expected_retention_uplift=expected_retention_uplift,
            estimated_offer_cost=_round_money(estimated_offer_cost),
            expected_gross_retention_value=expected_gross_retention_value,
            expected_net_benefit=expected_net_benefit,
            financially_positive=expected_net_benefit > 0,
            assumptions=list(ASSUMPTIONS),
            calculated_at=_utc_now(),
        )
