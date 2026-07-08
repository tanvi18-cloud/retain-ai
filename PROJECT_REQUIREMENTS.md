# RetainAI — Project Requirements

## Overview

RetainAI is a functional agentic AI customer-retention copilot for retail banking Relationship Managers (RMs). It helps RMs identify at-risk customers, understand eligibility for retention offers, and receive AI-assisted explanations and recommendations—all using synthetic data only.

## Problem Statement

Relationship Managers in retail banking need timely, actionable insight into customer churn risk and approved retention options. Manual portfolio review is slow, inconsistent, and hard to scale. RetainAI provides a unified copilot that combines deterministic scoring, approved-offer lookup, and LLM-powered explanation—without allowing the AI to override business rules or invent offers.

## Target Users

- **Relationship Managers** — primary users; monitor portfolios, review alerts, chat with the copilot, and act on retention opportunities.
- **Developers / QA** — run the stack locally with mock LLM mode and synthetic data for development and testing.

## Technology Stack

### Backend

| Component | Choice |
|-----------|--------|
| Language | Python 3.11 |
| API framework | FastAPI |
| ORM / models | SQLModel |
| Database | SQLite (MVP; designed for later replacement) |
| Configuration | Pydantic Settings |
| Agent framework | CrewAI |
| LLM | Qwen via OpenAI-compatible endpoint |
| Async processing | `asyncio.Queue` (MVP) |
| Real-time alerts | WebSockets |
| Email (dev) | SMTP |
| Testing | pytest |
| Linting | Ruff |

### Frontend

| Component | Choice |
|-----------|--------|
| Framework | React |
| Language | TypeScript (strict; no `any`) |
| Build tool | Vite |
| Styling | Tailwind CSS |
| Routing | React Router |
| Data fetching | TanStack Query |
| Charts | Recharts |
| Icons | Lucide React |
| Toasts | Sonner |

## Core Principles

1. **Synthetic data only** — never use real customer banking data in source code or fixtures meant for the repo.
2. **No real credentials** — never commit real banking credentials or personal data.
3. **Deterministic scoring** — credit eligibility and numerical scores are computed by deterministic services, not by the LLM.
4. **LLM explains, does not score** — the LLM may explain and recommend but must not change calculated scores.
5. **Approved offers only** — the LLM may only recommend offers returned by the approved-offer service.
6. **Structured AI output** — every AI response must conform to a Pydantic schema.
7. **Mock LLM mode** — the application must run fully with `MOCK_LLM_MODE=true` (no live LLM required).
8. **No arbitrary SQL from chat** — the chat agent must not execute arbitrary SQL.
9. **MVP scope** — do not use Kafka, Redis, Celery, Kubernetes, vector databases, or microservices in this MVP.
10. **Modular design** — keep persistence and queue abstractions swappable (SQLite → PostgreSQL, in-memory queue → external broker later).
11. **Python quality** — type hints and docstrings on important functions.
12. **TypeScript quality** — strict mode; avoid `any`.
13. **Test coverage** — tests for every business-critical service.
14. **Explicit errors** — do not silently catch exceptions.
15. **Verified APIs** — inspect installed package versions before using CrewAI-specific classes or decorators; do not invent package APIs.
16. **Current CrewAI imports** — do not use deprecated CrewAI imports.
17. **Living docs** — keep `README.md` and `IMPLEMENTATION_STATUS.md` updated after each phase.
18. **Green tests gate** — do not proceed to the next phase while existing tests fail.
19. **Stable API contracts** — keep API response shapes stable and documented.
20. **Small diffs** — prefer small, reviewable changes over unrelated rewrites.

## Functional Requirements (High Level)

### Customer & Portfolio

- Store and serve synthetic customer profiles, accounts, and interaction history.
- Support RM portfolio views with filtering and search.

### Churn & Retention Scoring

- Deterministic churn-risk and credit-eligibility scoring services.
- Scores exposed via API; auditable calculation inputs/outputs.

### Approved Offers

- Central approved-offer service returns the only offers the system (and LLM) may reference.
- Offers tied to eligibility rules; no free-form offer invention.

### Agentic Copilot

- CrewAI-based agent(s) for RM chat and batch insight generation.
- All agent outputs validated against Pydantic schemas.
- `MOCK_LLM_MODE=true` returns deterministic mock responses.

### Alerts & Notifications

- Background processing via `asyncio.Queue` for scoring refresh, alert generation, etc.
- WebSocket channel for live alerts to the frontend.
- SMTP-based email notifications for development.

### Frontend

- Dashboard for portfolio health, alerts, and customer detail.
- Chat interface for the retention copilot.
- Charts (Recharts) for trends and score distributions.

## Non-Functional Requirements

- Runnable locally with minimal external dependencies (SQLite, optional SMTP, optional LLM endpoint).
- Environment-based configuration via Pydantic Settings.
- Ruff-clean Python; strict TypeScript on the frontend.
- pytest suite covering business-critical paths.

## Out of Scope (MVP)

- Kafka, Redis, Celery, Kubernetes
- Vector databases and RAG over external document stores
- Microservices decomposition
- Real banking integrations or production PII
- Arbitrary SQL execution from natural-language chat

## Documentation Artifacts

| File | Purpose |
|------|---------|
| `README.md` | Project overview, architecture, setup |
| `PROJECT_REQUIREMENTS.md` | This document — requirements and principles |
| `IMPLEMENTATION_STATUS.md` | Phase tracking, validation commands, next steps |

## Implementation Phases (Planned)

Phases will be recorded in `IMPLEMENTATION_STATUS.md` as work progresses. Expected rough order:

1. **Phase 0** — Repository scaffolding and documentation (current)
2. **Phase 1** — Backend foundation (FastAPI, SQLModel, settings, synthetic seed data)
3. **Phase 2** — Business services (scoring, offers, queue workers)
4. **Phase 3** — CrewAI agents and mock LLM mode
5. **Phase 4** — WebSockets, SMTP alerts
6. **Phase 5** — Frontend shell and API integration
7. **Phase 6** — Dashboard, chat UI, polish and end-to-end tests
