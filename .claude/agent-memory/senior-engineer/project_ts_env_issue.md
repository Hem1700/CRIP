---
name: Pre-existing import.meta.env TypeScript errors
description: All API client files in frontend/src/lib/ have TS2339 errors on import.meta.env — pre-existing issue, not introduced per-task
type: project
---

`npx tsc --noEmit` from `frontend/` reports 4 errors (one per API client file: dashboardApi.ts, personaApi.ts, reasoningApi.ts, wsClient.ts), all `TS2339: Property 'env' does not exist on type 'ImportMeta'`.

**Why:** The tsconfig.json does not include `"vite/client"` in its `lib` or `types` — Vite's `ImportMeta` augmentation is missing.

**How to apply:** When a future task requires fixing or auditing TypeScript errors, add `"types": ["vite/client"]` (or `/// <reference types="vite/client" />`) to resolve these 4 errors. Do not count them as regressions introduced by individual tasks.
