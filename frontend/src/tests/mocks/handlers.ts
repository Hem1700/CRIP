import { http, HttpResponse } from 'msw'
import type { FindingsData, HeatmapData, Persona, PostureData, SimulationResult } from '../../types'

const POSTURE: PostureData = {
  riskScore: 742,
  totalAssets: 128,
  totalVulnerabilities: 347,
  edrCoveragePct: 68.4,
  patchCoveragePct: 55.2,
  criticalAssets: 12,
}

const HEATMAP: HeatmapData = {
  actors: [{ name: 'APT29 (Cozy Bear)', groupId: 'G0016' }],
  assets: [{ assetId: 'a-1', name: 'web-server-1' }],
  cells: [{
    actorName: 'APT29 (Cozy Bear)', actorId: 'G0016',
    assetName: 'web-server-1', assetId: 'a-1',
    pathCount: 3, intensity: 0.6,
  }],
}

const FINDINGS: FindingsData = {
  findings: [{
    assetId: 'a-1', assetName: 'web-server-1', assetCriticality: 9,
    cveId: 'CVE-2024-1234', cvss: 9.8, epss: 0.94,
    exploitAvailable: true, patchAvailable: true,
    riskScore: 9.2, severity: 'critical',
  }],
  pagination: { page: 1, pageSize: 20, total: 1, totalPages: 1 },
}

const PERSONA: Persona = {
  groupId: 'G0016',
  name: 'APT29 (Cozy Bear)',
  origin: 'Russia',
  primarySectors: ['Government', 'Healthcare'],
  motivations: ['Espionage', 'Intelligence Collection'],
  signatureTTPs: [
    { techniqueId: 'T1566.001', name: 'Spearphishing Attachment' },
    { techniqueId: 'T1059.001', name: 'PowerShell' },
  ],
  sophistication: 'nation-state',
  version: 1,
}

const SIMULATION: SimulationResult = {
  jobId: 'j-abc123',
  personaId: 'G0016',
  personaName: 'APT29 (Cozy Bear)',
  status: 'completed',
  result: {
    personaName: 'APT29 (Cozy Bear)',
    personaId: 'G0016',
    tenantId: 'demo-tenant',
    totalAssetsScanned: 128,
    vulnerableAssets: 42,
    attackPaths: [[{
      phase: 'initial-access',
      techniqueId: 'T1566.001',
      techniqueName: 'Spearphishing Attachment',
      targetAssetId: 'a-1',
      targetAssetName: 'web-server-1',
      successProbability: 0.7,
      notes: 'Phase: initial-access, Criticality: 9',
    }]],
    riskScore: 55.3,
    summary: 'APT29 simulation found 42 vulnerable assets out of 128 total.',
  },
}

export const handlers = [
  http.get('http://localhost:8003/dashboard/posture', () =>
    HttpResponse.json(POSTURE)
  ),

  http.get('http://localhost:8003/dashboard/heatmap', () =>
    HttpResponse.json(HEATMAP)
  ),

  http.get('http://localhost:8003/dashboard/findings', () =>
    HttpResponse.json(FINDINGS)
  ),

  http.post('http://localhost:8003/reports/generate', () =>
    HttpResponse.json({ reportId: 'r-abc123', status: 'completed', riskScore: 742 })
  ),

  http.get('http://localhost:8002/personas', () =>
    HttpResponse.json([PERSONA])
  ),

  http.get('http://localhost:8002/personas/:id', () =>
    HttpResponse.json({ current: PERSONA, versions: [PERSONA] })
  ),

  http.post('http://localhost:8002/personas/:id/simulate', () =>
    HttpResponse.json(SIMULATION)
  ),

  http.post('http://localhost:8001/query/sync', () =>
    HttpResponse.json({
      data: {
        answer: 'Your highest risk assets are web-server-1 and db-prod-2.',
        confidence: 0.91,
        citations: ['CVE-2024-1234'],
        intent: 'attack_path',
      },
      meta: {
        requestId: 'req-1',
        tenantId: 'demo-tenant',
        durationMs: 450,
        confidence: 0.91,
      },
      errors: [],
    })
  ),
]
