import { useQuery } from '@tanstack/react-query'
import { getPersona } from '../../lib/personaApi'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { Spinner } from '../../components/ui/Spinner'
import { ErrorBanner } from '../../components/ui/ErrorBanner'

interface Props {
  groupId: string
  onClose: () => void
}

export function PersonaDetail({ groupId, onClose }: Props) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['persona', groupId],
    queryFn: () => getPersona(groupId),
  })

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={onClose}
    >
      <div
        data-testid="persona-detail-modal"
        className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 shadow-xl max-w-lg w-full mx-4 p-6 max-h-[80vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-start mb-4">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            {data?.current.name ?? 'Loading…'}
          </h2>
          <Button variant="ghost" size="sm" onClick={onClose} aria-label="Close">
            ✕
          </Button>
        </div>

        {isLoading && <Spinner />}
        {isError && <ErrorBanner message="Failed to load persona details" />}

        {data && (
          <div className="space-y-4 text-sm">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wide">Origin</p>
                <p className="text-gray-900 dark:text-white mt-1">{data.current.origin}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wide">Sophistication</p>
                <p className="text-gray-900 dark:text-white mt-1">{data.current.sophistication}</p>
              </div>
            </div>

            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Target Sectors</p>
              <div className="flex flex-wrap gap-1">
                {data.current.primarySectors.map((s) => (
                  <Badge key={s} color="blue">{s}</Badge>
                ))}
              </div>
            </div>

            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wide mb-2">Signature TTPs</p>
              <ul className="space-y-1">
                {data.current.signatureTTPs.map((t) => (
                  <li key={t.techniqueId} className="flex items-center gap-2">
                    <Badge color="gray">{t.techniqueId}</Badge>
                    <span className="text-gray-700 dark:text-gray-300">{t.name}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">
                Version History ({data.versions.length})
              </p>
              <p className="text-gray-600 dark:text-gray-400">
                Current: v{data.current.version}
                {data.current.updatedAt && ` · Updated ${new Date(data.current.updatedAt).toLocaleDateString()}`}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
