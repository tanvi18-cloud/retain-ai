import { beforeAll, afterAll, afterEach, describe, expect, it, vi } from 'vitest'
import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { toast } from 'sonner'

import { AlertsPage } from '../pages/AlertsPage'
import { resetMockState, server, setAlertsError } from './handlers'
import { renderWithProviders } from './utils'

vi.mock('sonner', async (importOriginal) => {
  const actual = await importOriginal<typeof import('sonner')>()
  return {
    ...actual,
    toast: Object.assign(vi.fn(), {
      success: vi.fn(),
      error: vi.fn(),
      message: vi.fn(),
    }),
  }
})


beforeAll(() => server.listen())
afterEach(() => {
  server.resetHandlers()
  resetMockState()
  vi.clearAllMocks()
})
afterAll(() => server.close())

describe('Alerts page', () => {
  it('renders alert list', async () => {
    renderWithProviders(<AlertsPage />, { route: '/alerts' })
    expect((await screen.findAllByText('High churn risk — competitor transfer')).length).toBeGreaterThan(0)
    expect(screen.getAllByText('DPD escalation — repayment support needed').length).toBeGreaterThan(0)
  })

  it('filters unacknowledged tab', async () => {
    const user = userEvent.setup()
    renderWithProviders(<AlertsPage />, { route: '/alerts' })
    await screen.findAllByText('High churn risk — competitor transfer')

    await user.click(screen.getByRole('tab', { name: 'Unacknowledged' }))
    expect(screen.getAllByText('High churn risk — competitor transfer').length).toBeGreaterThan(0)
    expect(screen.queryByText('DPD escalation — repayment support needed')).not.toBeInTheDocument()
  })

  it('acknowledges alert and refreshes list', async () => {
    const user = userEvent.setup()
    renderWithProviders(<AlertsPage />, { route: '/alerts' })
    await screen.findAllByText('High churn risk — competitor transfer')

    await user.click(screen.getAllByRole('button', { name: /^Acknowledge$/i })[0])
    const dialog = await screen.findByRole('dialog')
    await user.click(within(dialog).getByRole('button', { name: 'Acknowledge' }))

    await waitFor(() => expect(vi.mocked(toast.success)).toHaveBeenCalledWith('Alert acknowledged'))
  })

  it('shows empty state when filtered results are empty', async () => {
    renderWithProviders(<AlertsPage />, { route: '/alerts?customer_id=MISSING' })
    expect(
      (await screen.findAllByRole('heading', { name: 'No alerts found' })).length,
    ).toBeGreaterThan(0)
  })

  it('shows error state', async () => {
    setAlertsError()
    renderWithProviders(<AlertsPage />, { route: '/alerts' })
    expect(await screen.findByText('Unable to load alerts.')).toBeInTheDocument()
  })
})
