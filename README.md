# RetainAI

**Agentic AI customer-retention copilot for retail banking Relationship Managers**

RetainAI helps Relationship Managers proactively retain customers by surfacing churn risk, deterministic eligibility scores, and AI-assisted explanations grounded in approved retention offers—all powered by synthetic data for safe local development.

## Problem Statement

Retail banking Relationship Managers manage large customer portfolios under time pressure. Identifying who is at risk of leaving, which retention offers apply, and how to prioritize outreach is often manual and inconsistent. RetainAI combines deterministic business logic (scoring, eligibility, approved offers) with an agentic copilot that explains insights and recommends next steps—without letting the LLM alter scores or invent offers.

## Architecture Summary

```text
┌─────────────────────────────────────────────────────────────────┐
│                     React + TypeScript (Vite)                   │
│   Dashboard · Portfolio · Alerts (WebSocket) · Copilot Chat     │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST / WebSocket
┌────────────────────────────▼────────────────────────────────────┐
│                      FastAPI (Python 3.11)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │ Scoring      │  │ Approved     │  │ CrewAI Agents        │ │
│  │ (deterministic)│ │ Offers       │  │ (Pydantic outputs)   │ │
│  └──────────────┘  └──────────────┘  └──────────────────────┘ │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │ asyncio.Queue│  │ WebSockets   │  │ SMTP (dev alerts)    │ │
│  └──────────────┘  └──────────────┘  └──────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │ SQLite (MVP)    │
                    │ Synthetic data  │
                    └─────────────────┘
```

### Key design constraints

- **Deterministic scoring** — churn and credit eligibility are computed by services, not the LLM.
- **Approved offers only** — the copilot may recommend only offers from the approved-offer service.
- **Structured AI output** — all LLM responses validate against Pydantic schemas.
- **Mock mode** — set `MOCK_LLM_MODE=true` to run without a live LLM.
- **MVP simplicity** — SQLite, in-memory `asyncio.Queue`; no Kafka, Redis, Celery, or microservices.

See [PROJECT_REQUIREMENTS.md](./PROJECT_REQUIREMENTS.md) for the full requirements list and [IMPLEMENTATION_STATUS.md](./IMPLEMENTATION_STATUS.md) for current progress.

## Prerequisites

<!-- To be filled in Phase 1+ -->

## Backend Setup

<!-- To be filled in Phase 1 -->

## Frontend Setup

<!-- To be filled in Phase 5 -->

## Environment Variables

<!-- To be filled in Phase 1 -->

## Running Tests

<!-- To be filled in Phase 1 -->

## Development Workflow

<!-- To be filled in as phases complete -->

## License

<!-- TBD -->
