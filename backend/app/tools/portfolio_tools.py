"""Read-only portfolio tools for CrewAI agents."""

from __future__ import annotations

from crewai.tools import tool

from app.schemas.tool_outputs import PortfolioMetricsToolOutput, PriorityCustomersToolOutput
from app.services.portfolio_service import PortfolioService
from app.tools._session import tool_session


@tool("get_portfolio_metrics")
def get_portfolio_metrics() -> str:
    """Return portfolio summary metrics including priority counts and revenue at risk."""
    with tool_session() as session:
        summary = PortfolioService(session).get_summary()
        return PortfolioMetricsToolOutput.from_summary(summary).model_dump_json()


@tool("get_priority_customers")
def get_priority_customers(limit: int = 10) -> str:
    """Return the highest-priority customers with scores, decisions, and suggested actions."""
    bounded_limit = max(1, min(int(limit), 50))
    with tool_session() as session:
        page = PortfolioService(session).list_customers(
            page=1,
            page_size=bounded_limit,
            sort_by="priority_score",
            sort_order="desc",
        )
        return PriorityCustomersToolOutput(customers=page.items).model_dump_json()
