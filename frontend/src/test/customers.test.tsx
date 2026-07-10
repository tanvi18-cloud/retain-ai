import { beforeAll, afterAll, afterEach, describe, expect, it } from 'vitest'
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { CustomersPage } from '../pages/CustomersPage'
import { renderWithProviders } from './utils'
import { resetMockState, server } from './handlers'

beforeAll(() => server.listen())
afterEach(() => {
  server.resetHandlers()
  resetMockState()
})
afterAll(() => server.close())

describe('CustomersPage', () => {
  it('renders customer list', async () => {
    renderWithProviders(<CustomersPage />)
    expect(await screen.findByText('Asha Verma')).toBeInTheDocument()
    expect(screen.getByText('C001')).toBeInTheDocument()
  })

  it('supports search', async () => {
    const user = userEvent.setup()
    renderWithProviders(<CustomersPage />)
    await screen.findByText('Asha Verma')
    await user.type(screen.getByLabelText('Search'), 'Asha')
    expect(screen.getByText('Asha Verma')).toBeInTheDocument()
  })

  it('links to customer 360', async () => {
    renderWithProviders(<CustomersPage />)
    const link = await screen.findByRole('link', { name: /Customer 360/i })
    expect(link).toHaveAttribute('href', '/customers/C001')
  })
})
