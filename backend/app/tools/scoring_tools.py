"""Read-only scoring tool for CrewAI agents."""

from __future__ import annotations

import json

from crewai.tools import tool

from app.core.exceptions import ResourceNotFoundError
from app.schemas.tool_outputs import CalculatedScoresToolOutput
from app.services.analysis_service import AnalysisService
from app.tools._session import tool_session


@tool("get_calculated_scores")
def get_calculated_scores(customer_id: str) -> str:
    """Return deterministic churn, value, priority scores and triggered rules for a customer."""
    normalized_id = customer_id.strip().upper()
    with tool_session() as session:
        try:
            analysis = AnalysisService(session).analyze_customer_rules_only(normalized_id)
        except ResourceNotFoundError:
            return json.dumps({"error": f"Customer {normalized_id} was not found"})
        return CalculatedScoresToolOutput.from_analysis(analysis).model_dump_json()
