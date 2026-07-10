# Business Case — RetainAI

> **Prototype capability** — not production banking policy. Financial figures are **estimated** for illustration; outcomes are **not guaranteed**.

## Business problem

Retail banks lose revenue when customers churn to competitors for home loans, credit cards, and deposits. Relationship Managers (RMs) manage large portfolios but lack a unified view of risk signals, eligibility constraints, and approved retention offers. Outreach is often **reactive** — triggered only after attrition — rather than when external shopping signals appear.

## Fragmented banking data

Customer insight is spread across:

- Core banking (balances, products, tenure)
- Credit history (bureau scores, delinquency)
- Bureau triggers (external loan/card inquiries)
- Transaction patterns (salary stability, spend shifts)

RetainAI **prototype** integrates these into a **Customer 360** view for demonstration purposes using **synthetic data only**.

## Reactive retention vs. proactive copilot

Traditional retention waits for account closure or complaint. RetainAI surfaces:

- **Churn risk** before exit
- **Revenue at risk** in currency terms
- **Priority-ranked** customers for RM time allocation
- **Next-best retention discussion** options from an approved catalog

## Customer 360

A single pane showing profile, products, credit posture, bureau triggers, and transaction features — refreshed on demand with staleness indicators. **Prototype:** seeded SQLite data, not live core banking feeds.

## External-shopping signals

Bureau events (e.g. home-loan inquiry at another institution) elevate urgency. The rules engine maps signal severity to churn score adjustments **deterministically** — the LLM does not alter scores.

## Revenue at risk

Synthetic modeling estimates annualized revenue exposure if the customer leaves, combining product balances and fee income. Used for **prioritization**, not regulatory capital calculations.

## Customer-value prioritization

Priority score blends churn risk and customer value so high-value at-risk customers surface first. Weights are configurable (`CHURN_PRIORITY_WEIGHT`, `VALUE_PRIORITY_WEIGHT`).

## Next-best retention discussion option

From eligible **approved offers** only (fee waivers, rate concessions, FD renewal incentives, repayment support). Agents recommend narrative framing; **eligibility is rules-gated**.

## RM productivity

- Portfolio dashboard with intervention counts
- Alert center (WebSocket + email in demo)
- RM Copilot for natural-language explanations grounded in evidence
- One-click approve / reject / defer on recommendations

**Estimated impact:** 15–25% reduction in RM research time per at-risk customer (illustrative; requires pilot measurement).

## Human approval

No offer is automatically applied to a customer account. RMs must **approve, reject, or defer** every recommendation. Audit logs record actions.

## Business KPIs (pilot targets)

| KPI | Prototype support | Production measurement |
|-----|-------------------|------------------------|
| Retention uplift | Scenario simulation | A/B pilot vs. control |
| Revenue saved | Revenue-at-risk rollup | Finance reconciliation |
| RM time per case | Copilot + 360 view | Time-motion study |
| Offer cost | Expected net benefit | Ledger actuals |
| Alert SLA | Event → notification latency | Ops monitoring |

## Estimated financial impact (illustrative)

Assumptions for a 500-RM pilot (synthetic modeling):

- 2% portfolio churn reduction on prioritized segment
- Average revenue at risk ₹1.2L per retained customer
- **Estimated annual value:** ₹15–40 Cr range (highly sensitive to segment definition)

**Disclaimer:** These figures are **estimates** for stakeholder discussion. They are not audited projections or guaranteed returns.

## Limitations

| Area | Prototype | Production need |
|------|-----------|-----------------|
| Data | Synthetic seed | Core banking connectors |
| Scoring | Rule-based churn | Calibrated ML model |
| Queue | In-memory asyncio | Durable message broker |
| Auth | None | RBAC, SSO |
| Offers | Static catalog | Live product engine |
| Compliance | Not reviewed | Policy + legal sign-off |

## Future adoption plan

1. **Phase 1** — Harden prototype (PostgreSQL, auth, durable queue)
2. **Phase 2** — Bank data integration and consent
3. **Phase 3** — Model governance and fairness review
4. **Phase 4** — Scale (Kubernetes, HA)
5. **Phase 5** — Pilot RMs, measure uplift, compliance approval

See [PRODUCTION_ROADMAP.md](./PRODUCTION_ROADMAP.md) for technical phases.

## Distinction summary

| Label | Meaning |
|-------|---------|
| **Prototype capability** | What this repository demonstrates today |
| **Production banking policy** | Requires bank-specific rules, legal review, and live data |
| **Estimated value** | Illustrative financial modeling |
| **Guaranteed outcome** | None — pilot measurement required |
