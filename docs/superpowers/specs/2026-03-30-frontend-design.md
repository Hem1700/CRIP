# CRIP Frontend Design

**Date:** 2026-03-30
**Status:** Approved

## Overview

React 18 SPA for the Cyber Risk Intelligence Platform. Multi-page routing with three distinct views: Dashboard (CISO overview), Analyst (RAG chat), and Personas (APT persona management + kill-chain simulation). Light/dark theme toggle with localStorage persistence.

---

## Stack

| Tool | Purpose |
|------|---------|
| React 18 + Vite + TypeScript | App framework and build |
| React Router v6 | Multi-page routing (`/`, `/analyst`, `/personas`) |
| TailwindCSS + class-variance-authority | Styling and component variants |
| TanStack Query (React Query) | REST API calls with caching |
| Zustand | Theme state (light/dark), persisted to localStorage |
| Native WebSocket | Analyst chat streaming |
| Vitest + React Testing Library + msw | Unit testing |

---

## Project Layout

```
frontend/
  index.html
  vite.config.ts
  tailwind.config.ts
  src/
    app/                    ← router, providers, global layout
    features/
      dashboard/            ← PostureCard, ThreatHeatmap, FindingsTable, GenerateReportButton
      analyst/              ← ChatWindow, ChatInput, MessageBubble
      personas/             ← PersonaGrid, PersonaCard, PersonaDetail, SimulateButton
    components/
      ui/                   ← Button, Badge, Card, Table, Spinner
      layout/               ← Navbar, PageWrapper
    lib/
      ingestionApi.ts       ← http://localhost:8000
      reasoningApi.ts       ← http://localhost:8001
      personaApi.ts         ← http://localhost:8002
      dashboardApi.ts       ← http://localhost:8003
      wsClient.ts           ← ws://localhost:8001/query/ws
    store/
      themeStore.ts         ← Zustand theme store
    types/
      index.ts              ← TypeScript types mirroring backend schemas
```

---

## Pages & Components

### `/` — Dashboard

**PostureCard row:** Four stat cards side-by-side — Risk Score, Total Assets, Total Vulns, EDR Coverage %. Data from `GET /dashboard/posture`.

**ThreatHeatmap:** D3 matrix — rows are threat actors, columns are critical assets, cell color intensity = path count. Data from `GET /dashboard/heatmap`.

**FindingsTable:** Paginated table with severity filter (critical/high/medium/low) and status filter. Columns: Asset, CVE, CVSS, EPSS, Exploit Available (badge), Patch Available (badge), Risk Score. Data from `GET /dashboard/findings`.

**GenerateReportButton:** Calls `POST /reports/generate`. On success, shows inline report ID and download link.

---

### `/analyst` — Analyst

**ChatWindow:** Scrollable message history. User messages right-aligned, assistant messages left-aligned with markdown rendering. Each assistant message shows confidence score and citation pills (CVE IDs, asset names).

**ChatInput:** Textarea + send button. Connects via WebSocket on page mount with a UUID session ID. Falls back to `POST /query/sync` if WebSocket is unavailable.

Session ID is generated once on page mount and used for all messages in that session.

---

### `/personas` — Personas

**PersonaGrid:** Card grid. Each card shows group name, description, tactic badges.

**PersonaDetail:** Modal opened on card click. Shows full persona data and version history from `GET /personas/{id}`.

**SimulateButton:** On each card. Calls `POST /personas/{id}/simulate`. Shows kill-chain results (steps, matched assets) in an expandable panel inline below the card.

---

### Shared

**Navbar:** Links to all three pages with active link highlight. Theme toggle (sun/moon icon). Present on every page.

**PageWrapper:** Consistent padding and max-width container wrapping each page's content.

---

## Data Flow

### API Clients

All API modules are thin `fetch` wrappers that prepend the base URL and inject `X-Tenant-ID: demo-tenant` on every request. Base URLs are read from Vite env vars (`VITE_*_API_URL`) defaulting to localhost.

### React Query

- Dashboard: 3 parallel queries (`posture`, `heatmap`, `findings`), cached 30s, refetch on window focus
- Personas: 1 query for persona list; mutations for simulate and report generation
- Findings table: query re-runs when severity/status filter or page changes

### WebSocket (Analyst)

1. On page mount: open `ws://localhost:8001/query/ws` with `sessionId`
2. On send: write `{question, tenant_id, session_id}` as JSON
3. On message: stream tokens into the current assistant message bubble
4. On close/error: fall back silently to `POST /query/sync`

### Theme

Zustand store holds `theme: 'light' | 'dark'`, persisted to `localStorage`. On mount, applies `class="dark"` to `<html>`. Tailwind uses `darkMode: 'class'` strategy.

---

## Error Handling

| Scenario | Handling |
|----------|---------|
| React Query fetch failure | Inline `ErrorBanner` with retry button per feature — no full-page errors |
| WebSocket disconnect | Silent fallback to REST sync endpoint |
| Simulate mutation failure | Inline error message below the SimulateButton |
| Report generation failure | Inline error message below GenerateReportButton |

No global error boundary needed — each feature manages its own error state.

---

## Testing

- **Framework:** Vitest + React Testing Library
- **API mocking:** msw (Mock Service Worker) — no real network calls
- **One test file per feature:** `dashboard.test.tsx`, `analyst.test.tsx`, `personas.test.tsx`
- **What to test:**
  - PostureCard renders correct values from mocked posture response
  - FindingsTable severity filter triggers correct query params
  - SimulateButton shows kill-chain results on success, error message on failure
  - Chat appends user message immediately and streams assistant response
  - Theme toggle persists across remount
- No snapshot tests

---

## ASCII Mockups

### Navbar
```
┌─────────────────────────────────────────────────────────────────┐
│  CRIP        [Dashboard]  [Analyst]  [Personas]          [☀/🌙] │
└─────────────────────────────────────────────────────────────────┘
```

### Dashboard (`/`)
```
┌─────────────────────────────────────────────────────────────────┐
│  CRIP        [Dashboard]  [Analyst]  [Personas]          [☀/🌙] │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │Risk Score│  │  Assets  │  │  Vulns   │  │EDR Cover │       │
│  │   742    │  │   128    │  │   347    │  │  68.4%   │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
│  Threat Heatmap                                                 │
│  ┌───────────────────────────────────────────────┐             │
│  │          asset-1  asset-2  asset-3  asset-4   │             │
│  │  APT28  [████]   [██  ]   [    ]   [███ ]    │             │
│  │  APT29  [██  ]   [████]   [█   ]   [    ]    │             │
│  └───────────────────────────────────────────────┘             │
│  Findings  [critical ▼]  [open ▼]        [Generate Report]     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Asset         CVE            CVSS  EPSS  Exploit  Patch │   │
│  │ web-server-1  CVE-2024-1234  9.8   0.94  [YES]   [YES] │   │
│  │ db-prod-2     CVE-2023-5678  8.1   0.71  [YES]   [NO]  │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │  < 1 2 3 ... 12 >                                       │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Analyst (`/analyst`)
```
┌─────────────────────────────────────────────────────────────────┐
│  CRIP        [Dashboard]  [Analyst]  [Personas]          [☀/🌙] │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐   │
│  │   ┌─────────────────────────────────────────────────┐  │   │
│  │   │ What are my highest-risk assets?           [you] │  │   │
│  │   └─────────────────────────────────────────────────┘  │   │
│  │  ┌──────────────────────────────────────────────────┐  │   │
│  │  │[AI] Based on your graph, web-server-1 and        │  │   │
│  │  │     db-prod-2 carry the highest composite risk.. │  │   │
│  │  │     confidence: 0.91  [CVE-2024-1234] [APT28]   │  │   │
│  │  └──────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────┐  [Send ▶]    │
│  │ Ask about your environment...                │              │
│  └──────────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

### Personas (`/personas`)
```
┌─────────────────────────────────────────────────────────────────┐
│  CRIP        [Dashboard]  [Analyst]  [Personas]          [☀/🌙] │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │ APT28            │  │ APT29            │  │ Lazarus      │  │
│  │ [Recon][Exploit] │  │ [Phishing][C2]   │  │ [Ransomware] │  │
│  │ [View] [Simulate]│  │ [View] [Simulate]│  │[View][Simul.]│  │
│  └──────────────────┘  └──────────────────┘  └──────────────┘  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ ▼ APT28 Simulation Results                              │   │
│  │   1. Recon       → web-server-1 (CVE-2024-1234)        │   │
│  │   2. Exploit     → vpn-gw-1     (CVE-2023-5678)        │   │
│  │   3. Persistence → db-prod-2                           │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```
