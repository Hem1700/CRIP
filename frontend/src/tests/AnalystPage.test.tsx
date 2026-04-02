import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AnalystPage } from '../features/analyst/AnalystPage'

// The WS client opens a real WebSocket which can't connect in tests.
// Mock it so isOpen() always returns false → fallback to REST.
vi.mock('../lib/wsClient', () => ({
  AnalystWsClient: vi.fn().mockImplementation(() => ({
    connect: vi.fn(),
    send: vi.fn(),
    isOpen: vi.fn().mockReturnValue(false),
    close: vi.fn(),
  })),
}))

function wrap(ui: React.ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return (
    <MemoryRouter>
      <QueryClientProvider client={qc}>{ui}</QueryClientProvider>
    </MemoryRouter>
  )
}

describe('AnalystPage', () => {
  beforeEach(() => vi.clearAllMocks())

  it('renders chat input', () => {
    render(wrap(<AnalystPage />))
    expect(screen.getByPlaceholderText(/ask about your environment/i)).toBeInTheDocument()
  })

  it('renders send button', () => {
    render(wrap(<AnalystPage />))
    expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument()
  })

  it('appends user message immediately on send', async () => {
    render(wrap(<AnalystPage />))
    await userEvent.type(screen.getByPlaceholderText(/ask about your environment/i), 'What are my risks?')
    await userEvent.click(screen.getByRole('button', { name: /send/i }))
    expect(screen.getByText('What are my risks?')).toBeInTheDocument()
  })

  it('shows assistant response from REST fallback', async () => {
    render(wrap(<AnalystPage />))
    await userEvent.type(screen.getByPlaceholderText(/ask about your environment/i), 'What are my risks?')
    await userEvent.click(screen.getByRole('button', { name: /send/i }))
    await waitFor(() =>
      expect(screen.getByText(/web-server-1/i)).toBeInTheDocument()
    )
  })

  it('shows confidence score after response', async () => {
    render(wrap(<AnalystPage />))
    await userEvent.type(screen.getByPlaceholderText(/ask about your environment/i), 'test')
    await userEvent.click(screen.getByRole('button', { name: /send/i }))
    await waitFor(() =>
      expect(screen.getByText(/0\.91/)).toBeInTheDocument()
    )
  })

  it('clears input after send', async () => {
    render(wrap(<AnalystPage />))
    const input = screen.getByPlaceholderText(/ask about your environment/i)
    await userEvent.type(input, 'hello')
    await userEvent.click(screen.getByRole('button', { name: /send/i }))
    expect(input).toHaveValue('')
  })
})
