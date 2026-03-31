// All shared TypeScript types mirroring backend response shapes.

export interface PostureData {
  riskScore: number
  totalAssets: number
  totalVulnerabilities: number
  edrCoveragePct: number
  patchCoveragePct: number
  criticalAssets: number
}

export interface HeatmapActor {
  name: string
  groupId: string
}

export interface HeatmapAsset {
  assetId: string
  name: string
}

export interface HeatmapCell {
  actorName: string
  actorId: string
  assetName: string
  assetId: string
  pathCount: number
  intensity: number
}

export interface HeatmapData {
  actors: HeatmapActor[]
  assets: HeatmapAsset[]
  cells: HeatmapCell[]
}

export interface Finding {
  assetId: string
  assetName: string
  assetCriticality: number
  cveId: string
  cvss: number
  epss: number
  exploitAvailable: boolean
  patchAvailable: boolean
  riskScore: number
  severity: 'critical' | 'high' | 'medium' | 'low'
}

export interface FindingsData {
  findings: Finding[]
  pagination: {
    page: number
    pageSize: number
    total: number
    totalPages: number
  }
}

export interface ReportResult {
  reportId: string
  status: string
  riskScore: number
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  confidence?: number
  citations?: string[]
}

export interface TTP {
  techniqueId: string
  name: string
}

export interface Persona {
  groupId: string
  name: string
  origin: string
  primarySectors: string[]
  motivations: string[]
  signatureTTPs: TTP[]
  sophistication: string
  version: number
  createdAt?: string
  updatedAt?: string
}

export interface PersonaDetail {
  current: Persona
  versions: Persona[]
}

export interface AttackStep {
  phase: string
  techniqueId: string
  techniqueName: string
  targetAssetId: string
  targetAssetName: string
  successProbability: number
  notes: string
}

export interface SimulationResult {
  jobId: string
  personaId: string
  personaName: string
  status: string
  result: {
    personaName: string
    personaId: string
    tenantId: string
    totalAssetsScanned: number
    vulnerableAssets: number
    attackPaths: AttackStep[][]
    riskScore: number
    summary: string
  }
}

export interface SyncQueryResult {
  answer: string
  confidence: number
  citations: string[]
  intent: string
}
