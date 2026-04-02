import { describe, it, expect } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ThreatHeatmap, buildCellMap } from '../features/dashboard/ThreatHeatmap'
import type { HeatmapData } from '../types'

function wrap(ui: React.ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={qc}>{ui}</QueryClientProvider>
}

describe('buildCellMap', () => {
  it('creates a map keyed by actorId:assetId', () => {
    const data: HeatmapData = {
      actors: [{ name: 'APT29', groupId: 'G0016' }],
      assets: [{ assetId: 'a-1', name: 'web-server-1' }],
      cells: [{
        actorName: 'APT29', actorId: 'G0016',
        assetName: 'web-server-1', assetId: 'a-1',
        pathCount: 3, intensity: 0.6,
      }],
    }
    const map = buildCellMap(data)
    expect(map.get('G0016:a-1')).toBe(0.6)
  })

  it('returns 0 for unknown actor/asset pair', () => {
    const map = buildCellMap({ actors: [], assets: [], cells: [] })
    expect(map.get('x:y') ?? 0).toBe(0)
  })
})

describe('ThreatHeatmap component', () => {
  it('renders heatmap container after load', async () => {
    render(wrap(<ThreatHeatmap />))
    await waitFor(() =>
      expect(screen.getByTestId('heatmap-container')).toBeInTheDocument()
    )
  })

  it('shows section heading', async () => {
    render(wrap(<ThreatHeatmap />))
    await waitFor(() =>
      expect(screen.getByText('Threat Heatmap')).toBeInTheDocument()
    )
  })
})
