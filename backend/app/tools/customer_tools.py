"""Read-only Customer 360 tool for CrewAI agents."""

from __future__ import annotations

import json

from crewai.tools import tool

from app.core.exceptions import ResourceNotFoundError
from app.services.customer_360_service import Customer360Service
from app.tools._session import tool_session


@tool("get_customer_360")
def get_customer_360(customer_id: str) -> str:
    """Return concise Customer 360 data, source freshness, and warnings for a customer."""
    normalized_id = customer_id.strip().upper()
    with tool_session() as session:
        try:
            response = Customer360Service(session).get_customer_360(normalized_id)
        except ResourceNotFoundError:
            return json.dumps({"error": f"Customer {normalized_id} was not found"})
        from app.schemas.tool_outputs import Customer360ToolOutput

        return Customer360ToolOutput.from_response(response).model_dump_json()
