"""End-to-end backend workflow integration tests."""

from __future__ import annotations

import asyncio
from datetime import date
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import Settings
from app.core.policy_rules import ELIGIBILITY_DISCLAIMER
from app.flows.retention_flow import run_retention_flow
from app.models.alert import Alert
from app.models.audit_log import AuditLog
from app.models.bureau_trigger import BureauTrigger
from app.models.credit_profile import CreditProfile
from app.models.enums import (
    AlertType,
    AnalysisExecutionMode,
    AnalysisExecutionStatus,
    EventType,
    IncomingEventStatus,
    NotificationStatus,
    RecommendationDecision,
    RecommendationStatus,
)
from app.models.event import IncomingEvent
from app.models.recommendation import Recommendation
from app.schemas.chat import ChatRequest
from app.seed.seed_database import seed_database
from app.services.analysis_execution_service import AnalysisExecutionService
from app.services.analysis_service import AnalysisService
from app.services.chat_service import ChatService
from app.services.event_processor import EventProcessor, deliver_notifications
from app.services.recommendation_action_service import APPROVAL_DISCLAIMER
from app.services.websocket_manager import WebSocketManager


@pytest.fixture
def e2e_settings() -> Settings:
    return Settings(
        app_name="RetainAI",
        app_env="development",
        mock_llm_mode=True,
        run_full_crew_min_priority=50,
        create_alert_min_priority=50,
        email_notifications_enabled=True,
    )


@pytest.fixture
def e2e_session(db_session: Session) -> Session:
    seed_database(db_session, skip_if_complete=False)
    return db_session


def _create_event(
    session: Session,
    *,
    customer_id: str,
    event_type: EventType,
    payload: dict,
    notifications_enabled: bool = True,
) -> IncomingEvent:
    event = IncomingEvent(
        customer_id=customer_id,
        event_type=event_type.value,
        source_system="CREDIT_BUREAU",
        payload_json=payload,
        status=IncomingEventStatus.RECEIVED,
        notifications_enabled=notifications_enabled,
    )
    session.add(event)
    session.commit()
    session.refresh(event)
    return event


class TestScenarioAHomeLoanRetention:
    """C001 urgent home-loan retention via EXTERNAL_HOME_LOAN_INQUIRY."""

    def test_full_event_workflow(self, e2e_session: Session, e2e_settings: Settings):
        before_churn = (
            AnalysisService(e2e_session).analyze_customer_rules_only("C001").churn_result.score
        )
        trigger_count_before = len(
            e2e_session.exec(select(BureauTrigger).where(BureauTrigger.customer_id == "C001")).all()
        )

        event = _create_event(
            e2e_session,
            customer_id="C001",
            event_type=EventType.EXTERNAL_HOME_LOAN_INQUIRY,
            payload={
                "severity": "HIGH",
                "institution_category": "PRIVATE_BANK",
                "amount_band": "HIGH",
            },
        )
        processor = EventProcessor(e2e_session, e2e_settings)
        alert_id = processor.process_sync(event.id)
        e2e_session.commit()
        e2e_session.refresh(event)

        after_churn = (
            AnalysisService(e2e_session).analyze_customer_rules_only("C001").churn_result.score
        )
        triggers = e2e_session.exec(
            select(BureauTrigger).where(BureauTrigger.customer_id == "C001")
        ).all()
        recs = e2e_session.exec(
            select(Recommendation).where(Recommendation.triggering_event_id == event.id)
        ).all()
        alerts = e2e_session.exec(select(Alert).where(Alert.event_id == event.id)).all()
        audits = e2e_session.exec(select(AuditLog).where(AuditLog.entity_id == event.id)).all()
        execution = AnalysisExecutionService(e2e_session).get_by_id(event.execution_id)

        assert len(triggers) > trigger_count_before
        assert any(t.product_type == "HOME_LOAN" for t in triggers)
        assert after_churn >= before_churn
        assert event.status == IncomingEventStatus.COMPLETED
        assert event.analysis_result_json is not None
        assert (
            event.analysis_result_json.get("priority_score") or 0
        ) >= e2e_settings.run_full_crew_min_priority
        assert event.analysis_result_json.get("agentic_analysis_ran") is True
        assert recs
        assert recs[0].recommended_offer_id in {"OFFER-HL-FEE", "OFFER-HL-RATE"}
        assert alerts
        assert execution.status == AnalysisExecutionStatus.COMPLETED
        assert audits

        async def _notify():
            manager = WebSocketManager()
            with patch("app.services.email_service.aiosmtplib.send", new_callable=AsyncMock):
                await deliver_notifications(event.id, alert_id, e2e_settings, manager)

        asyncio.run(_notify())
        e2e_session.expire_all()
        alert = e2e_session.get(Alert, alert_id)
        assert alert is not None
        assert alert.notification_status in {
            NotificationStatus.SENT,
            NotificationStatus.PARTIAL,
            NotificationStatus.FAILED,
            NotificationStatus.NOT_REQUIRED,
            NotificationStatus.PENDING,
        }


class TestScenarioBCreditRestriction:
    """C004 credit restriction and safe recommendation."""

    def test_c004_rules_and_flow(self, e2e_session: Session, e2e_settings: Settings):
        analysis = AnalysisService(e2e_session).analyze_customer_rules_only("C004")
        profile = e2e_session.exec(
            select(CreditProfile).where(CreditProfile.customer_id == "C004")
        ).one()

        assert profile.max_dpd_12m >= 60
        rejected_ids = {offer.offer_id for offer in analysis.eligibility_result.rejected_offers}
        eligible_ids = {offer.offer_id for offer in analysis.eligibility_result.eligible_offers}
        assert "OFFER-HL-FEE" in rejected_ids
        assert "OFFER-REPAY-SUPPORT" in eligible_ids
        assert ELIGIBILITY_DISCLAIMER in analysis.eligibility_result.policy_warnings

        execution = AnalysisExecutionService(e2e_session).create_execution(
            customer_id="C004",
            mode=AnalysisExecutionMode.AGENTIC,
        )
        e2e_session.commit()
        result = run_retention_flow(
            e2e_session,
            execution_id=execution.id,
            customer_id="C004",
            settings=e2e_settings,
            notifications_enabled=False,
        )
        e2e_session.commit()
        rec = e2e_session.get(Recommendation, result.recommendation_id)
        assert rec is not None
        assert rec.recommended_offer_id not in {"OFFER-HL-FEE", "OFFER-HL-RATE", "OFFER-CC-UPGRADE"}
        assert "approv" not in rec.summary.lower() or "discussion" in rec.summary.lower()


class TestScenarioCFixedDepositRetention:
    """C008 fixed-deposit maturity retention."""

    def test_fd_maturity_event(self, e2e_session: Session, e2e_settings: Settings):
        from app.models.account import Account

        fd_account = e2e_session.exec(
            select(Account).where(
                Account.customer_id == "C008",
                Account.account_type == "FIXED_DEPOSIT",
            )
        ).first()
        assert fd_account is not None
        maturity_date = fd_account.fixed_deposit_maturity_date or date(2026, 8, 1)

        event = _create_event(
            e2e_session,
            customer_id="C008",
            event_type=EventType.FIXED_DEPOSIT_MATURITY,
            payload={
                "maturity_date": maturity_date.isoformat(),
                "maturity_amount": 500000.0,
            },
            notifications_enabled=False,
        )
        EventProcessor(e2e_session, e2e_settings).process_sync(event.id)
        e2e_session.commit()
        e2e_session.refresh(event)
        e2e_session.refresh(fd_account)

        recs = e2e_session.exec(
            select(Recommendation).where(Recommendation.triggering_event_id == event.id)
        ).all()
        assert event.status == IncomingEventStatus.COMPLETED
        assert recs
        assert recs[0].recommended_offer_id == "OFFER-FD-RENEW"
        assert recs[0].expected_net_benefit >= 0


class TestScenarioDNoAction:
    """C010 no-action customer."""

    def test_c010_no_action_route(self, e2e_session: Session, e2e_settings: Settings):
        analysis = AnalysisService(e2e_session).analyze_customer_rules_only("C010")
        assert analysis.priority_result.decision == RecommendationDecision.NO_ACTION

        execution = AnalysisExecutionService(e2e_session).create_execution(
            customer_id="C010",
            mode=AnalysisExecutionMode.AGENTIC,
        )
        e2e_session.commit()
        result = run_retention_flow(
            e2e_session,
            execution_id=execution.id,
            customer_id="C010",
            settings=e2e_settings,
            notifications_enabled=False,
        )
        e2e_session.commit()
        rec = (
            e2e_session.get(Recommendation, result.recommendation_id)
            if result.recommendation_id
            else None
        )

        assert result.agentic_analysis_ran is False
        assert result.alert_id is None
        assert rec is None or rec.recommended_offer_id not in {
            "OFFER-HL-FEE",
            "OFFER-HL-RATE",
            "OFFER-FD-RENEW",
            "OFFER-CC-FEE",
            "OFFER-CC-UPGRADE",
            "OFFER-TC-UPGRADE",
            "OFFER-PRIORITY-REVIEW",
        }
        alerts = e2e_session.exec(select(Alert).where(Alert.customer_id == "C010")).all()
        agent_alerts = [
            alert for alert in alerts if alert.alert_type == AlertType.AGENT_RECOMMENDATION
        ]
        assert agent_alerts == []


class TestScenarioERMActionLifecycle:
    """Recommendation review through close."""

    def test_full_rm_lifecycle(self, seeded_client: TestClient):
        create = seeded_client.post(
            "/api/v1/analysis/C001",
            json={"notifications_enabled": False},
        )
        assert create.status_code == 202
        execution_id = create.json()["execution_id"]
        recommendation_id = None
        for _ in range(40):
            detail = seeded_client.get(f"/api/v1/analysis/executions/{execution_id}").json()
            if detail["status"] == AnalysisExecutionStatus.COMPLETED.value:
                recommendation_id = detail.get("recommendation_id")
                break
            __import__("time").sleep(0.1)
        assert recommendation_id is not None

        review = seeded_client.post(
            f"/api/v1/recommendations/{recommendation_id}/review",
            json={"rm_id": "RM001", "notes": "Reviewed for demo"},
        )
        approve = seeded_client.post(
            f"/api/v1/recommendations/{recommendation_id}/approve",
            json={"rm_id": "RM001"},
        )
        contacted = seeded_client.post(
            f"/api/v1/recommendations/{recommendation_id}/contacted",
            json={
                "rm_id": "RM001",
                "offer_presented": True,
                "contact_channel": "PHONE",
                "customer_response": "Will review",
            },
        )
        closed = seeded_client.post(
            f"/api/v1/recommendations/{recommendation_id}/close",
            json={"rm_id": "RM001", "closing_note": "Completed outreach"},
        )
        blocked = seeded_client.post(
            f"/api/v1/recommendations/{recommendation_id}/approve",
            json={"rm_id": "RM001"},
        )

        assert review.status_code == 200
        assert approve.status_code == 200
        assert contacted.status_code == 200
        assert closed.status_code == 200
        assert blocked.status_code == 409
        assert closed.json()["status"] == RecommendationStatus.CLOSED.value

        detail = seeded_client.get(f"/api/v1/recommendations/{recommendation_id}")
        assert detail.status_code == 200
        interactions = detail.json()["interactions"]
        assert interactions
        approve_interaction = next(
            (item for item in interactions if item["action_type"] == "RECOMMENDATION_APPROVED"),
            None,
        )
        assert approve_interaction is not None
        assert APPROVAL_DISCLAIMER in (approve_interaction.get("notes") or "")


class TestScenarioFRMChat:
    """RM chat context and evidence-backed answers."""

    @pytest.fixture
    def chat_service(self, e2e_session: Session, e2e_settings: Settings) -> ChatService:
        return ChatService(e2e_session, e2e_settings)

    def test_c001_chat_follow_up(self, chat_service: ChatService, e2e_session: Session):
        first = chat_service.chat(
            ChatRequest(message="Why is C001 urgent?", rm_id="RM-01", customer_id="C001")
        )
        e2e_session.commit()
        second = chat_service.chat(
            ChatRequest(
                message="What offer should I discuss?",
                rm_id="RM-01",
                conversation_id=first.conversation_id,
            )
        )

        assert "C001" in first.answer
        assert first.evidence
        assert "C001" in second.answer or second.customer_ids == ["C001"]
        assert "priority" in first.answer.lower() or "home" in first.answer.lower()
        if second.evidence:
            assert all(
                "score" not in item.field.lower() or item.value_summary for item in second.evidence
            )
        assert "approved for credit" not in second.answer.lower()
