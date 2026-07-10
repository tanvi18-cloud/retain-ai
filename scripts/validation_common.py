"""Shared helpers for RetainAI validation scripts."""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"


def bootstrap_backend_path() -> None:
    """Ensure backend package imports resolve when running from scripts/."""
    import sys

    backend_path = str(BACKEND_DIR)
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)


def validation_settings(*, database_url: str | None = None):
    """Build settings for offline validation with mock LLM mode."""
    bootstrap_backend_path()
    os.environ["MOCK_LLM_MODE"] = "true"

    from app.core.config import Settings

    if database_url is None:
        db_path = Path(tempfile.gettempdir()) / "retainai_validation.db"
        database_url = f"sqlite:///{db_path.as_posix()}"

    return Settings(
        app_name="RetainAI",
        app_env="development",
        mock_llm_mode=True,
        database_url=database_url,
        email_notifications_enabled=False,
    )


def reset_and_seed(settings):
    """Drop, recreate, and seed the validation database."""
    bootstrap_backend_path()
    from app.core.database import reset_engine
    from app.seed.seed_database import reset_database

    reset_engine()
    return reset_database(settings)


@dataclass
class CustomerValidationRow:
    """One row in the validation results table."""

    customer_id: str
    churn_score: float
    value_score: float
    priority_score: float
    decision: str
    selected_offer: str | None
    revenue_at_risk: float
    expected_net_benefit: float
    validation_status: str
    details: list[str]


def analyze_customer_flow(session, settings, customer_id: str):
    """Run agentic retention flow for one customer and return flow result + recommendation."""
    bootstrap_backend_path()
    from app.flows.retention_flow import run_retention_flow
    from app.models.enums import AnalysisExecutionMode
    from app.models.recommendation import Recommendation
    from app.services.analysis_execution_service import AnalysisExecutionService

    execution = AnalysisExecutionService(session).create_execution(
        customer_id=customer_id,
        mode=AnalysisExecutionMode.AGENTIC,
    )
    session.commit()
    flow_result = run_retention_flow(
        session,
        execution_id=execution.id,
        customer_id=customer_id,
        settings=settings,
        notifications_enabled=False,
    )
    session.commit()
    recommendation = None
    if flow_result.recommendation_id:
        recommendation = session.get(Recommendation, flow_result.recommendation_id)
    return flow_result, recommendation


def validate_customer_outcome(
    customer_id: str,
    *,
    churn_score: float,
    value_score: float,
    priority_score: float,
    decision: str,
    selected_offer: str | None,
    revenue_at_risk: float,
    expected_net_benefit: float,
) -> CustomerValidationRow:
    """Apply expected business rules for demo customers."""
    details: list[str] = []
    passed = True

    if customer_id == "C001":
        if decision != "RETAIN":
            passed = False
            details.append(f"expected RETAIN, got {decision}")
        if selected_offer not in {"OFFER-HL-FEE", "OFFER-HL-RATE"}:
            passed = False
            details.append(f"expected home-loan offer, got {selected_offer}")
    elif customer_id == "C004":
        if selected_offer in {"OFFER-HL-FEE", "OFFER-HL-RATE", "OFFER-CC-UPGRADE"}:
            passed = False
            details.append(f"lending offer must not be selected: {selected_offer}")
        if selected_offer != "OFFER-REPAY-SUPPORT" and selected_offer is not None:
            passed = False
            details.append("expected repayment support or no lending offer")
    elif customer_id == "C008":
        if selected_offer != "OFFER-FD-RENEW":
            passed = False
            details.append(f"expected OFFER-FD-RENEW, got {selected_offer}")
    elif customer_id == "C010":
        if decision != "NO_ACTION":
            passed = False
            details.append(f"expected NO_ACTION, got {decision}")
        retention_offers = {
            "OFFER-HL-FEE",
            "OFFER-HL-RATE",
            "OFFER-CC-FEE",
            "OFFER-CC-UPGRADE",
            "OFFER-TC-UPGRADE",
            "OFFER-FD-RENEW",
            "OFFER-PRIORITY-REVIEW",
        }
        if selected_offer in retention_offers:
            passed = False
            details.append(f"expected no retention offer, got {selected_offer}")

    status = "PASS" if passed else "FAIL"
    if not details:
        details.append("All checks passed")

    return CustomerValidationRow(
        customer_id=customer_id,
        churn_score=churn_score,
        value_score=value_score,
        priority_score=priority_score,
        decision=decision,
        selected_offer=selected_offer,
        revenue_at_risk=revenue_at_risk,
        expected_net_benefit=expected_net_benefit,
        validation_status=status,
        details=details,
    )


def print_validation_table(rows: list[CustomerValidationRow]) -> None:
    """Print a readable validation table."""
    headers = [
        "Customer",
        "Churn",
        "Value",
        "Priority",
        "Decision",
        "Offer",
        "Rev@Risk",
        "NetBenefit",
        "Status",
    ]
    print("\n" + " | ".join(headers))
    print("-" * 110)
    for row in rows:
        print(
            " | ".join(
                [
                    row.customer_id,
                    f"{row.churn_score:.1f}",
                    f"{row.value_score:.1f}",
                    f"{row.priority_score:.1f}",
                    row.decision,
                    row.selected_offer or "-",
                    f"{row.revenue_at_risk:,.0f}",
                    f"{row.expected_net_benefit:,.0f}",
                    row.validation_status,
                ]
            )
        )
        if row.validation_status == "FAIL":
            for detail in row.details:
                print(f"  -> {detail}")


def row_from_recommendation(customer_id: str, recommendation) -> dict[str, Any]:
    """Extract display fields from a recommendation model."""
    if recommendation is None:
        return {
            "churn_score": 0.0,
            "value_score": 0.0,
            "priority_score": 0.0,
            "decision": "UNKNOWN",
            "selected_offer": None,
            "revenue_at_risk": 0.0,
            "expected_net_benefit": 0.0,
        }
    return {
        "churn_score": recommendation.churn_score,
        "value_score": recommendation.value_score,
        "priority_score": recommendation.priority_score,
        "decision": recommendation.decision.value,
        "selected_offer": recommendation.recommended_offer_id,
        "revenue_at_risk": recommendation.revenue_at_risk,
        "expected_net_benefit": recommendation.expected_net_benefit,
    }
