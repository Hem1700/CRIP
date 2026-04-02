import ReactMarkdown from 'react-markdown'
import { Badge } from '../../components/ui/Badge'
import type { ChatMessage } from '../../types'

interface Props {
  message: ChatMessage
}

export function MessageBubble({ message }: Props) {
  if (message.role === 'user') {
    return (
      <div className="flex justify-end">
        <div className="max-w-lg rounded-lg bg-blue-600 text-white px-4 py-2 text-sm">
          {message.content}
        </div>
      </div>
    )
  }

  return (
    <div className="flex justify-start">
      <div className="max-w-2xl rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 px-4 py-3">
        <div className="prose prose-sm dark:prose-invert max-w-none text-gray-900 dark:text-gray-100">
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>
        {(message.confidence != null || (message.citations?.length ?? 0) > 0) && (
          <div className="flex flex-wrap items-center gap-2 mt-2 pt-2 border-t border-gray-100 dark:border-gray-800">
            {message.confidence != null && (
              <span className="text-xs text-gray-500 dark:text-gray-400">
                confidence: {message.confidence.toFixed(2)}
              </span>
            )}
            {message.citations?.map((c) => (
              <Badge key={c} color="blue">{c}</Badge>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
