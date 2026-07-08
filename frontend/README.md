# RetainAI Frontend

React + TypeScript + Vite frontend for the RetainAI customer-retention copilot.

## Stack

- React 19 with strict TypeScript
- Vite 8
- Tailwind CSS (`@tailwindcss/vite` plugin)
- React Router, TanStack Query, Recharts, Lucide React, Sonner

## Setup

From the repository root:

```bash
cp .env.example .env
cd frontend
npm install
```

## Commands

```bash
# Development server (http://localhost:5173)
npm run dev

# Production build
npm run build

# Preview production build
npm run preview

# Lint
npm run lint
```

## Project structure

```text
frontend/
  src/
    lib/       # Shared utilities (e.g. cn helper)
    App.tsx    # Root component
    main.tsx   # Entry point with providers
```

## Status

Scaffold only — dashboard, portfolio views, and copilot chat are added in later phases.
