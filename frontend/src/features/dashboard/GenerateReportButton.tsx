import { useState } from 'react'
import { generateReport } from '../../lib/dashboardApi'
import { Button } from '../../components/ui/Button'
import type { ReportResult } from '../../types'

export function GenerateReportButton() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<ReportResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function handleClick() {
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const data = await generateReport()
      setResult(data)
    } catch {
      setError('Failed to generate report')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex items-center gap-3">
      <Button onClick={() => void handleClick()} disabled={loading}>
        {loading ? 'Generating…' : 'Generate Report'}
      </Button>
      {result && (
        <span className="text-sm text-gray-600 dark:text-gray-400">
          Report <span className="font-mono text-blue-600 dark:text-blue-400">{result.reportId}</span> ready
          {' '}(score: {result.riskScore})
        </span>
      )}
      {error && (
        <span className="text-sm text-red-600 dark:text-red-400">{error}</span>
      )}
    </div>
  )
}
