# Architecture — RetainAI

Agentic AI customer-retention copilot for retail banking RMs. **Synthetic data only** in this MVP.

## System context

```mermaid
flowchart TB
    RM[Relationship Manager] --> UI[React Frontend]
    UI -->|REST /api/v1| API[FastAPI Backend]
    UI -->|WebSocket /ws/alerts| API
    API --> DB[(SQLite)]
    API --> Qwen[Qwen LLM optional]
    API --> SMTP[SMTP / Mailpit]
    subgraph External Demo
        Mailpit[Mailpit UI :8025]
    end
    SMTP --> Mailpit
```

## Layer overview

| Layer | Technology | Responsibility |
|-------|------------|----------------|
| Frontend | React, TypeScript, Vite | Dashboard, 360, alerts, copilot, simulator |
| API | FastAPI | REST, WebSocket, validation, thin routers |
| Persistence | SQLModel + SQLite | Customers, events, recommendations, audit |
| Rules engine | Python services | Churn, value, priority, eligibility (deterministic) |
| Agents | CrewAI + Pydantic | Narrative reasoning, offer framing, chat |
| Flow | CrewAI Flow | Route full crew vs. lightweight path |
| Queue | asyncio.Queue | Async event processing (non-durable) |
| LLM | Qwen via OpenAI-compatible API | Optional; mock mode default |
| Notifications | WebSocket + SMTP | Real-time alerts + email |

## Data ingestion

```mermaid
sequenceDiagram
    participant Sim as Simulator / API
    participant API as Events API
    participant Q as asyncio.Queue
    participant P as EventProcessor
    participant F as RetentionFlow
    Sim->>API: POST /events (202)
    API->>Q: enqueue(event_id)
    Q->>P: process event
    P->>F: run_retention_flow
    F-->>P: recommendation + alert
    P-->>API: COMPLETED status
```

Events: bureau triggers, manual reanalysis, CRM signals. Payloads validated per `EventType`.

## Customer 360

```mermaid
flowchart LR
    C[Customer ID] --> Repo[CustomerRepository]
    Repo --> Core[Core banking snapshot]
    Repo --> Credit[Credit profile]
    Repo --> Bureau[Bureau triggers]
    Repo --> Txn[Transaction features]
    Repo --> Offers[Approved offers]
    Core & Credit & Bureau & Txn --> View[Customer360Response]
```

Aggregates read-only snapshots; no raw transaction dump in API responses.

## Deterministic decision engine

```mermaid
flowchart TD
    A[Customer 360] --> Churn[ChurnScoringService]
    A --> Value[ValueScoringService]
    Churn --> Priority[PriorityService]
    Value --> Priority
    Priority --> Decision{Decision}
    Decision -->|score thresholds| RETAIN
    Decision --> REVIEW
    Decision --> NO_ACTION
    A --> Elig[EligibilityService]
    Elig --> Offers[Filtered approved offers]
```

**Design decision:** Rules remain deterministic so regulatory explainability and auditability are preserved. Scores are reproducible without LLM variance.

## CrewAI agent sequence

Four agents (mock or live Qwen):

1. **Retention Analyst** — interprets signals and context
2. **Offer Strategist** — selects from eligible offers only
3. **Risk Advisor** — policy warnings and guardrails
4. **RM Communicator** — customer-facing narrative

Agents output **Pydantic-validated** structures. They do **not** compute eligibility or invent offer IDs.

**Design decision:** Agents do not control eligibility — prevents LLM hallucination from bypassing credit policy.

## CrewAI Flow routing

```mermaid
flowchart TD
    Start[Flow start] --> Rules[Rules-only analysis]
    Rules --> Pri{Priority >= threshold?}
    Pri -->|No| Light[Lightweight path]
    Pri -->|Yes| Full[Full crew execution]
    Light --> Persist[Persist recommendation]
    Full --> Persist
    Persist --> Alert[Create alert if priority met]
```

`RUN_FULL_CREW_MIN_PRIORITY` gates expensive crew runs.

## Event queue processing

```mermaid
flowchart LR
    W[Worker coroutines] --> Q[asyncio.Queue]
    Q --> EP[EventProcessor.process_sync]
    EP --> RF[run_retention_flow]
    RF --> NS[NotificationService]
```

**Design decision:** `asyncio.Queue` is sufficient for MVP demos but is **non-durable** — queued events are lost on process stop. Production requires Redis/RabbitMQ + workers.

## Alert and email pipeline

```mermaid
sequenceDiagram
    participant F as RetentionFlow
    participant A as AlertService
    participant N as NotificationService
    participant WS as WebSocketManager
    participant E as EmailService
    F->>A: create alert
    A->>N: deliver
    N->>WS: broadcast_retention_alert
    N->>E: send SMTP (Mailpit in demo)
```

Thresholds: `CREATE_ALERT_MIN_PRIORITY`, `SEND_EMAIL_MIN_PRIORITY`.

## RM chat

```mermaid
sequenceDiagram
    participant RM as RM Copilot UI
    participant API as Chat API
    participant CS as ChatService
    participant Tools as Bounded tools
    RM->>API: POST /chat
    CS->>Tools: customer lookup, recommendation lookup
    Tools-->>CS: evidence records
    CS-->>RM: answer + evidence (no chain-of-thought)
```

Mock mode returns deterministic answers with evidence citations.

## Recommendation lifecycle

```mermaid
stateDiagram-v2
    [*] --> PENDING: flow creates recommendation
    PENDING --> APPROVED: RM approve
    PENDING --> REJECTED: RM reject
    PENDING --> DEFERRED: RM defer
    APPROVED --> [*]
    REJECTED --> [*]
    DEFERRED --> PENDING: re-open
```

**Design decision:** RM approval remains mandatory — no automatic product booking or customer contact.

## Docker deployment

```mermaid
flowchart TB
    subgraph compose [docker-compose]
        FE[Nginx :8080]
        BE[FastAPI :8000]
        MP[Mailpit]
        VOL[(retainai_data)]
    end
    Browser --> FE
    FE -->|proxy /api /ws| BE
    BE --> VOL
    BE --> MP
    BE -.->|optional| HostQwen[host.docker.internal]
```

See [DOCKER_SETUP.md](./DOCKER_SETUP.md).

## Mock mode

`MOCK_LLM_MODE=true` (default):

- Skips live Qwen HTTP calls
- Returns schema-valid mock agent and chat outputs
- Enables CI, Docker, and offline demos

**Design decision:** Mock mode is required for reproducible validation without GPU infrastructure.

## Key modules (backend)

| Path | Role |
|------|------|
| `app/api/` | Thin HTTP routers |
| `app/services/` | Business logic |
| `app/repositories/` | Persistence queries |
| `app/agents/` | CrewAI agent definitions |
| `app/flows/` | Retention flow orchestration |
| `app/core/policy_rules.py` | Deterministic guardrails |
| `app/seed/` | Synthetic data |

## Key modules (frontend)

| Path | Role |
|------|------|
| `src/pages/` | Route-level views |
| `src/api/` | Typed API client |
| `src/hooks/` | WebSocket, polling |
| `src/components/` | UI building blocks |

Frontend contains **no** scoring or eligibility logic — display and RM actions only.
