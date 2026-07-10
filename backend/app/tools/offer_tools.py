"""Read-only offer tools for CrewAI agents."""

from __future__ import annotations

import json

from crewai.tools import tool

from app.core.exceptions import ResourceNotFoundError
from app.schemas.tool_outputs import EligibleOffersToolOutput, OfferToolOutput
from app.services.analysis_service import AnalysisService
from app.services.offer_repository import OfferRepository
from app.tools._session import tool_session


@tool("get_eligible_offers")
def get_eligible_offers(customer_id: str) -> str:
    """Return eligible and rejected offers with policy warnings for a customer."""
    normalized_id = customer_id.strip().upper()
    with tool_session() as session:
        try:
            analysis = AnalysisService(session).analyze_customer_rules_only(normalized_id)
        except ResourceNotFoundError:
            return json.dumps({"error": f"Customer {normalized_id} was not found"})
        return EligibleOffersToolOutput.from_eligibility(
            analysis.eligibility_result
        ).model_dump_json()


@tool("get_offer_by_id")
def get_offer_by_id(offer_id: str) -> str:
    """Return an approved offer definition including eligibility thresholds and cost."""
    normalized_id = offer_id.strip().upper()
    with tool_session() as session:
        try:
            offer = OfferRepository(session).get_by_id(normalized_id)
        except ResourceNotFoundError:
            return json.dumps({"error": f"Offer {normalized_id} was not found"})
        return OfferToolOutput.from_detail(offer).model_dump_json()
