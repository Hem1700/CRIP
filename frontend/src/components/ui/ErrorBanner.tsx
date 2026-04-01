import { Button } from './Button'

interface Props {
  message: string
  onRetry?: () => void
}

export function ErrorBanner({ message, onRetry }: Props) {
  return (
    <div
      role="alert"
      className="flex items-center gap-3 rounded-lg border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20 p-3 text-sm text-red-800 dark:text-red-400"
    >
      <span className="flex-1">{message}</span>
      {onRetry && (
        <Button variant="secondary" size="sm" onClick={onRetry}>
          Retry
        </Button>
      )}
    </div>
  )
}
