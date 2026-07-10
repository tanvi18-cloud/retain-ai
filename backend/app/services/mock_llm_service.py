"""Deterministic mock agent outputs for all seeded customers."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlmodel import Session

from app.core.agent_policy import AGENT_ELIGIBILITY_DISCLAIMER, build_prohibited_claims
from app.core.config import Settings, get_settings
from app.core.database import get_engine
from app.core.policy_rules import C004_RESTRICTED_LENDING_OFFER_IDS
from app.models.enums import RecommendationDecision
from app.schemas.agent_outputs import (
    DataQuality,
    EvidenceReference,
    OfferStrategyOutput,
    RetentionDecisionOutput,
    RMCopilotBrief,
    SignalInvestigation,
    Urgency,
)
from app.schemas.analysis import OfferFinancialOption, RulesOnlyAnalysisResponse
from app.schemas.eligibility import EligibleOffer
from app.services.analysis_service import AnalysisService


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _data_quality(analysis: RulesOnlyAnalysisResponse) -> DataQuality:
    warnings = analysis.customer_360_warnings
    if not warnings:
        return DataQuality.GOOD
    if any("missing" in warning.lower() for warning in warnings):
        return DataQuality.POOR
    return DataQuality.PARTIAL


def _stale_sources(analysis: RulesOnlyAnalysisResponse) -> list[str]:
    stale: list[str] = []
    freshness = analysis.customer_360_warnings
    for warning in freshness:
        if "stale" in warning.lower():
            stale.append(warning)
    return stale


def _find_offer(
    analysis: RulesOnlyAnalysisResponse,
    *,
    product_types: set[str] | None = None,
    name_contains: str | None = None,
) -> EligibleOffer | None:
    eligible = analysis.eligibility_result.eligible_offers
    for offer in eligible:
        if product_types and offer.product_type not in product_types:
            continue
        if name_contains and name_contains.lower() not in offer.offer_name.lower():
            continue
        return offer
    if product_types:
        for offer in eligible:
            if offer.product_type in product_types:
                return offer
    return eligible[0] if eligible else None


def _financial_for_offer(
    analysis: RulesOnlyAnalysisResponse,
    offer_id: str | None,
) -> OfferFinancialOption | None:
    if offer_id is None:
        return None
    for option in analysis.financial_options:
        if option.offer_id == offer_id:
            return option
    return None


def _urgency_for_decision(
    decision: RecommendationDecision,
    priority_score: int,
) -> Urgency:
    if decision == RecommendationDecision.NO_ACTION:
        return Urgency.NONE
    if decision == RecommendationDecision.RETAIN and priority_score >= 80:
        return Urgency.IMMEDIATE
    if decision in {RecommendationDecision.RETAIN, RecommendationDecision.REVIEW}:
        return Urgency.WITHIN_24_HOURS
    if decision == RecommendationDecision.MONITOR:
        return Urgency.MONITOR
    return Urgency.WITHIN_3_DAYS


def _contact_window(urgency: Urgency) -> str:
    mapping = {
        Urgency.IMMEDIATE: "Contact within 4 business hours",
        Urgency.WITHIN_24_HOURS: "Contact within 24 hours",
        Urgency.WITHIN_3_DAYS: "Contact within 3 business days",
        Urgency.MONITOR: "Review during next portfolio cycle",
        Urgency.NONE: "No contact required",
    }
    return mapping[urgency]


class MockLLMService:
    """Return deterministic, schema-valid agent outputs without network calls."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def _load_analysis(self, customer_id: str) -> RulesOnlyAnalysisResponse:
        with Session(get_engine()) as session:
            return AnalysisService(session).analyze_customer_rules_only(customer_id)

    def signal_investigation(self, customer_id: str) -> SignalInvestigation:
        """Return deterministic signal investigation output."""
        analysis = self._load_analysis(customer_id)
        scenario = self._scenario_config(customer_id, analysis)
        evidence = scenario["evidence"]
        return SignalInvestigation(
            customer_id=customer_id,
            primary_signal=scenario["primary_signal"],
            primary_signal_source=scenario["primary_signal_source"],
            supporting_signals=scenario["supporting_signals"],
            counter_signals=scenario["counter_signals"],
            data_quality=_data_quality(analysis),
            missing_data=scenario["missing_data"],
            stale_data_sources=_stale_sources(analysis),
            investigation_summary=scenario["investigation_summary"],
            evidence_references=evidence,
            confidence=scenario["confidence"],
        )

    def retention_decision(
        self,
        customer_id: str,
        investigation: SignalInvestigation | None = None,
    ) -> RetentionDecisionOutput:
        """Return deterministic retention decision output."""
        analysis = self._load_analysis(customer_id)
        scenario = self._scenario_config(customer_id, analysis)
        decision = analysis.priority_result.decision
        urgency = _urgency_for_decision(decision, analysis.priority_result.priority_score)
        policy_warnings = list(analysis.eligibility_result.policy_warnings)
        if customer_id == "C004":
            policy_warnings.append(
                "Customer has elevated DPD; new lending products are restricted."
            )
        return RetentionDecisionOutput(
            customer_id=customer_id,
            deterministic_decision=decision,
            agent_supported_decision=decision,
            urgency=urgency,
            recommended_contact_window=_contact_window(urgency),
            business_reason=scenario["business_reason"],
            customer_value_context=(
                f"Priority score {analysis.priority_result.priority_score} with "
                f"churn {analysis.churn_result.score} and value {analysis.value_result.score}."
            ),
            risks=scenario["risks"],
            policy_warnings=policy_warnings,
            score_consistency_valid=True,
            confidence=scenario["confidence"],
        )

    def offer_strategy(
        self,
        customer_id: str,
        investigation: SignalInvestigation | None = None,
        decision: RetentionDecisionOutput | None = None,
    ) -> OfferStrategyOutput:
        """Return deterministic offer strategy output."""
        analysis = self._load_analysis(customer_id)
        scenario = self._scenario_config(customer_id, analysis)
        primary = scenario["primary_offer"]
        alternate = scenario["alternate_offer"]
        primary_financial = _financial_for_offer(analysis, primary.offer_id if primary else None)
        return OfferStrategyOutput(
            customer_id=customer_id,
            recommended_offer_id=primary.offer_id if primary else None,
            alternate_offer_id=alternate.offer_id if alternate else None,
            no_offer_reason=scenario["no_offer_reason"],
            offer_rationale=scenario["offer_rationale"],
            scenario_fit=scenario["scenario_fit"],
            estimated_offer_cost=primary_financial.financials.estimated_offer_cost
            if primary_financial
            else None,
            expected_retention_uplift=primary_financial.financials.expected_retention_uplift
            if primary_financial
            else None,
            expected_net_benefit=primary_financial.financials.expected_net_benefit
            if primary_financial
            else None,
            financially_positive=primary_financial.financials.financially_positive
            if primary_financial
            else None,
            eligibility_disclaimer=AGENT_ELIGIBILITY_DISCLAIMER,
            policy_warnings=list(analysis.eligibility_result.policy_warnings),
            confidence=scenario["confidence"],
        )

    def rm_copilot_brief(
        self,
        customer_id: str,
        investigation: SignalInvestigation | None = None,
        decision: RetentionDecisionOutput | None = None,
        offer_strategy: OfferStrategyOutput | None = None,
    ) -> RMCopilotBrief:
        """Return deterministic RM copilot brief."""
        analysis = self._load_analysis(customer_id)
        scenario = self._scenario_config(customer_id, analysis)
        investigation = investigation or self.signal_investigation(customer_id)
        decision = decision or self.retention_decision(customer_id, investigation)
        offer_strategy = offer_strategy or self.offer_strategy(
            customer_id,
            investigation,
            decision,
        )
        financial_summary = "No eligible retention offer selected."
        if offer_strategy.recommended_offer_id:
            financial = _financial_for_offer(analysis, offer_strategy.recommended_offer_id)
            if financial:
                financial_summary = (
                    f"Estimated revenue at risk {financial.financials.revenue_at_risk}; "
                    f"expected net benefit {financial.financials.expected_net_benefit} "
                    "(estimate, not guaranteed)."
                )
        return RMCopilotBrief(
            customer_id=customer_id,
            headline=scenario["headline"],
            executive_summary=scenario["executive_summary"],
            why_now=scenario["why_now"],
            recommended_action=decision.recommended_contact_window
            + ": "
            + scenario["recommended_action"],
            talking_points=scenario["talking_points"],
            questions_to_ask_customer=scenario["questions_to_ask_customer"],
            prohibited_claims=build_prohibited_claims(),
            next_steps=scenario["next_steps"],
            primary_offer_id=offer_strategy.recommended_offer_id,
            financial_impact_summary=financial_summary,
            evidence_references=investigation.evidence_references,
            confidence=scenario["confidence"],
        )

    def _scenario_config(
        self,
        customer_id: str,
        analysis: RulesOnlyAnalysisResponse,
    ) -> dict:
        """Return customer-specific deterministic narrative configuration."""
        builders = {
            "C001": self._c001_scenario,
            "C002": self._c002_scenario,
            "C003": self._c003_scenario,
            "C004": self._c004_scenario,
            "C005": self._c005_scenario,
            "C006": self._c006_scenario,
            "C007": self._c007_scenario,
            "C008": self._c008_scenario,
            "C009": self._c009_scenario,
            "C010": self._c010_scenario,
        }
        builder = builders.get(customer_id, self._default_scenario)
        return builder(analysis)

    def _default_scenario(self, analysis: RulesOnlyAnalysisResponse) -> dict:
        primary_offer = _find_offer(analysis)
        return {
            "primary_signal": analysis.primary_trigger or "Portfolio monitoring signal",
            "primary_signal_source": "TRANSACTION_ENGINE",
            "supporting_signals": analysis.top_risk_signals[:3],
            "counter_signals": ["Long relationship tenure"],
            "missing_data": [],
            "investigation_summary": analysis.suggested_action,
            "evidence": [],
            "confidence": 0.75,
            "business_reason": analysis.priority_result.explanation,
            "risks": analysis.top_risk_signals[:2],
            "primary_offer": primary_offer,
            "alternate_offer": None,
            "no_offer_reason": None if primary_offer else "No eligible offers returned.",
            "offer_rationale": "Best eligible offer from deterministic eligibility service.",
            "scenario_fit": "General retention scenario.",
            "headline": f"Retention review for {analysis.customer_name}",
            "executive_summary": analysis.suggested_action,
            "why_now": "Deterministic priority score warrants RM review.",
            "recommended_action": analysis.suggested_action,
            "talking_points": ["Review recent activity", "Discuss relationship value"],
            "questions_to_ask_customer": ["Have your banking needs changed recently?"],
            "next_steps": ["Schedule RM review"],
        }

    def _c001_scenario(self, analysis: RulesOnlyAnalysisResponse) -> dict:
        primary = _find_offer(analysis, product_types={"HOME_LOAN"}, name_contains="fee")
        alternate = _find_offer(analysis, product_types={"HOME_LOAN"}, name_contains="rate")
        evidence = [
            EvidenceReference(
                source_system="CREDIT_BUREAU",
                source_type="BUREAU_TRIGGER",
                field="product_type",
                observed_value="HOME_LOAN",
            ),
            EvidenceReference(
                source_system="TRANSACTION_ENGINE",
                source_type="TRANSACTION_FEATURE",
                field="balance_change_pct_30d",
                observed_value=analysis.customer_360_warnings,
            ),
        ]
        return {
            "primary_signal": "External home-loan inquiry detected",
            "primary_signal_source": "CREDIT_BUREAU",
            "supporting_signals": [
                "Balance decline over 30 days",
                "Large external transfer pattern",
            ],
            "counter_signals": ["Excellent repayment history", "Zero recent DPD"],
            "missing_data": [],
            "investigation_summary": (
                "High-severity external home-loan inquiry combined with balance decline "
                "indicates urgent competitor attrition risk for a priority customer."
            ),
            "evidence": evidence,
            "confidence": 0.9,
            "business_reason": "Elevated churn and value scores require urgent retention action.",
            "risks": ["Competitor home-loan acquisition", "Deposit outflow"],
            "primary_offer": primary,
            "alternate_offer": alternate,
            "no_offer_reason": None,
            "offer_rationale": (
                "Home-loan processing-fee waiver aligns with external inquiry signal."
            ),
            "scenario_fit": "External home-loan inquiry retention scenario.",
            "headline": "Urgent retention: external home-loan inquiry",
            "executive_summary": (
                "Priority customer shows external home-loan inquiry with balance decline; "
                "immediate RM retention review recommended."
            ),
            "why_now": (
                "External bureau inquiry and transfer activity suggest competitor evaluation."
            ),
            "recommended_action": "Immediate RM review with home-loan retention discussion.",
            "talking_points": [
                "Acknowledge relationship tenure and salary relationship.",
                "Discuss home-loan processing-fee waiver as an RM discussion option.",
                "Explore reasons for external inquiry without promising approval.",
            ],
            "questions_to_ask_customer": [
                "Are you evaluating a home-loan with another institution?",
                "What timeline and features matter most for your decision?",
            ],
            "next_steps": ["Call customer today", "Prepare eligible home-loan discussion options"],
        }

    def _c002_scenario(self, analysis: RulesOnlyAnalysisResponse) -> dict:
        primary = _find_offer(
            analysis,
            product_types={"CREDIT_CARD", "TRAVEL_CARD"},
            name_contains="fee",
        )
        alternate = _find_offer(analysis, product_types={"CREDIT_CARD"}, name_contains="upgrade")
        return {
            "primary_signal": "External credit-card inquiry detected",
            "primary_signal_source": "CREDIT_BUREAU",
            "supporting_signals": ["Strong card spending history"],
            "counter_signals": ["Good credit score", "Low DPD"],
            "missing_data": [],
            "investigation_summary": (
                "External card inquiry suggests upgrade or fee-competition review opportunity."
            ),
            "evidence": [
                EvidenceReference(
                    source_system="CREDIT_BUREAU",
                    source_type="BUREAU_TRIGGER",
                    field="product_type",
                    observed_value="CREDIT_CARD",
                )
            ],
            "confidence": 0.84,
            "business_reason": "Card inquiry with strong usage supports retention review.",
            "risks": ["Card attrition to competitor"],
            "primary_offer": primary,
            "alternate_offer": alternate,
            "no_offer_reason": None,
            "offer_rationale": "Annual-fee waiver or card upgrade fits card inquiry scenario.",
            "scenario_fit": "External card inquiry retention scenario.",
            "headline": "Card retention review after external inquiry",
            "executive_summary": "Mass-affluent card-active customer with external card inquiry.",
            "why_now": "Recent bureau inquiry indicates active card comparison.",
            "recommended_action": "Discuss card upgrade or annual-fee waiver options.",
            "talking_points": [
                "Review current card benefits and spend patterns.",
                "Present fee-waiver or upgrade as RM discussion options.",
            ],
            "questions_to_ask_customer": [
                "Which card features are most important to you?",
                "Are you comparing annual fees or rewards?",
            ],
            "next_steps": ["Schedule card retention discussion"],
        }

    def _c003_scenario(self, analysis: RulesOnlyAnalysisResponse) -> dict:
        primary = _find_offer(analysis, product_types={"RELATIONSHIP"}, name_contains="priority")
        return {
            "primary_signal": "Salary credit stopped with external transfer pattern",
            "primary_signal_source": "TRANSACTION_ENGINE",
            "supporting_signals": ["Repeated transfers to another bank", "Declining balance"],
            "counter_signals": ["Good credit profile when available"],
            "missing_data": [],
            "investigation_summary": (
                "Salary relationship interruption with competitor transfers requires immediate "
                "relationship call."
            ),
            "evidence": [
                EvidenceReference(
                    source_system="TRANSACTION_ENGINE",
                    source_type="TRANSACTION_FEATURE",
                    field="salary_received_current_month",
                    observed_value=False,
                )
            ],
            "confidence": 0.92,
            "business_reason": "Salary stoppage is a critical relationship risk signal.",
            "risks": ["Primary salary relationship loss", "Competitor account migration"],
            "primary_offer": primary,
            "alternate_offer": None,
            "no_offer_reason": None,
            "offer_rationale": "Priority relationship review addresses salary relationship risk.",
            "scenario_fit": "Salary dependency retention scenario.",
            "headline": "Immediate call: salary relationship at risk",
            "executive_summary": "Salary credit stopped with competitor transfer activity.",
            "why_now": "Salary inflow interruption threatens core relationship value.",
            "recommended_action": "Immediate relationship call to understand salary change.",
            "talking_points": [
                "Confirm employment or payroll change.",
                "Discuss ways to restore primary banking relationship.",
            ],
            "questions_to_ask_customer": [
                "Has your salary account moved to another bank?",
                "Can we assist with payroll setup or relationship benefits?",
            ],
            "next_steps": ["Call within 4 hours", "Escalate to assigned RM"],
        }

    def _c004_scenario(self, analysis: RulesOnlyAnalysisResponse) -> dict:
        primary = _find_offer(analysis, product_types={"REPAYMENT"}, name_contains="repayment")
        lending_blocked = any(
            offer.offer_id in C004_RESTRICTED_LENDING_OFFER_IDS
            for offer in analysis.eligibility_result.eligible_offers
        )
        return {
            "primary_signal": "Elevated DPD with distressed credit profile",
            "primary_signal_source": "CREDIT_BUREAU",
            "supporting_signals": ["High churn risk signals"],
            "counter_signals": [],
            "missing_data": [],
            "investigation_summary": (
                "Customer is in distress with 60 DPD; focus on repayment support, not new lending."
            ),
            "evidence": [
                EvidenceReference(
                    source_system="CREDIT_BUREAU",
                    source_type="CREDIT_PROFILE",
                    field="max_dpd_12m",
                    observed_value=60,
                )
            ],
            "confidence": 0.88,
            "business_reason": "Distressed borrower requires service consultation, not lending.",
            "risks": ["Further delinquency", "Regulatory sensitivity on new lending"],
            "primary_offer": primary,
            "alternate_offer": None,
            "no_offer_reason": "New lending products are policy-restricted for this customer.",
            "offer_rationale": "Repayment-support consultation is the safe primary option.",
            "scenario_fit": "Distressed borrower support scenario.",
            "headline": "Repayment support required — lending restricted",
            "executive_summary": "Distressed borrower with elevated DPD; no new lending offer.",
            "why_now": "Recent DPD deterioration requires immediate service intervention.",
            "recommended_action": "Schedule repayment-support consultation.",
            "talking_points": [
                "Focus on repayment options and hardship support.",
                "Do not discuss new lending products.",
            ],
            "questions_to_ask_customer": [
                "Are you facing temporary cash-flow difficulty?",
                "Would a repayment-plan discussion be helpful?",
            ],
            "next_steps": ["Service consultation", "Document policy restriction on lending"],
            "policy_warning_lending_blocked": lending_blocked,
        }

    def _c005_scenario(self, analysis: RulesOnlyAnalysisResponse) -> dict:
        primary = _find_offer(analysis, product_types={"RELATIONSHIP"})
        return {
            "primary_signal": "Declining product usage without strong external trigger",
            "primary_signal_source": "TRANSACTION_ENGINE",
            "supporting_signals": ["Product inactivity increase"],
            "counter_signals": ["Long tenure", "Stable balances"],
            "missing_data": [],
            "investigation_summary": (
                "Usage decline suggests relationship reactivation opportunity."
            ),
            "evidence": [
                EvidenceReference(
                    source_system="TRANSACTION_ENGINE",
                    source_type="TRANSACTION_FEATURE",
                    field="product_inactivity_days",
                    observed_value="elevated",
                )
            ],
            "confidence": 0.78,
            "business_reason": "Moderate priority warrants relationship review.",
            "risks": ["Silent attrition"],
            "primary_offer": primary,
            "alternate_offer": None,
            "no_offer_reason": None,
            "offer_rationale": "Relationship review supports reactivation.",
            "scenario_fit": "Relationship reactivation scenario.",
            "headline": "Relationship reactivation review",
            "executive_summary": "Long-tenure customer with declining product usage.",
            "why_now": "Inactivity trend may precede silent attrition.",
            "recommended_action": "Monitor or schedule relationship reactivation discussion.",
            "talking_points": ["Review product fit", "Explore unmet needs"],
            "questions_to_ask_customer": ["Have you changed how you use our products?"],
            "next_steps": ["Relationship review call"],
        }

    def _c006_scenario(self, analysis: RulesOnlyAnalysisResponse) -> dict:
        primary = _find_offer(analysis, product_types={"RELATIONSHIP"})
        return {
            "primary_signal": "Low-severity external inquiry",
            "primary_signal_source": "CREDIT_BUREAU",
            "supporting_signals": [],
            "counter_signals": ["Otherwise stable transactions"],
            "missing_data": [],
            "investigation_summary": (
                "Low-severity inquiry with stable profile suggests monitoring."
            ),
            "evidence": [
                EvidenceReference(
                    source_system="CREDIT_BUREAU",
                    source_type="BUREAU_TRIGGER",
                    field="severity",
                    observed_value="LOW",
                )
            ],
            "confidence": 0.7,
            "business_reason": "Low priority score supports monitor/no-action path.",
            "risks": ["Minor competitive browsing"],
            "primary_offer": primary if analysis.priority_result.priority_score >= 50 else None,
            "alternate_offer": None,
            "no_offer_reason": "Priority below active retention threshold.",
            "offer_rationale": "Monitor unless priority increases.",
            "scenario_fit": "Low-severity monitoring scenario.",
            "headline": "Monitor: low-severity external inquiry",
            "executive_summary": "Stable low-value customer with minor external inquiry.",
            "why_now": "Signal is present but not urgent.",
            "recommended_action": "Continue routine monitoring.",
            "talking_points": ["Light-touch relationship check if contacted"],
            "questions_to_ask_customer": ["Are you exploring any new banking products?"],
            "next_steps": ["Add to monitor list"],
        }

    def _c007_scenario(self, analysis: RulesOnlyAnalysisResponse) -> dict:
        primary = _find_offer(analysis, product_types={"TRAVEL_CARD"})
        return {
            "primary_signal": "High forex spend with travel-card inquiry",
            "primary_signal_source": "TRANSACTION_ENGINE",
            "supporting_signals": ["Frequent traveller behavior"],
            "counter_signals": ["Strong card usage"],
            "missing_data": [],
            "investigation_summary": (
                "Travel and forex pattern supports travel-card upgrade discussion."
            ),
            "evidence": [
                EvidenceReference(
                    source_system="TRANSACTION_ENGINE",
                    source_type="TRANSACTION_FEATURE",
                    field="forex_spend_30d",
                    observed_value="high",
                )
            ],
            "confidence": 0.86,
            "business_reason": "Travel spend pattern aligns with travel-card offer.",
            "risks": ["Travel-card competitor switch"],
            "primary_offer": primary,
            "alternate_offer": None,
            "no_offer_reason": None,
            "offer_rationale": "Travel-card upgrade matches forex and inquiry signals.",
            "scenario_fit": "Frequent traveller retention scenario.",
            "headline": "Travel-card retention opportunity",
            "executive_summary": "High forex spending with external travel-card inquiry.",
            "why_now": "Upcoming travel season increases competitive card switching risk.",
            "recommended_action": "Discuss travel-card upgrade benefits.",
            "talking_points": ["Review forex spend benefits", "Compare travel rewards"],
            "questions_to_ask_customer": ["How often do you travel internationally?"],
            "next_steps": ["Present travel-card upgrade option"],
        }

    def _c008_scenario(self, analysis: RulesOnlyAnalysisResponse) -> dict:
        primary = _find_offer(analysis, product_types={"FIXED_DEPOSIT"}, name_contains="renew")
        return {
            "primary_signal": "Fixed deposit maturity approaching with outflow pattern",
            "primary_signal_source": "CORE_BANKING",
            "supporting_signals": ["Recent external transfer", "High customer value"],
            "counter_signals": ["Strong deposit history"],
            "missing_data": [],
            "investigation_summary": (
                "FD maturity with outflow risk creates renewal retention opportunity."
            ),
            "evidence": [
                EvidenceReference(
                    source_system="CORE_BANKING",
                    source_type="ACCOUNT",
                    field="fixed_deposit_maturity_date",
                    observed_value="upcoming",
                )
            ],
            "confidence": 0.87,
            "business_reason": "Deposit maturity timing requires proactive renewal discussion.",
            "risks": ["Deposit outflow at maturity"],
            "primary_offer": primary,
            "alternate_offer": None,
            "no_offer_reason": None,
            "offer_rationale": "FD renewal incentive aligns with maturity retention scenario.",
            "scenario_fit": "Fixed deposit renewal scenario.",
            "headline": "Fixed deposit maturity retention opportunity",
            "executive_summary": "Priority depositor with large FD maturing soon.",
            "why_now": "Maturity window is the highest-risk period for deposit outflow.",
            "recommended_action": "Discuss FD renewal incentive before maturity date.",
            "talking_points": ["Confirm renewal intentions", "Present renewal incentive"],
            "questions_to_ask_customer": [
                "Do you plan to renew or redeploy the maturity proceeds?"
            ],
            "next_steps": ["Schedule pre-maturity call"],
        }

    def _c009_scenario(self, analysis: RulesOnlyAnalysisResponse) -> dict:
        primary = _find_offer(analysis, product_types={"RELATIONSHIP"})
        return {
            "primary_signal": "Increasing external investment-transfer pattern",
            "primary_signal_source": "TRANSACTION_ENGINE",
            "supporting_signals": ["High-value investor profile"],
            "counter_signals": ["Strong overall relationship value"],
            "missing_data": [],
            "investigation_summary": (
                "External investment transfers suggest wealth-management referral discussion."
            ),
            "evidence": [
                EvidenceReference(
                    source_system="TRANSACTION_ENGINE",
                    source_type="TRANSACTION_FEATURE",
                    field="external_transfer_amount_30d",
                    observed_value="elevated",
                )
            ],
            "confidence": 0.83,
            "business_reason": "Investment outflow pattern warrants relationship review.",
            "risks": ["Wealth assets migrating externally"],
            "primary_offer": primary,
            "alternate_offer": None,
            "no_offer_reason": None,
            "offer_rationale": (
                "Relationship review supports wealth referral discussion without approval claims."
            ),
            "scenario_fit": "High-value investor retention scenario.",
            "headline": "Wealth relationship review recommended",
            "executive_summary": "High-value investor with external investment-transfer pattern.",
            "why_now": "Transfer trend may accelerate without RM engagement.",
            "recommended_action": "Discuss wealth-management referral as RM discussion option.",
            "talking_points": [
                "Explore investment goals",
                "Introduce wealth referral discussion without promising approval",
            ],
            "questions_to_ask_customer": ["Are you consolidating investments externally?"],
            "next_steps": ["Wealth referral discussion with RM"],
        }

    def _c010_scenario(self, analysis: RulesOnlyAnalysisResponse) -> dict:
        return {
            "primary_signal": "No material retention signal detected",
            "primary_signal_source": "CRM",
            "supporting_signals": [],
            "counter_signals": ["Stable activity", "No external triggers"],
            "missing_data": [],
            "investigation_summary": "Customer profile is stable with no material risk signals.",
            "evidence": [
                EvidenceReference(
                    source_system="CRM",
                    source_type="CUSTOMER_PROFILE",
                    field="risk_signals",
                    observed_value="none",
                )
            ],
            "confidence": 0.8,
            "business_reason": "Low priority score supports no-action decision.",
            "risks": [],
            "primary_offer": None,
            "alternate_offer": None,
            "no_offer_reason": "No eligible retention action required.",
            "offer_rationale": "Stable customer does not require retention offer.",
            "scenario_fit": "Stable no-action scenario.",
            "headline": "Stable customer — no action required",
            "executive_summary": "No material risk signals; continue routine service.",
            "why_now": "No urgent trigger identified.",
            "recommended_action": "No immediate retention action.",
            "talking_points": ["Routine service only if customer contacts bank"],
            "questions_to_ask_customer": [],
            "next_steps": ["Continue standard monitoring"],
        }
