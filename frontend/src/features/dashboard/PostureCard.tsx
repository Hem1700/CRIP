import { Card } from '../../components/ui/Card'
import type { PostureData } from '../../types'

interface Props {
  data: PostureData
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <Card>
      <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">
        {label}
      </p>
      <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">{value}</p>
    </Card>
  )
}

export function PostureCard({ data }: Props) {
  return (
    <div
      data-testid="posture-card"
      className="grid grid-cols-2 gap-4 sm:grid-cols-4"
    >
      <StatCard label="Risk Score" value={data.riskScore} />
      <StatCard label="Assets" value={data.totalAssets} />
      <StatCard label="Vulnerabilities" value={data.totalVulnerabilities} />
      <StatCard label="EDR Coverage" value={`${data.edrCoveragePct}%`} />
    </div>
  )
}
