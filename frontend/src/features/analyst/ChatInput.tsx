import { useState, type KeyboardEvent } from 'react'
import { Button } from '../../components/ui/Button'

interface Props {
  onSend: (question: string) => void
  disabled?: boolean
}

export function ChatInput({ onSend, disabled }: Props) {
  const [value, setValue] = useState('')

  function submit() {
    const trimmed = value.trim()
    if (!trimmed) return
    onSend(trimmed)
    setValue('')
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  return (
    <div className="flex gap-3 p-4 border-t border-gray-200 dark:border-gray-800">
      <textarea
        className="flex-1 resize-none rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        rows={2}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask about your environment… (Enter to send, Shift+Enter for newline)"
        disabled={disabled}
      />
      <Button onClick={submit} disabled={disabled || !value.trim()} size="lg">
        Send
      </Button>
    </div>
  )
}
