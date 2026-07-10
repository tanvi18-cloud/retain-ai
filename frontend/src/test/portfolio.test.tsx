import { beforeAll, afterAll, afterEach, describe, expect, it } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { PortfolioPage } from '../pages/PortfolioPage'
import { renderWithProviders } from './utils'
import { resetMockState, server, setPortfolioError } from './handlers'

beforeAll(() => server.listen())
afterEach(() => {
  server.resetHandlers()
  resetMockState()
})
afterAll(() => server.close())

describe('PortfolioPage', () => {
  it('renders KPI cards', async () => {
    renderWithProviders(<PortfolioPage />)
    expect(await screen.findByText('Total customers')).toBeInTheDocument()
    expect(await screen.findByText('Immediate intervention')).toBeInTheDocument()
    expect((await screen.findAllByText('2')).length).toBeGreaterThan(0)
  })

  it('renders customer rows', async () => {
    renderWithProviders(<PortfolioPage />)
    expect(await screen.findByText('Asha Verma')).toBeInTheDocument()
    expect(screen.getByText('Rahul Mehta')).toBeInTheDocument()
  })

  it('filters by search', async () => {
    const user = userEvent.setup()
    renderWithProviders(<PortfolioPage />)
    await screen.findByText('Asha Verma')
    await user.type(screen.getByLabelText('Search'), 'C001')
    await waitFor(() => {
      expect(screen.getByText('Asha Verma')).toBeInTheDocument()
      expect(screen.queryByText('Rahul Mehta')).not.toBeInTheDocument()
    })
  })

  it('shows loading then data', async () => {
    renderWithProviders(<PortfolioPage />)
    await waitFor(() => expect(screen.getByText('Priority customers')).toBeInTheDocument())
  })

  it('shows API error state', async () => {
    setPortfolioError()
    renderWithProviders(<PortfolioPage />)
    expect(await screen.findByText(/Unable to load portfolio summary/i)).toBeInTheDocument()
  })

  it('shows chart fallback summary text', async () => {
    renderWithProviders(<PortfolioPage />)
    expect(await screen.findByText(/Quadrant summary/i)).toBeInTheDocument()
    expect(screen.getByText(/Action distribution/i)).toBeInTheDocument()
  })
})
