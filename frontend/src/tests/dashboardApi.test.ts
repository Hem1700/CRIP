import { describe, it, expect } from 'vitest'
import { http, HttpResponse } from 'msw'
import { server } from './mocks/server'
import {
  fetchPosture,
  fetchHeatmap,
  fetchFindings,
  generateReport,
} from '../lib/dashboardApi'

describe('dashboardApi', () => {
  it('fetchPosture returns posture data', async () => {
    const data = await fetchPosture()
    expect(data.riskScore).toBe(742)
    expect(data.totalAssets).toBe(128)
    expect(data.edrCoveragePct).toBe(68.4)
  })

  it('fetchHeatmap returns actors, assets, cells', async () => {
    const data = await fetchHeatmap()
    expect(data.actors).toHaveLength(1)
    expect(data.cells[0].intensity).toBe(0.6)
  })

  it('fetchFindings passes severity filter in query string', async () => {
    let capturedUrl = ''
    server.use(
      http.get('http://localhost:8003/dashboard/findings', ({ request }) => {
        capturedUrl = request.url
        return HttpResponse.json({
          findings: [],
          pagination: { page: 1, pageSize: 20, total: 0, totalPages: 0 },
        })
      })
    )
    await fetchFindings({ severity: 'critical', page: 2 })
    expect(capturedUrl).toContain('severity=critical')
    expect(capturedUrl).toContain('page=2')
  })

  it('fetchFindings omits severity param when not provided', async () => {
    let capturedUrl = ''
    server.use(
      http.get('http://localhost:8003/dashboard/findings', ({ request }) => {
        capturedUrl = request.url
        return HttpResponse.json({
          findings: [],
          pagination: { page: 1, pageSize: 20, total: 0, totalPages: 0 },
        })
      })
    )
    await fetchFindings({ page: 1 })
    expect(capturedUrl).not.toContain('severity=')
  })

  it('generateReport sends POST and returns reportId', async () => {
    const result = await generateReport()
    expect(result.reportId).toBe('r-abc123')
    expect(result.status).toBe('completed')
  })

  it('fetchPosture throws on non-ok response', async () => {
    server.use(
      http.get('http://localhost:8003/dashboard/posture', () =>
        HttpResponse.json({}, { status: 503 })
      )
    )
    await expect(fetchPosture()).rejects.toThrow('503')
  })
})
