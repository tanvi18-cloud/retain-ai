"""Suggested follow-up questions for RM chat."""

from app.models.enums import ChatIntent


def suggested_questions(intent: ChatIntent, customer_ids: list[str]) -> list[str]:
    """Return 3–5 contextual suggested questions."""
    customer = customer_ids[0] if customer_ids else None
    if customer == "C004":
        return [
            "Why are lending offers blocked?",
            "What support option is available?",
            "What should the RM avoid promising?",
            "What is the recommendation status?",
        ]
    if customer:
        return [
            "Why is this customer high risk?",
            "Which offers are eligible?",
            "What should I say on the call?",
            "What data is stale?",
            "What is the expected financial impact?",
        ]
    if intent in {ChatIntent.PORTFOLIO_SUMMARY, ChatIntent.PRIORITY_CUSTOMER_LIST}:
        return [
            "Who should I call today?",
            "Show high-value, high-risk customers.",
            "Which customers have home-loan inquiries?",
            "How much revenue is at risk?",
        ]
    return [
        "Who should I call today?",
        "Why is C001 urgent?",
        "Compare C001 and C008.",
    ][:4]
