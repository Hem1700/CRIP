import type { Persona, PersonaDetail, SimulationResult } from '../types'

const BASE = import.meta.env.VITE_PERSONA_API_URL ?? 'http://localhost:8002'
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

export async function listPersonas(): Promise<Persona[]> {
  return demand<Persona[]>(await fetch(`${BASE}/personas`, { headers: headers() }))
}

export async function getPersona(groupId: string): Promise<PersonaDetail> {
  return demand<PersonaDetail>(
    await fetch(`${BASE}/personas/${encodeURIComponent(groupId)}`, { headers: headers() })
  )
}

export async function simulatePersona(groupId: string): Promise<SimulationResult> {
  return demand<SimulationResult>(
    await fetch(`${BASE}/personas/${encodeURIComponent(groupId)}/simulate`, {
      method: 'POST',
      headers: headers(),
      body: JSON.stringify({ tenant_id: TENANT_ID }),
    })
  )
}
