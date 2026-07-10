import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'

import { resetLiveAlertToastsForTests } from '../components/alerts/LiveAlertToast'
import { __resetAlertsWebSocketForTests } from '../hooks/useAlertsWebSocket'

type WebSocketListener = ((event: Event) => void) | null

export class MockWebSocket {
  static CONNECTING = 0
  static OPEN = 1
  static CLOSING = 2
  static CLOSED = 3

  static instances: MockWebSocket[] = []

  url: string
  readyState = MockWebSocket.CONNECTING
  onopen: WebSocketListener = null
  onclose: WebSocketListener = null
  onerror: WebSocketListener = null
  onmessage: WebSocketListener = null
  sent: string[] = []
  private listeners = new Map<string, Set<EventListener>>()

  constructor(url: string) {
    this.url = url
    MockWebSocket.instances.push(this)
    queueMicrotask(() => {
      if (this.readyState === MockWebSocket.CLOSED) return
      this.readyState = MockWebSocket.OPEN
      this.dispatchEvent(new Event('open'))
      this.onmessage?.(
        new MessageEvent('message', {
          data: JSON.stringify({
            type: 'CONNECTED',
            message: 'Connected',
            timestamp: new Date().toISOString(),
          }),
        }),
      )
    })
  }

  addEventListener(type: string, listener: EventListener) {
    if (!this.listeners.has(type)) this.listeners.set(type, new Set())
    this.listeners.get(type)!.add(listener)
  }

  removeEventListener(type: string, listener: EventListener) {
    this.listeners.get(type)?.delete(listener)
  }

  dispatchEvent(event: Event): boolean {
    this.listeners.get(event.type)?.forEach((listener) => listener(event))
    if (event.type === 'open') this.onopen?.(event)
    if (event.type === 'close') this.onclose?.(event)
    if (event.type === 'error') this.onerror?.(event)
    if (event.type === 'message') this.onmessage?.(event as MessageEvent)
    return true
  }

  send(data: string) {
    this.sent.push(data)
    try {
      const parsed = JSON.parse(data) as { type?: string }
      if (parsed.type === 'PING') {
        this.onmessage?.(
          new MessageEvent('message', {
            data: JSON.stringify({ type: 'PONG', timestamp: new Date().toISOString() }),
          }),
        )
      }
    } catch {
      // ignore malformed test payloads
    }
  }

  close() {
    this.readyState = MockWebSocket.CLOSED
    this.dispatchEvent(new Event('close'))
  }

  static reset() {
    MockWebSocket.instances.forEach((socket) => socket.close())
    MockWebSocket.instances = []
  }

  static latest(): MockWebSocket | undefined {
    return MockWebSocket.instances[MockWebSocket.instances.length - 1]
  }
}

beforeAll(() => {
  vi.stubGlobal('WebSocket', MockWebSocket as unknown as typeof WebSocket)
})

afterEach(() => {
  cleanup()
  resetLiveAlertToastsForTests()
  __resetAlertsWebSocketForTests()
  MockWebSocket.reset()
  vi.useRealTimers()
})
