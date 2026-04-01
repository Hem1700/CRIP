import { useQuery } from '@tanstack/react-query'
import { fetchPosture } from '../../lib/dashboardApi'
import { PageWrapper } from '../../components/layout/PageWrapper'
import { Spinner } from '../../components/ui/Spinner'
import { ErrorBanner } from '../../components/ui/ErrorBanner'
import { PostureCard } from './PostureCard'
import { ThreatHeatmap } from './ThreatHeatmap'
import { FindingsTable } from './FindingsTable'
import { GenerateReportButton } from './GenerateReportButton'

export function DashboardPage() {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['posture'],
    queryFn: fetchPosture,
    staleTime: 30_000,
  })

  return (
    <PageWrapper>
      <div className="space-y-8">
        {isLoading && <Spinner />}
        {isError && (
          <ErrorBanner
            message="Failed to load security posture"
            onRetry={() => void refetch()}
          />
        )}
        {data && <PostureCard data={data} />}

        <ThreatHeatmap />

        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide">
              Findings
            </h2>
            <GenerateReportButton />
          </div>
          <FindingsTable />
        </div>
      </div>
    </PageWrapper>
  )
}
