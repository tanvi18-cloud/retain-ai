import { beforeAll, afterAll, afterEach, describe, expect, it, vi } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { CustomerDetailsPage } from '../pages/CustomerDetailsPage'
import { renderWithProviders } from './utils'
import { getExecutionPollCount, resetMockState, server, setFailedExecution } from './handlers'

beforeAll(() => server.listen())
afterEach(() => {
  server.resetHandlers()
  resetMockState()
  vi.restoreAllMocks()
})
afterAll(() => server.close())

function renderCustomerDetails() {
  return renderWithProviders(<CustomerDetailsPage />, {
    route: '/customers/C001',
    withRoutes: true,
  })
}

describe('CustomerDetailsPage', () => {
  it('renders profile and risk scores', async () => {
    renderCustomerDetails()
    expect(await screen.findByText('Asha Verma')).toBeInTheDocument()
    expect(screen.getByText('Churn score')).toBeInTheDocument()
    expect(screen.getByText('82')).toBeInTheDocument()
  })

  it('renders evidence and credit profile', async () => {
    renderCustomerDetails()
    expect(await screen.findByText('Evidence timeline')).toBeInTheDocument()
    expect(screen.getByText('Credit profile')).toBeInTheDocument()
    expect(screen.getByText('720')).toBeInTheDocument()
  })

  it('renders transaction behavior and freshness warnings', async () => {
    renderCustomerDetails()
    expect(await screen.findByText('Transaction behavior')).toBeInTheDocument()
    expect(screen.getByText(/Credit history is older than 7 days/i)).toBeInTheDocument()
  })

  it('shows recommendation state', async () => {
    renderCustomerDetails()
    expect(await screen.findByText('Latest recommendation')).toBeInTheDocument()
    expect(await screen.findByText(/competitor transfer signals/i)).toBeInTheDocument()
  })

  it('runs rules-only analysis', async () => {
    const user = userEvent.setup()
    renderCustomerDetails()
    await user.click(await screen.findByRole('button', { name: /rules-only analysis/i }))
    expect(await screen.findByText('Rules-only analysis result')).toBeInTheDocument()
  })

  it('polls full analysis to completion', async () => {
    const user = userEvent.setup()
    renderCustomerDetails()

    await screen.findByText('Latest recommendation')

    const runButton = screen.getByRole('button', { name: 'Run full analysis' })
    await user.click(runButton)

    await waitFor(() => {
      expect(screen.getByText(/Full analysis completed/i)).toBeInTheDocument()
    })

    expect(getExecutionPollCount()).toBeGreaterThanOrEqual(1)
    expect(screen.getByRole('button', { name: 'Run full analysis' })).toBeEnabled()
    expect(screen.queryByText(/QUEUED…/i)).not.toBeInTheDocument()
  })

  it('shows failed execution safely', async () => {
    setFailedExecution()
    const user = userEvent.setup()
    renderCustomerDetails()

    await screen.findByText('Latest recommendation')

    await user.click(screen.getByRole('button', { name: 'Run full analysis' }))

    await waitFor(() => {
      expect(
        screen.getByText(/Analysis could not be completed safely/i),
      ).toBeInTheDocument()
    })

    expect(screen.queryByText(/stack trace/i)).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Run full analysis' })).toBeEnabled()
  })
})
