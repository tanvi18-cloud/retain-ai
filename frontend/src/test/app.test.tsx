import { beforeAll, afterAll, afterEach, describe, expect, it } from 'vitest'
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import App from '../App'
import { renderWithProviders } from './utils'
import { resetMockState, server } from './handlers'

beforeAll(() => server.listen())
afterEach(() => {
  server.resetHandlers()
  resetMockState()
})
afterAll(() => server.close())

describe('Application shell', () => {
  it('renders shell and portfolio navigation', async () => {
    renderWithProviders(<App />, { route: '/' })
    expect(await screen.findByRole('heading', { level: 2, name: 'Customer Retention Command Center' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Customers/i })).toBeInTheDocument()
  })

  it('navigates to customers page', async () => {
    const user = userEvent.setup()
    renderWithProviders(<App />, { route: '/' })
    await user.click(screen.getByRole('link', { name: /Customers/i }))
    expect(await screen.findByRole('heading', { level: 2, name: 'Customer Directory' })).toBeInTheDocument()
  })

  it('shows 404 page', async () => {
    renderWithProviders(<App />, { route: '/404' })
    expect(screen.getByText('Page not found')).toBeInTheDocument()
  })
})
