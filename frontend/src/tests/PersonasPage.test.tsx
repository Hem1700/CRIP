import { describe, it, expect } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { server } from './mocks/server'
import { PersonasPage } from '../features/personas/PersonasPage'

function wrap(ui: React.ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return (
    <MemoryRouter>
      <QueryClientProvider client={qc}>{ui}</QueryClientProvider>
    </MemoryRouter>
  )
}

describe('PersonasPage', () => {
  it('renders persona card after load', async () => {
    render(wrap(<PersonasPage />))
    await waitFor(() =>
      expect(screen.getByText('APT29 (Cozy Bear)')).toBeInTheDocument()
    )
  })

  it('shows motivation badge', async () => {
    render(wrap(<PersonasPage />))
    await waitFor(() =>
      expect(screen.getByText('Espionage')).toBeInTheDocument()
    )
  })

  it('clicking View button opens detail modal', async () => {
    render(wrap(<PersonasPage />))
    await waitFor(() => screen.getByText('APT29 (Cozy Bear)'))
    await userEvent.click(screen.getByRole('button', { name: /view/i }))
    await waitFor(() =>
      expect(screen.getByTestId('persona-detail-modal')).toBeInTheDocument()
    )
  })

  it('detail modal shows origin', async () => {
    render(wrap(<PersonasPage />))
    await waitFor(() => screen.getByText('APT29 (Cozy Bear)'))
    await userEvent.click(screen.getByRole('button', { name: /view/i }))
    await waitFor(() =>
      expect(screen.getByText('Russia')).toBeInTheDocument()
    )
  })

  it('closing modal removes it from DOM', async () => {
    render(wrap(<PersonasPage />))
    await waitFor(() => screen.getByText('APT29 (Cozy Bear)'))
    await userEvent.click(screen.getByRole('button', { name: /view/i }))
    await waitFor(() => screen.getByTestId('persona-detail-modal'))
    await userEvent.click(screen.getByRole('button', { name: /close/i }))
    expect(screen.queryByTestId('persona-detail-modal')).not.toBeInTheDocument()
  })

  it('Simulate button shows result after click', async () => {
    render(wrap(<PersonasPage />))
    await waitFor(() => screen.getByText('APT29 (Cozy Bear)'))
    await userEvent.click(screen.getByRole('button', { name: /simulate/i }))
    await waitFor(() =>
      expect(screen.getByText(/42 vulnerable assets/i)).toBeInTheDocument()
    )
  })

  it('Simulate button shows error on failure', async () => {
    server.use(
      http.post('http://localhost:8002/personas/:id/simulate', () =>
        HttpResponse.json({}, { status: 500 })
      )
    )
    render(wrap(<PersonasPage />))
    await waitFor(() => screen.getByText('APT29 (Cozy Bear)'))
    await userEvent.click(screen.getByRole('button', { name: /simulate/i }))
    await waitFor(() =>
      expect(screen.getByText(/simulation failed/i)).toBeInTheDocument()
    )
  })
})
