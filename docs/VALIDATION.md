# RetainAI Validation Guide

This document describes the end-to-end validation scope for the RetainAI MVP, expected demo outcomes, security checks, and how to interpret validation script results.

## Validation Scope

Phase 9 validation covers:

- Backend business-rule correctness (deterministic scoring, eligibility, flow routing)
- Event-to-alert workflows with mock LLM mode
- Recommendation lifecycle and RM chat guardrails
- Data integrity and referential consistency after seed and processing
- API and UI security guardrails (no credential leakage, no unsafe agent actions)
- Frontend integration workflows with mocked HTTP/WebSocket
- Performance smoke checks with relaxed local/CI thresholds

Validation intentionally does **not** require a live Qwen endpoint. All agentic paths run with `MOCK_LLM_MODE=true`.

## Tested Business Scenarios

| Customer | Scenario | Expected outcome |
|----------|----------|------------------|
| **C001** | External home-loan inquiry / urgent retention | `RETAIN`, home-loan offer (`OFFER-HL-FEE` or `OFFER-HL-RATE`), alert created, crew runs |
| **C004** | 60 DPD credit restriction | No new lending offer; repayment support allowed; policy warnings present |
| **C008** | Fixed-deposit maturity | FD renewal offer (`OFFER-FD-RENEW`), non-negative expected net benefit |
| **C010** | Stable no-action customer | `NO_ACTION`, crew skipped, no retention offer, no agent alert |

Additional workflow coverage:

- RM recommendation lifecycle: review → approve → contacted → close
- RM chat follow-up with preserved customer context and evidence citations
- Event retry idempotency (no duplicate recommendations/alerts)

## Security Checks

Validation confirms:

1. API responses do not expose API keys, SMTP passwords, DB URLs, auth headers, or stack traces
2. Recommendation and chat responses exclude chain-of-thought and hidden prompts
3. Agent/chat tools remain read-only (no customer writes, approvals, email, or arbitrary SQL)
4. LLM output cannot override deterministic scores or eligibility
5. UI shows synthetic-data, eligibility, and approval disclaimers

## Known MVP Limitations

- SQLite and in-memory `asyncio.Queue` are non-durable
- Seed data is not auto-loaded on API startup (`scripts/reset_database.py --reset`)
- Revenue-by-product charts use estimated groupings, not ledger truth
- Email delivery depends on local SMTP (Mailhog recommended); validation mocks SMTP where needed
- WebSocket reconnect behavior requires a running backend for manual demos

## Running Validation Scripts

From the repository root:

```bash
cd backend
uv sync --all-groups
uv run python ../scripts/validate_project.py
uv run python ../scripts/run_demo_validation.py
```

### `validate_project.py`

1. Resets and seeds a temporary validation database
2. Verifies exactly 10 customers and 8 offers
3. Runs agentic analysis for C001, C004, C008, C010
4. Prints a results table with scores, decision, offer, and pass/fail status

**Exit codes:** `0` = all checks passed, non-zero = at least one failure

### `run_demo_validation.py`

Runs a broader demo workflow:

1. C001 `EXTERNAL_HOME_LOAN_INQUIRY` event through the event processor
2. Notification attempt (email mocked)
3. RM chat questions for C001
4. Guardrail checks for C004, C008, C010

Uses bounded polling (no infinite loops).

## Interpreting Results

- **PASS** on a row/check means measured values matched expected business rules
- **FAIL** includes detail lines explaining the mismatch (decision, offer ID, missing alert, etc.)
- A passing validation run does not imply production readiness — it confirms MVP demo behavior under synthetic data and mock LLM mode

## Mock Mode Requirement

Set `MOCK_LLM_MODE=true` (default in `.env.example`) before validation. Scripts force mock mode internally, but the backend server used for manual UI demos should also run with mock mode unless explicitly testing live Qwen connectivity.

## Related Documentation

- [TESTING.md](./TESTING.md) — pytest/Vitest commands and fixture strategy
- [../IMPLEMENTATION_STATUS.md](../IMPLEMENTATION_STATUS.md) — current phase and known issues
