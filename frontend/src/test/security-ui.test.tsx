import { beforeAll, afterAll, afterEach, describe, expect, it, vi } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'

import { PortfolioPage } from '../pages/PortfolioPage'
import { CustomerDetailsPage } from '../pages/CustomerDetailsPage'
import { SystemStatusPage } from '../pages/SystemStatusPage'
import { ChatPage } from '../pages/ChatPage'
import { RMActionPanel } from '../components/customers/RMActionPanel'
import { CustomerScenarioCard } from '../components/simulator/CustomerScenarioCard'
import { RecommendationPanel } from '../components/customers/RecommendationPanel'
import {
  mockCustomer360C004,
  mockCustomer360C010,
  mockRecommendation,
  mockRecommendationC010,
} from './fixtures'
import { DEFAULT_SUGGESTED_QUESTIONS } from '../components/chat/suggestedQuestionDefaults'
import { resetMockState, server } from './handlers'
import { renderWithProviders } from './utils'

const API = 'http://127.0.0.1:8001/api/v1'

const SECRET_PATTERNS = [
  /QWEN_API_KEY/i,
  /SMTP_PASSWORD/i,
  /super-secret/i,
  /Traceback \(most recent call last\)/,
  /chain-of-thought/i,
  /hidden prompt/i,
  /system instruction/i,
]

beforeAll(() => server.listen())
afterEach(() => {
  server.resetHandlers()
  resetMockState()
  vi.clearAllMocks()
  vi.useRealTimers()
})
afterAll(() => server.close())

function assertNoSecrets(text: string) {
  for (const pattern of SECRET_PATTERNS) {
    expect(text).not.toMatch(pattern)
  }
}

describe('Security UI rendering', () => {
  it('system status does not expose secrets', async () => {
    renderWithProviders(<SystemStatusPage />, { route: '/system' })
    await waitFor(() => expect(screen.getAllByText('localhost').length).toBeGreaterThan(0))
    assertNoSecrets(document.body.textContent ?? '')
    expect(screen.queryByText(/password/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/api[_-]?key/i)).not.toBeInTheDocument()
  })

  it('portfolio page shows synthetic-data badge', async () => {
    renderWithProviders(<PortfolioPage />)
    expect(await screen.findByText('Synthetic data')).toBeInTheDocument()
    assertNoSecrets(document.body.textContent ?? '')
  })

  it('customer page shows estimated revenue disclaimer context', async () => {
    renderWithProviders(<CustomerDetailsPage />, {
      route: '/customers/C001',
      withRoutes: true,
    })
    expect(await screen.findByText('Latest recommendation')).toBeInTheDocument()
    expect(screen.getByText(/Revenue at risk/i)).toBeInTheDocument()
    assertNoSecrets(document.body.textContent ?? '')
  })

  it('approval disclaimer is visible in RM action dialog', async () => {
    const user = userEvent.setup()
    renderWithProviders(
      <RMActionPanel recommendation={mockRecommendation} customerId="C001" />,
    )
    await user.click(screen.getByRole('button', { name: /Approve for discussion/i }))
    expect(
      screen.getByRole('dialog').textContent,
    ).toMatch(/It does not represent credit or product approval/i)
  })

  it('recommendation panel shows eligibility disclaimer', () => {
    renderWithProviders(<RecommendationPanel recommendation={mockRecommendation} />)
    expect(screen.getByText(mockRecommendation.eligibility_disclaimer)).toBeInTheDocument()
  })

  it('C004 lending restriction is visible in scenario card', () => {
    renderWithProviders(<CustomerScenarioCard customerId="C004" />)
    expect(screen.getByText(/lending products are policy-restricted/i)).toBeInTheDocument()
    expect(screen.getAllByText(/repayment support/i).length).toBeGreaterThan(0)
  })

  it('C010 no-action state shows no offer in recommendation panel', () => {
    renderWithProviders(<RecommendationPanel recommendation={mockRecommendationC010} />)
    expect(screen.getByText('No action')).toBeInTheDocument()
    expect(screen.getAllByText('—').length).toBeGreaterThan(0)
    expect(screen.queryByText(/OFFER-HL/i)).not.toBeInTheDocument()
  })

  it('chat UI does not render raw secrets or SQL', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ChatPage />, { route: '/chat' })
    await user.click(await screen.findByRole('button', { name: DEFAULT_SUGGESTED_QUESTIONS[0] }))
    const answer = await screen.findByText(
      'Start with C001 — high priority score and unacknowledged alerts.',
    )
    assertNoSecrets(answer.textContent ?? '')
    expect(document.body.textContent).not.toMatch(/DROP TABLE/i)
  })

  it('customer 360 mock responses omit full account numbers in UI', async () => {
    server.use(
      http.get(`${API}/customers/C004/360`, () => HttpResponse.json(mockCustomer360C004)),
      http.get(`${API}/customers/C010/360`, () => HttpResponse.json(mockCustomer360C010)),
    )
    renderWithProviders(<CustomerDetailsPage />, {
      route: '/customers/C004',
      withRoutes: true,
    })
    expect(await screen.findByText('Credit profile')).toBeInTheDocument()
    assertNoSecrets(document.body.textContent ?? '')
    expect(document.body.textContent).not.toMatch(/\d{12,}/)
  })
})

describe('Security UI guardrails with MSW payloads', () => {
  it('does not render raw transaction JSON in customer view', async () => {
    renderWithProviders(<CustomerDetailsPage />, {
      route: '/customers/C001',
      withRoutes: true,
    })
    await screen.findByText('Transaction behavior')
    expect(document.body.textContent).not.toMatch(/raw transaction json/i)
    expect(document.body.textContent).not.toMatch(/"monthly_inflow":/i)
  })
})
