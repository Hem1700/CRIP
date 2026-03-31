import { describe, it, expect } from 'vitest'
import { http, HttpResponse } from 'msw'
import { server } from './mocks/server'
import { listPersonas, getPersona, simulatePersona } from '../lib/personaApi'

describe('personaApi', () => {
  it('listPersonas returns persona array', async () => {
    const personas = await listPersonas()
    expect(personas).toHaveLength(1)
    expect(personas[0].groupId).toBe('G0016')
    expect(personas[0].name).toBe('APT29 (Cozy Bear)')
  })

  it('getPersona returns current and versions', async () => {
    const detail = await getPersona('G0016')
    expect(detail.current.groupId).toBe('G0016')
    expect(detail.versions).toHaveLength(1)
  })

  it('simulatePersona sends POST with tenant_id body', async () => {
    let body: unknown = null
    server.use(
      http.post('http://localhost:8002/personas/:id/simulate', async ({ request }) => {
        body = await request.json()
        return HttpResponse.json({
          jobId: 'j-1', personaId: 'G0016', personaName: 'APT29',
          status: 'completed',
          result: {
            personaName: 'APT29', personaId: 'G0016', tenantId: 'demo-tenant',
            totalAssetsScanned: 10, vulnerableAssets: 3, attackPaths: [], riskScore: 30, summary: 'ok',
          },
        })
      })
    )
    await simulatePersona('G0016')
    expect(body).toEqual({ tenant_id: 'demo-tenant' })
  })

  it('simulatePersona returns attackPaths from result', async () => {
    const result = await simulatePersona('G0016')
    expect(result.result.attackPaths).toHaveLength(1)
    expect(result.result.riskScore).toBe(55.3)
  })

  it('listPersonas throws on 500', async () => {
    server.use(
      http.get('http://localhost:8002/personas', () =>
        HttpResponse.json({}, { status: 500 })
      )
    )
    await expect(listPersonas()).rejects.toThrow('500')
  })
})
