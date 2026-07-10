"""Read-only interaction and financial tools for CrewAI agents."""

from __future__ import annotations

import json

from crewai.tools import tool

from app.core.exceptions import ResourceNotFoundError
from app.schemas.tool_outputs import FinancialOptionsToolOutput, InteractionsToolOutput
from app.services.analysis_service import AnalysisService
from app.services.interaction_repository import InteractionRepository
from app.tools._session import tool_session


@tool("get_customer_interactions")
def get_customer_interactions(customer_id: str) -> str:
    """Return the latest 10 customer interactions without internal database details."""
    normalized_id = customer_id.strip().upper()
    with tool_session() as session:
        try:
            AnalysisService(session).analyze_customer_rules_only(normalized_id)
        except ResourceNotFoundError:
            return json.dumps({"error": f"Customer {normalized_id} was not found"})
        interactions = InteractionRepository(session).list_recent_by_customer(
            normalized_id,
            limit=10,
        )
        return InteractionsToolOutput(
            customer_id=normalized_id,
            interactions=interactions,
        ).model_dump_json()


@tool("get_customer_financial_options")
def get_customer_financial_options(customer_id: str) -> str:
    """Return eligible financial options with expected net benefit and assumptions."""
    normalized_id = customer_id.strip().upper()
    with tool_session() as session:
        try:
            analysis = AnalysisService(session).analyze_customer_rules_only(normalized_id)
        except ResourceNotFoundError:
            return json.dumps({"error": f"Customer {normalized_id} was not found"})
        return FinancialOptionsToolOutput.from_analysis(analysis).model_dump_json()
