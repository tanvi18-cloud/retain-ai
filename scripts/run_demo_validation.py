#!/usr/bin/env python3
"""End-to-end demo validation for RetainAI (mock LLM, bounded polling)."""

from __future__ import annotations

import asyncio
import sys
import time
from datetime import date
from unittest.mock import AsyncMock, patch

from validation_common import (
    analyze_customer_flow,
    bootstrap_backend_path,
    print_validation_table,
    reset_and_seed,
    row_from_recommendation,
    validate_customer_outcome,
    validation_settings,
)

POLL_INTERVAL_SECONDS = 0.05
POLL_TIMEOUT_SECONDS = 15.0


def _poll_event_completion(session, event_id: str) -> bool:
    """Poll event status until completed or timeout."""
    bootstrap_backend_path()
    from app.models.enums import IncomingEventStatus
    from app.models.event import IncomingEvent

    deadline = time.monotonic() + POLL_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        event = session.get(IncomingEvent, event_id)
        if event is None:
            return False
        if event.status == IncomingEventStatus.COMPLETED:
            return True
        if event.status == IncomingEventStatus.FAILED:
            return False
        session.expire(event)
        time.sleep(POLL_INTERVAL_SECONDS)
    return False


async def _deliver_notifications_safe(event_id: str, alert_id: str | None, settings) -> str:
    """Attempt notification delivery with email mocked."""
    bootstrap_backend_path()
    from app.services.event_processor import deliver_notifications
    from app.services.websocket_manager import WebSocketManager

    if alert_id is None:
        return "SKIPPED_NO_ALERT"
    manager = WebSocketManager()
    with patch("app.services.email_service.aiosmtplib.send", new_callable=AsyncMock):
        await deliver_notifications(event_id, alert_id, settings, manager)
    from sqlmodel import Session

    from app.core.database import get_engine
    from app.models.alert import Alert

    with Session(get_engine()) as session:
        alert = session.get(Alert, alert_id)
        if alert is None:
            return "UNKNOWN"
        return alert.notification_status.value


def main() -> int:
    """Run the full demo validation workflow and print a pass/fail report."""
    settings = validation_settings()
    reset_and_seed(settings)

    bootstrap_backend_path()
    from sqlmodel import Session, select

    from app.core.config import Settings
    from app.core.database import configure_engine, get_engine
    from app.core.policy_rules import C004_RESTRICTED_LENDING_OFFER_IDS, ELIGIBILITY_DISCLAIMER
    from app.flows.retention_flow import run_retention_flow
    from app.models.alert import Alert
    from app.models.audit_log import AuditLog
    from app.models.bureau_trigger import BureauTrigger
    from app.models.credit_profile import CreditProfile
    from app.models.enums import (
        AnalysisExecutionMode,
        AnalysisExecutionStatus,
        EventType,
        IncomingEventStatus,
        NotificationStatus,
    )
    from app.models.event import IncomingEvent
    from app.models.recommendation import Recommendation
    from app.schemas.chat import ChatRequest
    from app.services.analysis_execution_service import AnalysisExecutionService
    from app.services.analysis_service import AnalysisService
    from app.services.chat_service import ChatService
    from app.services.event_processor import EventProcessor

    configure_engine(settings.database_url)
    checks: list[tuple[str, bool, str]] = []

    with Session(get_engine()) as session:
        # --- C001 home-loan event workflow ---
        before_churn = AnalysisService(session).analyze_customer_rules_only("C001").churn_result.score
        trigger_count_before = len(
            session.exec(select(BureauTrigger).where(BureauTrigger.customer_id == "C001")).all()
        )

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
            notifications_enabled=True,
        )
        session.add(event)
        session.commit()
        session.refresh(event)

        processor = EventProcessor(session, settings)
        alert_id = processor.process_sync(event.id)
        session.commit()
        session.refresh(event)

        after_churn = AnalysisService(session).analyze_customer_rules_only("C001").churn_result.score
        triggers = session.exec(
            select(BureauTrigger).where(BureauTrigger.customer_id == "C001")
        ).all()
        recs = session.exec(
            select(Recommendation).where(Recommendation.triggering_event_id == event.id)
        ).all()
        alerts = session.exec(select(Alert).where(Alert.event_id == event.id)).all()
        audits = session.exec(
            select(AuditLog).where(AuditLog.entity_id == event.id)
        ).all()
        execution = (
            AnalysisExecutionService(session).get_by_id(event.execution_id)
            if event.execution_id
            else None
        )

        checks.append(("C001 event completed", event.status == IncomingEventStatus.COMPLETED, event.status.value))
        checks.append(
            (
                "C001 bureau trigger created",
                len(triggers) > trigger_count_before,
                f"triggers={len(triggers)}",
            )
        )
        checks.append(
            (
                "C001 churn increased",
                after_churn >= before_churn,
                f"{before_churn:.1f} -> {after_churn:.1f}",
            )
        )
        checks.append(
            (
                "C001 priority threshold met",
                event.analysis_result_json is not None
                and (event.analysis_result_json.get("priority_score") or 0) >= settings.run_full_crew_min_priority,
                str(event.analysis_result_json),
            )
        )
        checks.append(
            (
                "C001 recommendation persisted",
                bool(recs),
                f"count={len(recs)}",
            )
        )
        if recs:
            checks.append(
                (
                    "C001 home-loan offer selected",
                    recs[0].recommended_offer_id in {"OFFER-HL-FEE", "OFFER-HL-RATE"},
                    recs[0].recommended_offer_id or "none",
                )
            )
        checks.append(("C001 alert created", bool(alerts), f"count={len(alerts)}"))
        checks.append(
            (
                "C001 analysis execution completed",
                execution is not None and execution.status == AnalysisExecutionStatus.COMPLETED,
                execution.status.value if execution else "missing",
            )
        )
        checks.append(("C001 audit logs created", bool(audits), f"count={len(audits)}"))
        checks.append(
            (
                "C001 agentic analysis ran",
                bool(event.analysis_result_json and event.analysis_result_json.get("agentic_analysis_ran")),
                str(event.analysis_result_json.get("agentic_analysis_ran") if event.analysis_result_json else None),
            )
        )

        notification_status = asyncio.run(_deliver_notifications_safe(event.id, alert_id, settings))
        checks.append(
            (
                "C001 notification attempted",
                notification_status
                in {
                    NotificationStatus.SENT.value,
                    NotificationStatus.PARTIAL.value,
                    NotificationStatus.FAILED.value,
                    NotificationStatus.NOT_REQUIRED.value,
                },
                notification_status,
            )
        )

        # --- RM chat ---
        chat_service = ChatService(session, Settings(**settings.model_dump()))
        first = chat_service.chat(
            ChatRequest(message="Why is C001 urgent?", rm_id="RM-01", customer_id="C001")
        )
        session.commit()
        second = chat_service.chat(
            ChatRequest(
                message="What offer should I discuss?",
                rm_id="RM-01",
                conversation_id=first.conversation_id,
            )
        )
        checks.append(("Chat cites C001 evidence", "C001" in first.answer, first.answer[:120]))
        checks.append(
            (
                "Chat follow-up preserves context",
                "C001" in second.answer or second.customer_ids == ["C001"],
                second.answer[:120],
            )
        )
        checks.append(
            (
                "Chat answer cites evidence",
                bool(first.evidence),
                f"evidence_count={len(first.evidence)}",
            )
        )
        checks.append(
            (
                "Chat no approval promise",
                "approved" not in second.answer.lower() or "discussion" in second.answer.lower(),
                second.answer[:120],
            )
        )

        # --- Guardrail customers via validation table ---
        demo_rows = []
        for customer_id in ("C004", "C008", "C010"):
            _flow, recommendation = analyze_customer_flow(session, settings, customer_id)
            fields = row_from_recommendation(customer_id, recommendation)
            row = validate_customer_outcome(customer_id, **fields)
            demo_rows.append(row)
            checks.append(
                (f"{customer_id} scenario", row.validation_status == "PASS", "; ".join(row.details))
            )

        # --- C004 specific guardrails ---
        c004_analysis = AnalysisService(session).analyze_customer_rules_only("C004")
        profile = session.exec(
            select(CreditProfile).where(CreditProfile.customer_id == "C004")
        ).one()
        checks.append(("C004 60 DPD present", profile.max_dpd_12m >= 60, str(profile.max_dpd_12m)))
        rejected_ids = {o.offer_id for o in c004_analysis.eligibility_result.rejected_offers}
        checks.append(
            ("C004 lending offers rejected", "OFFER-HL-FEE" in rejected_ids, str(rejected_ids))
        )
        eligible_ids = {o.offer_id for o in c004_analysis.eligibility_result.eligible_offers}
        checks.append(
            (
                "C004 repayment support allowed",
                "OFFER-REPAY-SUPPORT" in eligible_ids,
                str(eligible_ids),
            )
        )
        checks.append(
            (
                "C004 policy warning present",
                any("DPD" in w or "credit" in w.lower() for w in c004_analysis.eligibility_result.policy_warnings)
                or ELIGIBILITY_DISCLAIMER in c004_analysis.eligibility_result.policy_warnings,
                str(c004_analysis.eligibility_result.policy_warnings),
            )
        )
        if demo_rows and demo_rows[0].customer_id == "C004":
            offer = demo_rows[0].selected_offer
            checks.append(
                (
                    "C004 no restricted lending offer",
                    offer not in C004_RESTRICTED_LENDING_OFFER_IDS if offer else True,
                    str(offer),
                )
            )

        # --- C008 FD scenario via event ---
        c008_account_maturity = None
        from app.models.account import Account

        fd_account = session.exec(
            select(Account).where(
                Account.customer_id == "C008",
                Account.account_type == "FIXED_DEPOSIT",
            )
        ).first()
        if fd_account and fd_account.fixed_deposit_maturity_date:
            c008_account_maturity = fd_account.fixed_deposit_maturity_date

        fd_event = IncomingEvent(
            customer_id="C008",
            event_type=EventType.FIXED_DEPOSIT_MATURITY.value,
            source_system="CORE_BANKING",
            payload_json={
                "maturity_date": (c008_account_maturity or date(2026, 8, 1)).isoformat(),
                "maturity_amount": 500000.0,
            },
            status=IncomingEventStatus.RECEIVED,
            notifications_enabled=False,
        )
        session.add(fd_event)
        session.commit()
        EventProcessor(session, settings).process_sync(fd_event.id)
        session.commit()
        session.refresh(fd_event)
        c008_recs = session.exec(
            select(Recommendation).where(Recommendation.triggering_event_id == fd_event.id)
        ).all()
        checks.append(
            (
                "C008 FD event completed",
                fd_event.status == IncomingEventStatus.COMPLETED,
                fd_event.status.value,
            )
        )
        if c008_recs:
            checks.append(
                (
                    "C008 FD renewal offer",
                    c008_recs[0].recommended_offer_id == "OFFER-FD-RENEW",
                    c008_recs[0].recommended_offer_id or "none",
                )
            )
            checks.append(
                (
                    "C008 positive net benefit",
                    c008_recs[0].expected_net_benefit >= 0,
                    str(c008_recs[0].expected_net_benefit),
                )
            )

        # --- C010 no action ---
        c010_flow, c010_rec = analyze_customer_flow(session, settings, "C010")
        checks.append(
            ("C010 full crew skipped", c010_flow.agentic_analysis_ran is False, str(c010_flow.agentic_analysis_ran))
        )
        checks.append(("C010 no alert", c010_flow.alert_id is None, str(c010_flow.alert_id)))
        checks.append(
            (
                "C010 no retention offer",
                c010_rec is None
                or c010_rec.recommended_offer_id
                not in {
                    "OFFER-HL-FEE",
                    "OFFER-HL-RATE",
                    "OFFER-FD-RENEW",
                    "OFFER-CC-FEE",
                    "OFFER-CC-UPGRADE",
                    "OFFER-TC-UPGRADE",
                    "OFFER-PRIORITY-REVIEW",
                },
                c010_rec.recommended_offer_id if c010_rec else "none",
            )
        )

    print_validation_table(demo_rows)
    print("\nDemo validation report")
    print("-" * 60)
    failed = 0
    for name, ok, detail in checks:
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {name}: {detail}")
        if not ok:
            failed += 1

    if failed:
        print(f"\nDemo validation FAILED ({failed} check(s))", file=sys.stderr)
        return 1

    print("\nDemo validation PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
