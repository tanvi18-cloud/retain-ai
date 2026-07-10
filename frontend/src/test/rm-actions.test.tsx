import { beforeAll, afterAll, afterEach, describe, expect, it } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { RMActionPanel } from '../components/customers/RMActionPanel'
import { mockRecommendation } from './fixtures'
import { renderWithProviders } from './utils'
import { resetMockState, server, setInvalidTransition } from './handlers'

beforeAll(() => server.listen())
afterEach(() => {
  server.resetHandlers()
  resetMockState()
})
afterAll(() => server.close())

describe('RMActionPanel', () => {
  it('shows approve confirmation dialog', async () => {
    const user = userEvent.setup()
    renderWithProviders(
      <RMActionPanel recommendation={mockRecommendation} customerId="C001" />,
    )
    await user.click(screen.getByRole('button', { name: /Approve for discussion/i }))
    expect(
      screen.getByRole('dialog').textContent,
    ).toMatch(/It does not represent credit or product approval/i)
  })

  it('requires rejection reason', async () => {
    const user = userEvent.setup()
    renderWithProviders(
      <RMActionPanel recommendation={mockRecommendation} customerId="C001" />,
    )
    await user.click(screen.getByRole('button', { name: /^Reject$/i }))
    const dialog = screen.getByRole('dialog')
    const rejectButton = Array.from(dialog.querySelectorAll('button')).find(
      (button) => button.textContent === 'Reject',
    )
    expect(rejectButton).toBeDefined()
    expect(rejectButton).toBeDisabled()
    await user.type(screen.getByLabelText(/Rejection reason/i), 'Customer declined offer')
    expect(rejectButton).not.toBeDisabled()
  })

  it('shows contacted form fields', async () => {
    const user = userEvent.setup()
    renderWithProviders(
      <RMActionPanel
        recommendation={{ ...mockRecommendation, status: 'APPROVED' }}
        customerId="C001"
      />,
    )
    await user.click(screen.getByRole('button', { name: /Mark contacted/i }))
    expect(screen.getByLabelText(/Contact channel/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Customer response/i)).toBeInTheDocument()
  })

  it('handles invalid transition error on approve', async () => {
    setInvalidTransition()
    const user = userEvent.setup()
    renderWithProviders(
      <RMActionPanel recommendation={mockRecommendation} customerId="C001" />,
    )
    await user.click(screen.getByRole('button', { name: /Approve for discussion/i }))
    await user.click(screen.getAllByRole('button', { name: /^Approve$/i }).at(-1)!)
    await waitFor(() =>
      expect(screen.getByText(/Invalid status transition/i)).toBeInTheDocument(),
    )
  })
})
