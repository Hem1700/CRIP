import { useQuery } from '@tanstack/react-query'
import { listPersonas } from '../../lib/personaApi'
import { PageWrapper } from '../../components/layout/PageWrapper'
import { Spinner } from '../../components/ui/Spinner'
import { ErrorBanner } from '../../components/ui/ErrorBanner'
import { PersonaGrid } from './PersonaGrid'

export function PersonasPage() {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['personas'],
    queryFn: listPersonas,
    staleTime: 60_000,
  })

  return (
    <PageWrapper>
      <h1 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">
        APT Personas
      </h1>
      {isLoading && <Spinner />}
      {isError && (
        <ErrorBanner
          message="Failed to load personas"
          onRetry={() => void refetch()}
        />
      )}
      {data && <PersonaGrid personas={data} />}
    </PageWrapper>
  )
}
