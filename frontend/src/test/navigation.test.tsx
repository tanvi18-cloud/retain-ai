import { beforeAll, afterAll, afterEach, describe, expect, it } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import App from '../App'
import { RouteSkeleton } from '../components/layout/RouteSkeleton'
import { resetMockState, server } from './handlers'
import { renderWithProviders } from './utils'

beforeAll(() => server.listen())
afterEach(() => {
  server.resetHandlers()
  resetMockState()
})
afterAll(() => server.close())

describe('Navigation', () => {
  it('navigates to all primary routes', async () => {
    const user = userEvent.setup()
    renderWithProviders(<App />, { route: '/' })

    const alertsLinks = screen.getAllByRole('link', { name: /^Alerts$/i })
    await user.click(alertsLinks[0])
    expect(await screen.findByRole('heading', { level: 2, name: 'Retention Alerts' })).toBeInTheDocument()

    await user.click(screen.getAllByRole('link', { name: /RM Copilot/i })[0])
    expect(await screen.findByRole('heading', { level: 2, name: 'RM Copilot' })).toBeInTheDocument()

    await user.click(screen.getAllByRole('link', { name: /Event Simulator/i })[0])
    expect(await screen.findByRole('heading', { level: 2, name: 'Event Simulator' })).toBeInTheDocument()

    await user.click(screen.getAllByRole('link', { name: /System Status/i })[0])
    expect(await screen.findByRole('heading', { level: 2, name: 'System Status' })).toBeInTheDocument()
  })

  it('redirects /copilot to /chat', async () => {
    renderWithProviders(<App />, { route: '/copilot' })
    expect(await screen.findByRole('heading', { level: 2, name: 'RM Copilot' })).toBeInTheDocument()
  })

  it('marks active route in sidebar', async () => {
    renderWithProviders(<App />, { route: '/alerts' })
    const alertsLink = (await screen.findAllByRole('link', { name: /^Alerts$/i })).find(
      (link) => link.getAttribute('aria-current') === 'page',
    )
    expect(alertsLink).toBeTruthy()
  })

  it('shows mobile quick navigation', async () => {
    renderWithProviders(<App />, { route: '/' })
    expect(screen.getByRole('navigation', { name: 'Mobile quick navigation' })).toBeInTheDocument()
  })
})

describe('Route code splitting', () => {
  it('renders route skeleton fallback', () => {
    renderWithProviders(<RouteSkeleton />)
    expect(screen.getByLabelText('Loading page')).toBeInTheDocument()
  })

  it('lazy-loads alerts page content', async () => {
    renderWithProviders(<App />, { route: '/alerts' })
    await waitFor(() =>
      expect(screen.getByRole('heading', { level: 2, name: 'Retention Alerts' })).toBeInTheDocument(),
    )
  })
})
