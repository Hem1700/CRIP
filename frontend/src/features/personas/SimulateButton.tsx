import { useState } from 'react'
import { simulatePersona } from '../../lib/personaApi'
import { Button } from '../../components/ui/Button'
import type { SimulationResult } from '../../types'

interface Props {
  groupId: string
  personaName: string
}

export function SimulateButton({ groupId, personaName }: Props) {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<SimulationResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [expanded, setExpanded] = useState(false)

  async function handleSimulate() {
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const data = await simulatePersona(groupId)
      setResult(data)
      setExpanded(true)
    } catch {
      setError('Simulation failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <Button size="sm" onClick={() => void handleSimulate()} disabled={loading}>
        {loading ? 'Running…' : 'Simulate'}
      </Button>
      {error && (
        <p className="text-xs text-red-600 dark:text-red-400 mt-1">{error}</p>
      )}
      {result && (
        <div className="mt-3">
          <button
            className="text-xs font-medium text-gray-700 dark:text-gray-300 flex items-center gap-1"
            onClick={() => setExpanded((e) => !e)}
          >
            {expanded ? '▼' : '▶'} {personaName} Simulation Results
          </button>
          {expanded && (
            <div className="mt-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 p-3 text-xs space-y-2">
              <p className="text-gray-700 dark:text-gray-300">{result.result.summary}</p>
              <p className="text-gray-500 dark:text-gray-400">
                Scanned {result.result.totalAssetsScanned} assets
                · Risk: {result.result.riskScore}/100
              </p>
              {result.result.attackPaths.length > 0 && (
                <div>
                  <p className="font-medium text-gray-700 dark:text-gray-300 mb-1">Top attack path:</p>
                  <ol className="space-y-1 list-decimal list-inside">
                    {result.result.attackPaths[0].map((step, i) => (
                      <li key={i} className="text-gray-600 dark:text-gray-400">
                        <span className="font-medium">{step.phase}</span>
                        {' → '}
                        {step.targetAssetName}
                        {step.techniqueId && (
                          <span className="text-gray-400"> ({step.techniqueId})</span>
                        )}
                        <span className="text-gray-400"> p={step.successProbability}</span>
                      </li>
                    ))}
                  </ol>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
