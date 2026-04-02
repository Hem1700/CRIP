import { describe, it, expect } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { server } from './mocks/server'
import { GenerateReportButton } from '../features/dashboard/GenerateReportButton'

function wrap(ui: React.ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={qc}>{ui}</QueryClientProvider>
}

describe('GenerateReportButton', () => {
  it('renders the button', () => {
    render(wrap(<GenerateReportButton />))
    expect(screen.getByRole('button', { name: /generate report/i })).toBeInTheDocument()
  })

  it('shows report ID on success', async () => {
    render(wrap(<GenerateReportButton />))
    await userEvent.click(screen.getByRole('button', { name: /generate report/i }))
    await waitFor(() =>
      expect(screen.getByText(/r-abc123/)).toBeInTheDocument()
    )
  })

  it('shows error message on failure', async () => {
    server.use(
      http.post('http://localhost:8003/reports/generate', () =>
        HttpResponse.json({}, { status: 500 })
      )
    )
    render(wrap(<GenerateReportButton />))
    await userEvent.click(screen.getByRole('button', { name: /generate report/i }))
    await waitFor(() =>
      expect(screen.getByText(/failed/i)).toBeInTheDocument()
    )
  })
})
