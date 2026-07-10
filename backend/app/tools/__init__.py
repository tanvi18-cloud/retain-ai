"""CrewAI tool exports for RetainAI agents."""

from app.tools.customer_tools import get_customer_360
from app.tools.interaction_tools import get_customer_financial_options, get_customer_interactions
from app.tools.offer_tools import get_eligible_offers, get_offer_by_id
from app.tools.portfolio_tools import get_portfolio_metrics, get_priority_customers
from app.tools.scoring_tools import get_calculated_scores

SIGNAL_INVESTIGATOR_TOOLS = [
    get_customer_360,
    get_calculated_scores,
    get_customer_interactions,
]

RETENTION_DECISION_TOOLS = [
    get_customer_360,
    get_calculated_scores,
    get_customer_interactions,
]

OFFER_STRATEGY_TOOLS = [
    get_customer_360,
    get_calculated_scores,
    get_eligible_offers,
    get_offer_by_id,
    get_customer_financial_options,
]

RM_COPILOT_TOOLS = [
    get_customer_360,
    get_calculated_scores,
    get_eligible_offers,
    get_customer_interactions,
    get_customer_financial_options,
]

__all__ = [
    "OFFER_STRATEGY_TOOLS",
    "RETENTION_DECISION_TOOLS",
    "RM_COPILOT_TOOLS",
    "SIGNAL_INVESTIGATOR_TOOLS",
    "get_calculated_scores",
    "get_customer_360",
    "get_customer_financial_options",
    "get_customer_interactions",
    "get_eligible_offers",
    "get_offer_by_id",
    "get_portfolio_metrics",
    "get_priority_customers",
]
