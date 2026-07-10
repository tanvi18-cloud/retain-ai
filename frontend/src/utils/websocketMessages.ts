import type {
  RetentionAlertMessage,
  WebSocketConnectedMessage,
  WebSocketConnectionState,
  WebSocketInboundMessage,
  WebSocketPongMessage,
} from '../types/alert'

const PING_INTERVAL_MS = 30_000
const INITIAL_RECONNECT_MS = 1_000
const MAX_RECONNECT_MS = 30_000

export function isRetentionAlertMessage(
  message: WebSocketInboundMessage,
): message is RetentionAlertMessage {
  return message.type === 'RETENTION_ALERT'
}

export function isConnectedMessage(
  message: WebSocketInboundMessage,
): message is WebSocketConnectedMessage {
  return message.type === 'CONNECTED'
}

export function isPongMessage(
  message: WebSocketInboundMessage,
): message is WebSocketPongMessage {
  return message.type === 'PONG'
}

export function parseWebSocketMessage(data: unknown): WebSocketInboundMessage | null {
  if (typeof data !== 'object' || data === null || !('type' in data)) {
    return null
  }
  const record = data as Record<string, unknown>
  const type = record.type
  if (type === 'CONNECTED' && typeof record.message === 'string') {
    return {
      type: 'CONNECTED',
      message: record.message,
      timestamp: String(record.timestamp ?? ''),
    }
  }
  if (type === 'PONG') {
    return { type: 'PONG', timestamp: String(record.timestamp ?? '') }
  }
  if (
    type === 'RETENTION_ALERT' &&
    typeof record.alert_id === 'string' &&
    typeof record.customer_id === 'string'
  ) {
    return record as unknown as RetentionAlertMessage
  }
  return null
}

export interface WebSocketDiagnostics {
  url: string
  state: WebSocketConnectionState
  lastConnectedAt: string | null
  reconnectAttempt: number
  lastPongAt: string | null
  lastAlertId: string | null
}

export const WS_CONSTANTS = {
  PING_INTERVAL_MS,
  INITIAL_RECONNECT_MS,
  MAX_RECONNECT_MS,
}
