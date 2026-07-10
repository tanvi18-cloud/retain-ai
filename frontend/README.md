# RetainAI Frontend

React + TypeScript + Vite frontend for the RetainAI customer-retention copilot.

## Stack

- React 19 with strict TypeScript
- Vite 8
- Tailwind CSS (`@tailwindcss/vite` plugin)
- React Router, TanStack Query, Recharts, Lucide React, Sonner
- Vitest, Testing Library, MSW

## Setup

```bash
cd frontend
cp .env.example .env
npm install
```

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `VITE_API_BASE_URL` | `http://127.0.0.1:8001/api/v1` | Backend API base URL |
| `VITE_WS_BASE_URL` | _(derived from API URL)_ | WebSocket alerts endpoint |
| `VITE_APP_NAME` | `RetainAI` | Shell title |
| `VITE_APP_VERSION` | `0.1.0` | Version label |
| `VITE_USE_MOCK_DATA` | `false` | Reserved for future mock mode |
| `VITE_RM_ID` | `RM-01` | RM identifier for chat/acknowledgements |
| `VITE_RM_NAME` | `RM User` | RM display name |
| `VITE_ENABLE_SIMULATOR` | `true` | Show event simulator nav |
| `VITE_ENABLE_SYSTEM_PAGE` | `true` | Show system status nav |

## Commands

```bash
# Development server (http://localhost:5173)
npm run dev

# Production build
npm run build

# Unit tests
npm run test -- --run

# Preview production build
npm run preview

# Lint
npm run lint
```

## Routes

| Path | Page |
|------|------|
| `/` | Portfolio command center |
| `/customers` | Customer directory |
| `/customers/:customerId` | Customer 360 |
| `/alerts` | Coming soon (Prompt 13) |
| `/copilot` | Coming soon (Prompt 13) |
| `/simulator` | Coming soon (Prompt 13) |
| `/system` | Coming soon (Prompt 13) |

## Project structure

```text
frontend/src/
  api/           # Typed API client and endpoint modules
  components/
    layout/      # App shell, navigation, page header
    ui/          # Reusable UI primitives
    charts/      # Portfolio charts
    customers/   # Customer 360 panels
  hooks/
  pages/
  routes/
  types/
  utils/
  test/          # Vitest setup, MSW handlers, fixtures
```

## Status

Phase 7 core dashboard is implemented. WebSocket alerts, copilot chat, event simulator, and system status pages are deferred to Prompt 13.
