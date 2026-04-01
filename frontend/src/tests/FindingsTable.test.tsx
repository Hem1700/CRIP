import { describe, it, expect } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { server } from './mocks/server'
import { FindingsTable } from '../features/dashboard/FindingsTable'

function wrap(ui: React.ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={qc}>{ui}</QueryClientProvider>
}

describe('FindingsTable', () => {
  it('renders a finding row after load', async () => {
    render(wrap(<FindingsTable />))
    await waitFor(() => {
      expect(screen.getByText('web-server-1')).toBeInTheDocument()
    })
    expect(screen.getByText('CVE-2024-1234')).toBeInTheDocument()
    expect(screen.getByText('9.8')).toBeInTheDocument()
  })

  it('shows severity badge', async () => {
    render(wrap(<FindingsTable />))
    await waitFor(() => {
      const badges = screen.getAllByText('critical')
      // There's a button with 'critical' and a badge with 'critical'
      expect(badges.length).toBeGreaterThanOrEqual(2)
    })
  })

  it('shows exploit badge YES', async () => {
    render(wrap(<FindingsTable />))
    await waitFor(() => {
      const badges = screen.getAllByText('YES')
      expect(badges.length).toBeGreaterThan(0)
    })
  })

  it('clicking critical filter re-fetches with severity param', async () => {
    let capturedUrl = ''
    server.use(
      http.get('http://localhost:8003/dashboard/findings', ({ request }) => {
        capturedUrl = request.url
        return HttpResponse.json({
          findings: [],
          pagination: { page: 1, pageSize: 20, total: 0, totalPages: 0 },
        })
      })
    )
    render(wrap(<FindingsTable />))
    // Wait for initial load to complete
    await waitFor(() => {
      expect(screen.getByTestId('filter-critical')).toBeInTheDocument()
    })
    await userEvent.click(screen.getByTestId('filter-critical'))
    await waitFor(() => expect(capturedUrl).toContain('severity=critical'))
  })

  it('shows error banner on fetch failure', async () => {
    server.use(
      http.get('http://localhost:8003/dashboard/findings', () =>
        HttpResponse.json({}, { status: 500 })
      )
    )
    render(wrap(<FindingsTable />))
    await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument())
  })
})
