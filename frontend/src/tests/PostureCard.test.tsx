import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PostureCard } from '../features/dashboard/PostureCard'
import type { PostureData } from '../types'

const data: PostureData = {
  riskScore: 742,
  totalAssets: 128,
  totalVulnerabilities: 347,
  edrCoveragePct: 68.4,
  patchCoveragePct: 55.2,
  criticalAssets: 12,
}

describe('PostureCard', () => {
  it('renders risk score', () => {
    render(<PostureCard data={data} />)
    expect(screen.getByText('742')).toBeInTheDocument()
  })

  it('renders total assets', () => {
    render(<PostureCard data={data} />)
    expect(screen.getByText('128')).toBeInTheDocument()
  })

  it('renders total vulnerabilities', () => {
    render(<PostureCard data={data} />)
    expect(screen.getByText('347')).toBeInTheDocument()
  })

  it('renders EDR coverage as percentage string', () => {
    render(<PostureCard data={data} />)
    expect(screen.getByText('68.4%')).toBeInTheDocument()
  })

  it('has testid posture-card', () => {
    render(<PostureCard data={data} />)
    expect(screen.getByTestId('posture-card')).toBeInTheDocument()
  })
})
