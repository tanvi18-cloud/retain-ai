"""Demo scenario and performance smoke validation tests."""

from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.flows.retention_flow import run_retention_flow
from app.models.enums import AnalysisExecutionMode
from app.models.recommendation import Recommendation
from app.services.analysis_execution_service import AnalysisExecutionService
from app.services.analysis_service import AnalysisService


@pytest.fixture
def demo_settings() -> Settings:
    return Settings(
        app_name="RetainAI",
        app_env="development",
        mock_llm_mode=True,
        run_full_crew_min_priority=50,
        create_alert_min_priority=50,
    )


class TestDemoCustomerOutcomes:
    def test_c001_retain_home_loan(self, agent_seeded_session, demo_settings: Settings):
        execution = AnalysisExecutionService(agent_seeded_session).create_execution(
            customer_id="C001",
            mode=AnalysisExecutionMode.AGENTIC,
        )
        agent_seeded_session.commit()
        result = run_retention_flow(
            agent_seeded_session,
            execution_id=execution.id,
            customer_id="C001",
            settings=demo_settings,
            notifications_enabled=False,
        )
        agent_seeded_session.commit()
        rec = agent_seeded_session.get(Recommendation, result.recommendation_id)
        assert rec is not None
        assert rec.decision.value == "RETAIN"
        assert rec.recommended_offer_id in {"OFFER-HL-FEE", "OFFER-HL-RATE"}

    def test_c004_support_not_lending(self, agent_seeded_session, demo_settings: Settings):
        analysis = AnalysisService(agent_seeded_session).analyze_customer_rules_only("C004")
        eligible = {item.offer_id for item in analysis.eligibility_result.eligible_offers}
        assert "OFFER-REPAY-SUPPORT" in eligible
        assert "OFFER-HL-FEE" not in eligible

    def test_c008_fd_renewal(self, agent_seeded_session, demo_settings: Settings):
        execution = AnalysisExecutionService(agent_seeded_session).create_execution(
            customer_id="C008",
            mode=AnalysisExecutionMode.AGENTIC,
        )
        agent_seeded_session.commit()
        result = run_retention_flow(
            agent_seeded_session,
            execution_id=execution.id,
            customer_id="C008",
            settings=demo_settings,
            notifications_enabled=False,
        )
        agent_seeded_session.commit()
        rec = agent_seeded_session.get(Recommendation, result.recommendation_id)
        assert rec is not None
        assert rec.recommended_offer_id == "OFFER-FD-RENEW"

    def test_c010_no_action(self, agent_seeded_session, demo_settings: Settings):
        analysis = AnalysisService(agent_seeded_session).analyze_customer_rules_only("C010")
        assert analysis.priority_result.decision.value == "NO_ACTION"


class TestPerformanceSmoke:
    PORTFOLIO_THRESHOLD_SECONDS = 5.0
    CUSTOMER_360_THRESHOLD_SECONDS = 5.0
    ANALYSIS_THRESHOLD_SECONDS = 60.0

    def test_portfolio_api_latency(self, seeded_client: TestClient):
        start = time.perf_counter()
        response = seeded_client.get("/api/v1/portfolio/customers", params={"page_size": 10})
        elapsed = time.perf_counter() - start
        assert response.status_code == 200
        assert elapsed < self.PORTFOLIO_THRESHOLD_SECONDS

    def test_customer_360_api_latency(self, seeded_client: TestClient):
        start = time.perf_counter()
        response = seeded_client.get("/api/v1/customers/C001/360")
        elapsed = time.perf_counter() - start
        assert response.status_code == 200
        assert elapsed < self.CUSTOMER_360_THRESHOLD_SECONDS

    def test_mock_analysis_latency(self, agent_seeded_session, demo_settings: Settings):
        start = time.perf_counter()
        execution = AnalysisExecutionService(agent_seeded_session).create_execution(
            customer_id="C001",
            mode=AnalysisExecutionMode.AGENTIC,
        )
        agent_seeded_session.commit()
        run_retention_flow(
            agent_seeded_session,
            execution_id=execution.id,
            customer_id="C001",
            settings=demo_settings,
            notifications_enabled=False,
        )
        elapsed = time.perf_counter() - start
        assert elapsed < self.ANALYSIS_THRESHOLD_SECONDS
