"""Central agent policy guardrails shared across all RetainAI agents."""

AGENT_ELIGIBILITY_DISCLAIMER = (
    "Eligibility indicates an RM discussion option and does not represent final "
    "credit or product approval. Financial values are estimates, not guaranteed revenue."
)

AGENT_POLICY_RULES: tuple[str, ...] = (
    "Use only information returned by tools or supplied task context.",
    "Never invent balances, credit scores, DPD, transactions, eligibility, offers, "
    "financial values, or customer events.",
    "Never change deterministic churn, value, or priority scores.",
    "Never recommend an offer not returned by the eligibility service.",
    "Never state that a product is approved.",
    "Never state expected revenue is guaranteed.",
    "Never infer protected or sensitive personal characteristics.",
    "Never send customer communications.",
    "Never write to the database.",
    "Never expose chain-of-thought.",
    "State when data is missing or stale.",
    "Include source evidence for important claims.",
    "Keep responses concise.",
    "Avoid unsupported regulatory or policy claims.",
)

PROHIBITED_APPROVAL_PHRASES: tuple[str, ...] = (
    "pre-approved",
    "preapproved",
    "guaranteed approval",
    "product is approved",
    "loan approved",
    "card approved",
    "guaranteed revenue",
    "guaranteed retention",
)


def build_agent_guardrail_text(*, role_context: str) -> str:
    """Build shared guardrail instructions for an agent prompt."""
    rules = "\n".join(f"- {rule}" for rule in AGENT_POLICY_RULES)
    return (
        f"{role_context}\n\n"
        "Global agent policy:\n"
        f"{rules}\n"
        f"- Required disclaimer when discussing offers or financial impact: "
        f"{AGENT_ELIGIBILITY_DISCLAIMER}"
    )


def build_prohibited_claims() -> list[str]:
    """Return standard prohibited claims for RM briefs."""
    return [
        "Do not promise product approval or final pricing.",
        "Do not guarantee retention outcomes or revenue.",
        "Do not quote balances or credit scores not returned by tools.",
        AGENT_ELIGIBILITY_DISCLAIMER,
    ]
