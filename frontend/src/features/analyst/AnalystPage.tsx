import { useEffect, useRef, useState, useCallback } from 'react'
import { v4 as uuidv4 } from 'uuid'
import { PageWrapper } from '../../components/layout/PageWrapper'
import { ChatWindow } from './ChatWindow'
import { ChatInput } from './ChatInput'
import { AnalystWsClient } from '../../lib/wsClient'
import { querySync } from '../../lib/reasoningApi'
import type { ChatMessage } from '../../types'

export function AnalystPage() {
  const sessionId = useRef(uuidv4())
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [sending, setSending] = useState(false)
  const wsRef = useRef<AnalystWsClient | null>(null)

  // Append a token to the last (streaming) assistant message
  const appendToken = useCallback((token: string) => {
    setMessages((prev) => {
      const last = prev[prev.length - 1]
      if (!last || last.role !== 'assistant') return prev
      return [
        ...prev.slice(0, -1),
        { ...last, content: last.content + token },
      ]
    })
  }, [])

  // Finalize the streaming assistant message with confidence + citations
  const finalizeStream = useCallback((confidence: number, citations: string[]) => {
    setMessages((prev) => {
      const last = prev[prev.length - 1]
      if (!last || last.role !== 'assistant') return prev
      return [...prev.slice(0, -1), { ...last, confidence, citations }]
    })
    setSending(false)
  }, [])

  // On WS error/close, fall back to REST
  const handleWsError = useCallback(() => {
    wsRef.current = null
  }, [])

  useEffect(() => {
    const client = new AnalystWsClient(appendToken, finalizeStream, handleWsError)
    client.connect(sessionId.current)
    wsRef.current = client
    return () => client.close()
  }, [appendToken, finalizeStream, handleWsError])

  async function send(question: string) {
    setSending(true)

    // Optimistically add user message
    const userMsg: ChatMessage = { id: uuidv4(), role: 'user', content: question }
    setMessages((prev) => [...prev, userMsg])

    if (wsRef.current?.isOpen()) {
      // WS path: add empty assistant bubble to stream into
      const assistantMsg: ChatMessage = { id: uuidv4(), role: 'assistant', content: '' }
      setMessages((prev) => [...prev, assistantMsg])
      wsRef.current.send(question, sessionId.current)
      // setSending(false) called in finalizeStream
    } else {
      // REST fallback
      try {
        const result = await querySync({ question, sessionId: sessionId.current })
        const assistantMsg: ChatMessage = {
          id: uuidv4(),
          role: 'assistant',
          content: result.answer,
          confidence: result.confidence,
          citations: result.citations,
        }
        setMessages((prev) => [...prev, assistantMsg])
      } catch {
        const errorMsg: ChatMessage = {
          id: uuidv4(),
          role: 'assistant',
          content: 'Sorry, I could not reach the reasoning service. Please try again.',
        }
        setMessages((prev) => [...prev, errorMsg])
      } finally {
        setSending(false)
      }
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-3.5rem)]">
      <PageWrapper>
        <h1 className="text-lg font-semibold text-gray-900 dark:text-white mb-0">
          Analyst
        </h1>
      </PageWrapper>
      <div className="flex flex-col flex-1 overflow-hidden max-w-7xl mx-auto w-full px-4 sm:px-6">
        <ChatWindow messages={messages} />
        <ChatInput onSend={(q) => void send(q)} disabled={sending} />
      </div>
    </div>
  )
}
