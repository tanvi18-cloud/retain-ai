import { beforeAll, afterAll, afterEach, describe, expect, it } from 'vitest'
import { screen, waitFor } from '@testing-library/react'

import { SystemStatusPage } from '../pages/SystemStatusPage'
import { mockLLMStatusUnavailable } from './fixtures'
import { http, HttpResponse } from 'msw'
import { resetMockState, server } from './handlers'
import { renderWithProviders } from './utils'

const API = 'http://127.0.0.1:8001/api/v1'

beforeAll(() => server.listen())
afterEach(() => {
  server.resetHandlers()
  resetMockState()
})
afterAll(() => server.close())

describe('System status page', () => {
  it('renders health and queue metrics', async () => {
    renderWithProviders(<SystemStatusPage />, { route: '/system' })
    expect(await screen.findByText('MOCK mode')).toBeInTheDocument()
    expect(screen.getByText('Workers')).toBeInTheDocument()
    expect(screen.getByText('Completed (startup)')).toBeInTheDocument()
    expect(screen.getAllByText('localhost').length).toBeGreaterThan(0)
  })

  it('shows connection status labels', async () => {
    renderWithProviders(<SystemStatusPage />, { route: '/system' })
    await waitFor(() => {
      expect(screen.getAllByText('API Connected').length).toBeGreaterThan(0)
      expect(screen.getAllByText('Live alerts connected').length).toBeGreaterThan(0)
    })
  })

  it('shows notification configuration without secrets', async () => {
    renderWithProviders(<SystemStatusPage />, { route: '/system' })
    await waitFor(() => expect(screen.getAllByText('localhost').length).toBeGreaterThan(0))
    expect(screen.getByText('1025')).toBeInTheDocument()
    expect(screen.queryByText(/password/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/api[_-]?key/i)).not.toBeInTheDocument()
  })

  it('shows unavailable Qwen status', async () => {
    server.use(
      http.get(`${API}/system/llm-status`, () =>
        HttpResponse.json(mockLLMStatusUnavailable),
      ),
    )
    renderWithProviders(<SystemStatusPage />, { route: '/system' })
    expect(await screen.findByText('QWEN unavailable')).toBeInTheDocument()
    expect(screen.getByText('Qwen endpoint unreachable')).toBeInTheDocument()
  })
})
