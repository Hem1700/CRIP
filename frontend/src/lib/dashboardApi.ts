import type { FindingsData, HeatmapData, PostureData, ReportResult } from '../types'

const BASE = import.meta.env.VITE_DASHBOARD_API_URL ?? 'http://localhost:8003'
const TENANT_ID = 'demo-tenant'

function headers(): HeadersInit {
  return {
    'Content-Type': 'application/json',
    'X-Tenant-ID': TENANT_ID,
  }
}

async function demand<T>(res: Response): Promise<T> {
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.url}`)
  return res.json() as Promise<T>
}

export async function fetchPosture(): Promise<PostureData> {
  return demand<PostureData>(
    await fetch(`${BASE}/dashboard/posture`, { headers: headers() })
  )
}

export async function fetchHeatmap(): Promise<HeatmapData> {
  return demand<HeatmapData>(
    await fetch(`${BASE}/dashboard/heatmap`, { headers: headers() })
  )
}

export async function fetchFindings(params: {
  severity?: string
  status?: string
  page?: number
  pageSize?: number
}): Promise<FindingsData> {
  const url = new URL(`${BASE}/dashboard/findings`)
  if (params.severity) url.searchParams.set('severity', params.severity)
  if (params.status) url.searchParams.set('status', params.status)
  if (params.page != null) url.searchParams.set('page', String(params.page))
  if (params.pageSize != null) url.searchParams.set('page_size', String(params.pageSize))
  return demand<FindingsData>(await fetch(url.toString(), { headers: headers() }))
}

export async function generateReport(): Promise<ReportResult> {
  return demand<ReportResult>(
    await fetch(`${BASE}/reports/generate`, { method: 'POST', headers: headers() })
  )
}
