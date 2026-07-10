import { ws } from 'msw'

import type { RetentionAlertMessage } from '../types/alert'

const WS_ALERTS_URL = 'ws://127.0.0.1:8001/ws/alerts'

export const alertsWebSocketLink = ws.link(WS_ALERTS_URL)

function pongForPing(raw: string): string | null {
  try {
    const parsed = JSON.parse(raw) as { type?: string }
    if (parsed.type === 'PING') {
      return JSON.stringify({ type: 'PONG', timestamp: new Date().toISOString() })
    }
  } catch {
    return null
  }
  return null
}

/** MSW WebSocket handler — CONNECTED + application-level PING/PONG for alert stream. */
export const alertsWebSocketHandler = alertsWebSocketLink.addEventListener(
  'connection',
  ({ client }) => {
    queueMicrotask(() => {
      client.send(
        JSON.stringify({
          type: 'CONNECTED',
          message: 'Connected to RetainAI alerts',
          timestamp: new Date().toISOString(),
        }),
      )
    })

    client.addEventListener('message', (event) => {
      const raw = typeof event.data === 'string' ? event.data : String(event.data)
      const pong = pongForPing(raw)
      if (pong) {
        client.send(pong)
      }
    })
  },
)

export function broadcastTestRetentionAlert(alert: RetentionAlertMessage): void {
  alertsWebSocketLink.broadcast(JSON.stringify(alert))
}
