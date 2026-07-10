import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'

import { mockRetentionAlertWs } from './fixtures'

const mockToast = vi.hoisted(() =>
  Object.assign(vi.fn(), {
    success: vi.fn(),
    error: vi.fn(),
    message: vi.fn(),
  }),
)

vi.mock('sonner', () => ({
  toast: mockToast,
}))

describe('showRetentionAlertToast', () => {
  beforeEach(() => {
    mockToast.mockClear()
    vi.resetModules()
  })

  afterEach(() => {
    vi.resetModules()
  })

  it('invokes sonner toast once per alert id', async () => {
    const { resetLiveAlertToastsForTests, showRetentionAlertToast } = await import(
      '../components/alerts/LiveAlertToast'
    )
    resetLiveAlertToastsForTests()
    showRetentionAlertToast(mockRetentionAlertWs)
    showRetentionAlertToast(mockRetentionAlertWs)
    expect(mockToast).toHaveBeenCalledTimes(1)
  })
})
