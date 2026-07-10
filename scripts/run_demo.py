#!/usr/bin/env python3
"""Interactive demonstration script for RetainAI synthetic retention scenarios."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field

from validation_common import (
    analyze_customer_flow,
    bootstrap_backend_path,
    reset_and_seed,
    validate_customer_outcome,
    validation_settings,
)

SYNTHETIC_LABEL = "[SYNTHETIC DATA — NOT FOR PRODUCTION DECISIONS]"


@dataclass
class DemoCustomerReport:
    customer_id: str
    churn_score: float = 0.0
    value_score: float = 0.0
    priority_score: float = 0.0
    decision: str = "UNKNOWN"
    selected_offer: str | None = None
    revenue_at_risk: float = 0.0
    expected_net_benefit: float = 0.0
    policy_warnings: list[str] = field(default_factory=list)
    alert_status: str = "NONE"
    recommendation_status: str | None = None
    validation_status: str = "PENDING"
    notes: list[str] = field(default_factory=list)


def _print_header(title: str) -> None:
    print(f"\n{'=' * 72}")
    print(title)
    print("=" * 72)


def _print_customer_report(report: DemoCustomerReport) -> None:
    print(f"\nCustomer: {report.customer_id} {SYNTHETIC_LABEL}")
    print(f"  Churn score:           {report.churn_score:.1f}")
    print(f"  Customer-value score:  {report.value_score:.1f}")
    print(f"  Priority score:        {report.priority_score:.1f}")
    print(f"  Decision:              {report.decision}")
    print(f"  Selected offer:        {report.selected_offer or '-'}")
    print(f"  Revenue at risk:       {report.revenue_at_risk:,.0f}")
    print(f"  Expected net benefit:  {report.expected_net_benefit:,.0f}")
    print(f"  Policy warnings:       {', '.join(report.policy_warnings) or '-'}")
    print(f"  Alert status:          {report.alert_status}")
    print(f"  Recommendation status: {report.recommendation_status or '-'}")
    print(f"  Validation:            {report.validation_status}")
    for note in report.notes:
        print(f"    -> {note}")


def main() -> int:
    """Run the RetainAI demonstration workflow and print a final report."""
    settings = validation_settings()
    if not settings.mock_llm_mode:
        print("ERROR: MOCK_LLM_MODE must be true for the demo script.", file=sys.stderr)
        return 1

    print(SYNTHETIC_LABEL)
    print("RetainAI demonstration — mock LLM mode (no live Qwen required)")

    summary = reset_and_seed(settings)
    bootstrap_backend_path()

    from sqlmodel import Session, select

    from app.core.database import configure_engine, get_engine
    from app.core.policy_rules import ELIGIBILITY_DISCLAIMER
    from app.flows.retention_flow import run_retention_flow
    from app.models.alert import Alert
    from app.models.customer import Customer
    from app.models.enums import (
        AnalysisExecutionMode,
        EventType,
        IncomingEventStatus,
        RecommendationStatus,
    )
    from app.models.event import IncomingEvent
    from app.models.offer import Offer
    from app.models.recommendation import Recommendation
    from app.schemas.chat import ChatRequest
    from app.services.analysis_execution_service import AnalysisExecutionService
    from app.services.analysis_service import AnalysisService
    from app.services.chat_service import ChatService
    from app.services.event_processor import EventProcessor
    from app.services.portfolio_service import PortfolioService

    configure_engine(settings.database_url)
    failures: list[str] = []
    reports: list[DemoCustomerReport] = []

    with Session(get_engine()) as session:
        customer_count = len(session.exec(select(Customer)).all())
        offer_count = len(session.exec(select(Offer)).all())
        if customer_count != 10:
            failures.append(f"expected 10 customers, found {customer_count}")
        if offer_count != 8:
            failures.append(f"expected 8 offers, found {offer_count}")

        portfolio = PortfolioService(session).get_summary()
        _print_header("Starting portfolio summary")
        print(f"  Total customers:              {portfolio.total_customers}")
        print(f"  Immediate intervention count: {portfolio.immediate_intervention_count}")
        print(f"  Review count:                 {portfolio.review_count}")
        print(f"  No-action count:              {portfolio.no_action_count}")
        print(f"  Total revenue at risk:        {portfolio.total_revenue_at_risk:,.0f}")

        # --- C001 home-loan urgency ---
        _print_header("Scenario C001 — urgent home-loan retention")
        event = IncomingEvent(
            customer_id="C001",
            event_type=EventType.EXTERNAL_HOME_LOAN_INQUIRY.value,
            source_system="CREDIT_BUREAU",
            payload_json={
                "severity": "HIGH",
                "institution_category": "PRIVATE_BANK",
                "amount_band": "HIGH",
            },
            status=IncomingEventStatus.RECEIVED,
            notifications_enabled=False,
        )
        session.add(event)
        session.commit()
        EventProcessor(session, settings).process_sync(event.id)
        session.commit()
        session.refresh(event)

        c001_rec = session.exec(
            select(Recommendation).where(Recommendation.triggering_event_id == event.id)
        ).first()
        c001_alert = session.exec(select(Alert).where(Alert.event_id == event.id)).first()
        c001_analysis = AnalysisService(session).analyze_customer_rules_only("C001")

        c001_report = DemoCustomerReport(customer_id="C001")
        if c001_rec:
            c001_report.churn_score = c001_rec.churn_score
            c001_report.value_score = c001_rec.value_score
            c001_report.priority_score = c001_rec.priority_score
            c001_report.decision = c001_rec.decision.value
            c001_report.selected_offer = c001_rec.recommended_offer_id
            c001_report.revenue_at_risk = c001_rec.revenue_at_risk
            c001_report.expected_net_benefit = c001_rec.expected_net_benefit
            c001_report.recommendation_status = c001_rec.status.value
        c001_report.policy_warnings = list(c001_analysis.eligibility_result.policy_warnings)
        c001_report.alert_status = (
            c001_alert.notification_status.value if c001_alert else "NONE"
        )
        validation = validate_customer_outcome(
            "C001",
            churn_score=c001_report.churn_score,
            value_score=c001_report.value_score,
            priority_score=c001_report.priority_score,
            decision=c001_report.decision,
            selected_offer=c001_report.selected_offer,
            revenue_at_risk=c001_report.revenue_at_risk,
            expected_net_benefit=c001_report.expected_net_benefit,
        )
        c001_report.validation_status = validation.validation_status
        c001_report.notes = validation.details
        reports.append(c001_report)
        if validation.validation_status == "FAIL":
            failures.extend(validation.details)

        # --- C004 lending restriction ---
        _print_header("Scenario C004 — lending restriction")
        c004_analysis = AnalysisService(session).analyze_customer_rules_only("C004")
        execution = AnalysisExecutionService(session).create_execution(
            customer_id="C004",
            mode=AnalysisExecutionMode.AGENTIC,
        )
        session.commit()
        c004_flow = run_retention_flow(
            session,
            execution_id=execution.id,
            customer_id="C004",
            settings=settings,
            notifications_enabled=False,
        )
        session.commit()
        c004_rec = (
            session.get(Recommendation, c004_flow.recommendation_id)
            if c004_flow.recommendation_id
            else None
        )

        c004_report = DemoCustomerReport(customer_id="C004")
        if c004_rec:
            c004_report.churn_score = c004_rec.churn_score
            c004_report.value_score = c004_rec.value_score
            c004_report.priority_score = c004_rec.priority_score
            c004_report.decision = c004_rec.decision.value
            c004_report.selected_offer = c004_rec.recommended_offer_id
            c004_report.revenue_at_risk = c004_rec.revenue_at_risk
            c004_report.expected_net_benefit = c004_rec.expected_net_benefit
            c004_report.recommendation_status = c004_rec.status.value
        c004_report.policy_warnings = list(c004_analysis.eligibility_result.policy_warnings)
        validation = validate_customer_outcome(
            "C004",
            churn_score=c004_report.churn_score,
            value_score=c004_report.value_score,
            priority_score=c004_report.priority_score,
            decision=c004_report.decision,
            selected_offer=c004_report.selected_offer,
            revenue_at_risk=c004_report.revenue_at_risk,
            expected_net_benefit=c004_report.expected_net_benefit,
        )
        c004_report.validation_status = validation.validation_status
        c004_report.notes = validation.details
        if ELIGIBILITY_DISCLAIMER in c004_analysis.eligibility_result.policy_warnings:
            c004_report.notes.append("Eligibility disclaimer present")
        reports.append(c004_report)
        if validation.validation_status == "FAIL":
            failures.extend(validation.details)

        # --- C008 FD retention ---
        _print_header("Scenario C008 — fixed-deposit retention")
        _flow, c008_rec = analyze_customer_flow(session, settings, "C008")
        c008_analysis = AnalysisService(session).analyze_customer_rules_only("C008")
        c008_report = DemoCustomerReport(customer_id="C008")
        if c008_rec:
            c008_report.churn_score = c008_rec.churn_score
            c008_report.value_score = c008_rec.value_score
            c008_report.priority_score = c008_rec.priority_score
            c008_report.decision = c008_rec.decision.value
            c008_report.selected_offer = c008_rec.recommended_offer_id
            c008_report.revenue_at_risk = c008_rec.revenue_at_risk
            c008_report.expected_net_benefit = c008_rec.expected_net_benefit
            c008_report.recommendation_status = c008_rec.status.value
        c008_report.policy_warnings = list(c008_analysis.eligibility_result.policy_warnings)
        validation = validate_customer_outcome(
            "C008",
            churn_score=c008_report.churn_score,
            value_score=c008_report.value_score,
            priority_score=c008_report.priority_score,
            decision=c008_report.decision,
            selected_offer=c008_report.selected_offer,
            revenue_at_risk=c008_report.revenue_at_risk,
            expected_net_benefit=c008_report.expected_net_benefit,
        )
        c008_report.validation_status = validation.validation_status
        c008_report.notes = validation.details
        reports.append(c008_report)
        if validation.validation_status == "FAIL":
            failures.extend(validation.details)

        # --- C010 no action ---
        _print_header("Scenario C010 — stable no-action customer")
        _flow, c010_rec = analyze_customer_flow(session, settings, "C010")
        c010_analysis = AnalysisService(session).analyze_customer_rules_only("C010")
        c010_report = DemoCustomerReport(customer_id="C010")
        if c010_rec:
            c010_report.churn_score = c010_rec.churn_score
            c010_report.value_score = c010_rec.value_score
            c010_report.priority_score = c010_rec.priority_score
            c010_report.decision = c010_rec.decision.value
            c010_report.selected_offer = c010_rec.recommended_offer_id
            c010_report.revenue_at_risk = c010_rec.revenue_at_risk
            c010_report.expected_net_benefit = c010_rec.expected_net_benefit
            c010_report.recommendation_status = c010_rec.status.value
        elif c010_analysis.priority_result.decision.value == "NO_ACTION":
            c010_report.decision = "NO_ACTION"
            c010_report.churn_score = c010_analysis.churn_result.score
            c010_report.value_score = c010_analysis.value_result.score
            c010_report.priority_score = c010_analysis.priority_result.priority_score
        c010_report.policy_warnings = list(c010_analysis.eligibility_result.policy_warnings)
        validation = validate_customer_outcome(
            "C010",
            churn_score=c010_report.churn_score,
            value_score=c010_report.value_score,
            priority_score=c010_report.priority_score,
            decision=c010_report.decision,
            selected_offer=c010_report.selected_offer,
            revenue_at_risk=c010_report.revenue_at_risk,
            expected_net_benefit=c010_report.expected_net_benefit,
        )
        c010_report.validation_status = validation.validation_status
        c010_report.notes = validation.details
        reports.append(c010_report)
        if validation.validation_status == "FAIL":
            failures.extend(validation.details)

        # --- RM Copilot chat ---
        _print_header("RM Copilot chat (mock mode)")
        chat_service = ChatService(session, settings)
        chat_checks = [
            ("Why is C001 urgent?", "C001"),
            ("Why is C004 not eligible for a loan?", "C004"),
            ("What offer is recommended for C008?", "C008"),
        ]
        for question, expected_customer in chat_checks:
            response = chat_service.chat(
                ChatRequest(message=question, rm_id="RM-01", customer_id=expected_customer)
            )
            session.commit()
            print(f"\nQ: {question}")
            print(f"A: {response.answer[:240]}{'...' if len(response.answer) > 240 else ''}")
            if expected_customer not in response.answer and expected_customer not in response.customer_ids:
                failures.append(f"chat answer for {expected_customer} missing customer context")
            if not response.evidence:
                failures.append(f"chat answer for {expected_customer} missing evidence")

    _print_header("Final demonstration report")
    for report in reports:
        _print_customer_report(report)

    print(f"\nSeed summary: customers={summary.customers_inserted}, offers={summary.offers_inserted}")
    print(f"MOCK_LLM_MODE={settings.mock_llm_mode}")

    if failures:
        print("\nDEMO FAILED", file=sys.stderr)
        for item in failures:
            print(f"  - {item}", file=sys.stderr)
        return 1

    print("\nDEMO PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
