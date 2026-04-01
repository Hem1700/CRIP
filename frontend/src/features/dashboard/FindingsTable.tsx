import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchFindings } from '../../lib/dashboardApi'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { Spinner } from '../../components/ui/Spinner'
import { ErrorBanner } from '../../components/ui/ErrorBanner'
import type { Finding } from '../../types'

const SEVERITY_OPTIONS = ['all', 'critical', 'high', 'medium', 'low'] as const
type Severity = (typeof SEVERITY_OPTIONS)[number]

const SEVERITY_COLOR: Record<string, string> = {
  critical: 'red',
  high: 'orange',
  medium: 'yellow',
  low: 'green',
}

export function FindingsTable() {
  const [severity, setSeverity] = useState<Severity>('all')
  const [page, setPage] = useState(1)

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['findings', severity, page],
    queryFn: () =>
      fetchFindings({
        severity: severity === 'all' ? undefined : severity,
        page,
        pageSize: 20,
      }),
    staleTime: 30_000,
  })

  if (isLoading) return <Spinner />
  if (isError)
    return (
      <ErrorBanner
        message="Failed to load findings"
        onRetry={() => void refetch()}
      />
    )

  const findings = data?.findings ?? []
  const pagination = data?.pagination

  return (
    <div>
      <div className="flex flex-wrap gap-2 mb-4">
        {SEVERITY_OPTIONS.map((s) => (
          <Button
            key={s}
            variant={severity === s ? 'primary' : 'secondary'}
            size="sm"
            onClick={() => {
              setSeverity(s)
              setPage(1)
            }}
            data-testid={`filter-${s}`}
          >
            {s}
          </Button>
        ))}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide border-b border-gray-200 dark:border-gray-700">
              <th className="pb-2 pr-4">Asset</th>
              <th className="pb-2 pr-4">CVE</th>
              <th className="pb-2 pr-4">CVSS</th>
              <th className="pb-2 pr-4">EPSS</th>
              <th className="pb-2 pr-4">Exploit</th>
              <th className="pb-2 pr-4">Patch</th>
              <th className="pb-2">Severity</th>
            </tr>
          </thead>
          <tbody>
            {findings.map((f: Finding) => (
              <tr
                key={`${f.assetId}-${f.cveId}`}
                className="border-b border-gray-100 dark:border-gray-800"
              >
                <td className="py-2 pr-4 font-medium text-gray-900 dark:text-white">
                  {f.assetName}
                </td>
                <td className="py-2 pr-4 font-mono text-xs text-gray-600 dark:text-gray-400">
                  {f.cveId}
                </td>
                <td className="py-2 pr-4 text-gray-700 dark:text-gray-300">{f.cvss}</td>
                <td className="py-2 pr-4 text-gray-700 dark:text-gray-300">
                  {f.epss.toFixed(2)}
                </td>
                <td className="py-2 pr-4">
                  <Badge color={f.exploitAvailable ? 'red' : 'gray'}>
                    {f.exploitAvailable ? 'YES' : 'NO'}
                  </Badge>
                </td>
                <td className="py-2 pr-4">
                  <Badge color={f.patchAvailable ? 'green' : 'gray'}>
                    {f.patchAvailable ? 'YES' : 'NO'}
                  </Badge>
                </td>
                <td className="py-2">
                  <Badge color={SEVERITY_COLOR[f.severity] ?? 'gray'}>
                    {f.severity}
                  </Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {pagination && pagination.totalPages > 1 && (
        <div className="flex items-center gap-2 mt-4">
          <Button
            variant="secondary"
            size="sm"
            disabled={page === 1}
            onClick={() => setPage((p) => p - 1)}
          >
            &lt;
          </Button>
          <span className="text-sm text-gray-600 dark:text-gray-400">
            {page} / {pagination.totalPages}
          </span>
          <Button
            variant="secondary"
            size="sm"
            disabled={page === pagination.totalPages}
            onClick={() => setPage((p) => p + 1)}
          >
            &gt;
          </Button>
        </div>
      )}
    </div>
  )
}
