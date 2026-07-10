import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { act, renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'

import {
  AlertsWebSocketProvider,
  useAlertsWebSocket,
} from '../hooks/useAlertsWebSocket'
import { mockRetentionAlertWs } from './fixtures'
import { MockWebSocket } from './setup'

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return (
    <QueryClientProvider client={client}>
      <AlertsWebSocketProvider>{children}</AlertsWebSocketProvider>
    </QueryClientProvider>
  )
}

describe('useAlertsWebSocket', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('handles CONNECTED and PING/PONG', async () => {
    const { result } = renderHook(() => useAlertsWebSocket(), { wrapper })

    await waitFor(() => expect(result.current.state).toBe('CONNECTED'))

    const socket = MockWebSocket.latest()
    expect(socket?.sent.some((msg) => msg.includes('PING'))).toBe(false)

    await act(async () => {
      socket?.send(JSON.stringify({ type: 'PING' }))
    })

    await waitFor(() => expect(result.current.diagnostics.lastPongAt).not.toBeNull())
  })

  it('handles retention alert and ignores duplicates', async () => {
    const { result } = renderHook(() => useAlertsWebSocket(), { wrapper })
    await waitFor(() => expect(result.current.state).toBe('CONNECTED'))

    const socket = MockWebSocket.latest()
    const payload = JSON.stringify(mockRetentionAlertWs)

    await act(async () => {
      socket?.onmessage?.(new MessageEvent('message', { data: payload }))
      socket?.onmessage?.(new MessageEvent('message', { data: payload }))
    })

    expect(result.current.diagnostics.lastAlertId).toBe('ALT-NEW')
    expect(result.current.seenAlertIds.has('ALT-NEW')).toBe(true)
  })

  it('ignores malformed messages without closing connection', async () => {
    const { result } = renderHook(() => useAlertsWebSocket(), { wrapper })
    await waitFor(() => expect(result.current.state).toBe('CONNECTED'))

    const socket = MockWebSocket.latest()
    await act(async () => {
      socket?.onmessage?.(new MessageEvent('message', { data: 'not-json' }))
      socket?.onmessage?.(new MessageEvent('message', { data: JSON.stringify({ type: 'UNKNOWN' }) }))
    })

    expect(result.current.state).toBe('CONNECTED')
  })

  it('reconnects after close with backoff', async () => {
    vi.useFakeTimers()
    const { result } = renderHook(() => useAlertsWebSocket(), { wrapper })

    await act(async () => {
      await Promise.resolve()
    })

    const first = MockWebSocket.latest()
    await act(async () => {
      first?.close()
    })

    expect(result.current.state).toBe('RECONNECTING')

    await act(async () => {
      vi.advanceTimersByTime(1000)
      await Promise.resolve()
    })

    expect(MockWebSocket.instances.length).toBeGreaterThan(1)
    vi.useRealTimers()
  })

  it('cleans up on unmount', async () => {
    const { unmount } = renderHook(() => useAlertsWebSocket(), { wrapper })
    await waitFor(() => expect(MockWebSocket.latest()?.readyState).toBe(MockWebSocket.OPEN))

    const socket = MockWebSocket.latest()
    unmount()

    expect(socket?.readyState).toBe(MockWebSocket.CLOSED)
  })
})
