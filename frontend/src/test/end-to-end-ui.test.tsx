import { beforeAll, afterAll, afterEach, describe, expect, it, vi } from 'vitest'
import { act, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { toast } from 'sonner'

import App from '../App'
import { showRetentionAlertToast } from '../components/alerts/LiveAlertToast'
import { mockChatFollowUpResponse, mockChatResponse, mockRetentionAlertWs } from './fixtures'
import { getExecutionPollCount, resetMockState, server } from './handlers'
import { renderWithProviders } from './utils'

const API = 'http://127.0.0.1:8001/api/v1'

beforeAll(() => server.listen())
afterEach(() => {
  server.resetHandlers()
  resetMockState()
  vi.clearAllMocks()
  vi.useRealTimers()
})
afterAll(() => server.close())

describe('Portfolio workflow', () => {
  it('loads dashboard KPIs and opens Customer 360 from priority table', async () => {
    const user = userEvent.setup()
    renderWithProviders(<App />, { route: '/' })

    expect(await screen.findByText('Total customers')).toBeInTheDocument()
    expect(screen.getByText('Immediate intervention')).toBeInTheDocument()
    expect(await screen.findByText('Priority customers')).toBeInTheDocument()
    expect(await screen.findByText('Asha Verma')).toBeInTheDocument()

    const viewLinks = screen.getAllByRole('link', { name: 'View' })
    await user.click(viewLinks[0])
    expect(await screen.findByText('Churn score')).toBeInTheDocument()
  })
})

describe('Customer analysis workflow', () => {
  it('runs full analysis, polls execution, and shows recommendation actions', async () => {
    const user = userEvent.setup()
    renderWithProviders(<App />, { route: '/customers/C001' })

    expect(await screen.findByText('Latest recommendation')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Run full analysis' }))

    await waitFor(() => {
      expect(getExecutionPollCount()).toBeGreaterThanOrEqual(1)
      expect(screen.getByRole('button', { name: 'Run full analysis' })).toBeEnabled()
    })

    await user.click(screen.getByRole('button', { name: /Approve for discussion/i }))
    expect(
      screen.getByRole('dialog').textContent,
    ).toMatch(/It does not represent credit or product approval/i)
  })
})

describe('Alert workflow', () => {
  it('shows toast, opens alerts page, and acknowledges alert', async () => {
    const successSpy = vi.spyOn(toast, 'success')
    const { resetLiveAlertToastsForTests } = await import('../components/alerts/LiveAlertToast')
    resetLiveAlertToastsForTests()
    showRetentionAlertToast(mockRetentionAlertWs)

    const user = userEvent.setup()
    renderWithProviders(<App />, { route: '/alerts' })
    expect((await screen.findAllByText('High churn risk — competitor transfer')).length).toBeGreaterThan(0)

    await user.click(screen.getAllByRole('button', { name: /^Acknowledge$/i })[0])
    const dialog = await screen.findByRole('dialog')
    await user.click(within(dialog).getByRole('button', { name: 'Acknowledge' }))
    await waitFor(() => expect(successSpy).toHaveBeenCalledWith('Alert acknowledged'))
    successSpy.mockRestore()
  })
})

describe('Chat workflow', () => {
  it('asks about urgency, shows evidence, and uses suggested follow-up', async () => {
    server.use(
      http.post(`${API}/chat`, async ({ request }) => {
        const body = (await request.json()) as { message?: string }
        if (body.message?.includes('What offer should I discuss')) {
          return HttpResponse.json(mockChatFollowUpResponse)
        }
        return HttpResponse.json(mockChatResponse)
      }),
    )

    const user = userEvent.setup()
    renderWithProviders(<App />, { route: '/chat' })

    const textarea = await screen.findByLabelText('Message')
    await user.type(textarea, 'Why is this customer urgent?')
    await user.click(screen.getByRole('button', { name: 'Send' }))

    expect(
      await screen.findByText('Start with C001 — high priority score and unacknowledged alerts.'),
    ).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /View 1 evidence items/i }))
    expect(await screen.findByText('priority_score')).toBeInTheDocument()

    expect(
      await screen.findByRole('button', { name: 'What offer should I discuss?' }),
    ).toBeInTheDocument()
  })
})

describe('Simulator workflow', () => {
  it('submits FD maturity event, polls to completion, and shows completed state', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    const user = userEvent.setup()
    renderWithProviders(<App />, { route: '/simulator' })

    await user.selectOptions(await screen.findByLabelText(/^Customer$/i), 'C008')
    await user.selectOptions(screen.getByLabelText(/Event type/i), 'FIXED_DEPOSIT_MATURITY')
    await user.type(screen.getByLabelText(/Maturity date/i), '2026-08-15')
    await user.click(screen.getByRole('button', { name: /Submit event/i }))
    await vi.advanceTimersByTimeAsync(100)

    expect(await screen.findByText(/Event processing completed/i)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /view customer/i })).toBeInTheDocument()
  })
})

describe('System workflow', () => {
  it('shows API, mock mode, queue, websocket, and email status', async () => {
    renderWithProviders(<App />, { route: '/system' })
    expect(await screen.findByText('MOCK mode')).toBeInTheDocument()
    expect(screen.getByText('Workers')).toBeInTheDocument()
    await waitFor(() => {
      expect(screen.getAllByText('API Connected').length).toBeGreaterThan(0)
      expect(screen.getAllByText('Live alerts connected').length).toBeGreaterThan(0)
    })
    expect(screen.getByText('1025')).toBeInTheDocument()
  })
})

describe('Performance smoke (frontend)', () => {
  it('uses bounded polling for analysis execution', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    const user = userEvent.setup()
    renderWithProviders(<App />, { route: '/customers/C001' })
    await screen.findByText('Latest recommendation')

    const pollsBefore = getExecutionPollCount()
    await user.click(screen.getByRole('button', { name: 'Run full analysis' }))
    await act(async () => {
      await vi.advanceTimersByTimeAsync(5000)
    })
    const pollsAfter = getExecutionPollCount()
    expect(pollsAfter - pollsBefore).toBeLessThan(20)
  })
})
