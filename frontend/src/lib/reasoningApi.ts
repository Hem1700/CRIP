import type { SyncQueryResult } from '../types'

const BASE = import.meta.env.VITE_REASONING_API_URL ?? 'http://localhost:8001'
const TENANT_ID = 'demo-tenant'

function headers(): HeadersInit {
  return {
    'Content-Type': 'application/json',
    'X-Tenant-ID': TENANT_ID,
  }
}

// Calls POST /query/sync and unwraps the ApiResponse<QueryResult> wrapper.
export async function querySync(params: {
  question: string
  sessionId: string
}): Promise<SyncQueryResult> {
  const res = await fetch(`${BASE}/query/sync`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({
      question: params.question,
      tenant_id: TENANT_ID,
      session_id: params.sessionId,
    }),
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.url}`)
  const wrapper = (await res.json()) as { data: SyncQueryResult }
  return wrapper.data
}
