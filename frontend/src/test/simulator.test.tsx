import { beforeAll, afterAll, afterEach, describe, expect, it, vi } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { SimulatorPage } from '../pages/SimulatorPage'
import { resetMockState, server, setFailedEvent } from './handlers'
import { renderWithProviders } from './utils'

beforeAll(() => server.listen())
afterEach(() => {
  server.resetHandlers()
  resetMockState()
  vi.useRealTimers()
})
afterAll(() => server.close())

describe('Event simulator', () => {
  it('renders synthetic notice and event form', async () => {
    renderWithProviders(<SimulatorPage />, { route: '/simulator' })
    expect((await screen.findAllByText(/Synthetic demonstration tool/i)).length).toBeGreaterThan(0)
    expect(screen.getByLabelText(/Event type/i)).toBeInTheDocument()
  })

  it('shows scenario card for C001', async () => {
    renderWithProviders(<SimulatorPage />, { route: '/simulator' })
    expect(await screen.findByText(/external home-loan shopping/i)).toBeInTheDocument()
  })

  it('renders dynamic fields for selected event type', async () => {
    const user = userEvent.setup()
    renderWithProviders(<SimulatorPage />, { route: '/simulator' })

    const eventType = await screen.findByLabelText(/event type/i)
    await user.selectOptions(eventType, 'LARGE_EXTERNAL_TRANSFER')
    expect(screen.getByLabelText(/amount/i)).toBeInTheDocument()
  })

  it('submits event and polls to completion', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    const user = userEvent.setup()
    renderWithProviders(<SimulatorPage />, { route: '/simulator' })

    await user.click(await screen.findByRole('button', { name: /submit event/i }))

    await waitFor(() => expect(screen.getByText(/Event queued for processing/i)).toBeInTheDocument())

    await vi.advanceTimersByTimeAsync(50)

    expect(await screen.findByText(/Event processing completed/i)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /view customer/i })).toHaveAttribute('href', '/customers/C001')
  })

  it('shows failed event and offers retry', async () => {
    setFailedEvent()
    vi.useFakeTimers({ shouldAdvanceTime: true })
    const user = userEvent.setup()
    renderWithProviders(<SimulatorPage />, { route: '/simulator' })

    await user.click(await screen.findByRole('button', { name: /Submit event/i }))
    await vi.advanceTimersByTimeAsync(100)

    expect(screen.getAllByText('Failed').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Event processing failed safely.').length).toBeGreaterThan(0)
    expect(screen.getByRole('button', { name: /Retry event/i })).toBeInTheDocument()
  })

  it('validates required fields client-side', async () => {
    const user = userEvent.setup()
    renderWithProviders(<SimulatorPage />, { route: '/simulator' })

    const eventType = await screen.findByLabelText(/Event type/i)
    await user.selectOptions(eventType, 'INVESTMENT_TRANSFER_INCREASE')
    await user.click(screen.getByRole('button', { name: /Submit event/i }))

    expect(await screen.findByText('Transfer amount is required.')).toBeInTheDocument()
  })
})
