# Demo Script — RetainAI

Repeatable demonstration of synthetic retention scenarios using real backend services (no Docker or Qwen required).

## Run

From the `backend` directory:

```bash
cd backend
uv run python ../scripts/run_demo.py
```

Requirements:

- `MOCK_LLM_MODE=true` (enforced by the script)
- No running server required (uses in-process services)
- No real email sent (`notifications_enabled=False` for scripted events)

## What it does

1. **Confirms mock mode** — exits if `MOCK_LLM_MODE` is not true
2. **Resets and seeds** the database with 10 synthetic customers and 8 approved offers
3. **Verifies** exactly 10 customers
4. **Prints** starting portfolio summary
5. **Runs scenarios:**
   - **C001** — urgent home-loan retention (external inquiry event)
   - **C004** — lending restriction (agentic flow, no lending offers)
   - **C008** — fixed-deposit retention
   - **C010** — stable no-action customer
6. **RM Copilot questions:**
   - "Why is C001 urgent?"
   - "Why is C004 not eligible for a loan?"
   - "What offer is recommended for C008?"
7. **Prints final report** per customer

## Report fields (per customer)

| Field | Description |
|-------|-------------|
| Churn score | Deterministic 0–100 risk score |
| Customer-value score | Portfolio value contribution |
| Priority score | Weighted retention priority |
| Decision | RETAIN / REVIEW / NO_ACTION |
| Selected offer | Approved offer ID or `-` |
| Revenue at risk | Synthetic INR exposure |
| Expected net benefit | Offer benefit minus cost |
| Policy warnings | Eligibility disclaimers |
| Alert status | Notification delivery state |
| Recommendation status | PENDING / APPROVED / etc. |

All values are labeled **\[SYNTHETIC DATA — NOT FOR PRODUCTION DECISIONS\]**.

## Expected outcomes

| Customer | Expected |
|----------|----------|
| C001 | RETAIN, home-loan offer (OFFER-HL-FEE or OFFER-HL-RATE) |
| C004 | No lending offers; repayment support or none |
| C008 | OFFER-FD-RENEW |
| C010 | NO_ACTION, no active retention offer |

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | All validations passed |
| 1 | Seed count mismatch, scenario validation failure, or chat missing evidence |

## Related scripts

| Script | Purpose |
|--------|---------|
| `scripts/validate_project.py` | Deterministic business-rule validation |
| `scripts/run_demo_validation.py` | Bounded async event + notification validation |
| `scripts/smoke_test.py` | HTTP smoke test against running API |

## Docker demo workflow

1. `docker compose up -d`
2. Open http://localhost:8080
3. Navigate Portfolio → C001 → trigger analysis
4. Check Mailpit at http://localhost:8025 for alert emails
5. Use RM Copilot for natural-language explanations

See [VALIDATION.md](./VALIDATION.md) for full test matrix.
