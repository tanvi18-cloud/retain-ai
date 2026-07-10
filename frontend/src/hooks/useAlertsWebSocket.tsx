import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react'
import { useQueryClient } from '@tanstack/react-query'

import { getEnv } from '../api/env'
import type {
  RetentionAlertMessage,
  WebSocketConnectionState,
} from '../types/alert'
import { queryKeys } from '../utils/queryKeys'
import {
  parseWebSocketMessage,
  WS_CONSTANTS,
  type WebSocketDiagnostics,
} from '../utils/websocketMessages'
import { showRetentionAlertToast } from '../components/alerts/LiveAlertToast'

interface AlertsWebSocketContextValue {
  state: WebSocketConnectionState
  diagnostics: WebSocketDiagnostics
  seenAlertIds: ReadonlySet<string>
  reconnect: () => void
}

const AlertsWebSocketContext = createContext<AlertsWebSocketContextValue | null>(null)

let globalSocket: WebSocket | null = null
let globalSocketUrl: string | null = null
let subscriberCount = 0

export function AlertsWebSocketProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const [state, setState] = useState<WebSocketConnectionState>('DISCONNECTED')
  const [diagnostics, setDiagnostics] = useState<WebSocketDiagnostics>({
    url: getEnv().wsBaseUrl,
    state: 'DISCONNECTED',
    lastConnectedAt: null,
    reconnectAttempt: 0,
    lastPongAt: null,
    lastAlertId: null,
  })
  const seenAlertIdsRef = useRef<Set<string>>(new Set())
  const [, setSeenVersion] = useState(0)
  const reconnectDelayRef = useRef(WS_CONSTANTS.INITIAL_RECONNECT_MS)
  const reconnectTimerRef = useRef<number | null>(null)
  const pingTimerRef = useRef<number | null>(null)
  const mountedRef = useRef(true)
  const toastOnReconnectRef = useRef(false)

  const clearTimers = useCallback(() => {
    if (reconnectTimerRef.current !== null) {
      window.clearTimeout(reconnectTimerRef.current)
      reconnectTimerRef.current = null
    }
    if (pingTimerRef.current !== null) {
      window.clearInterval(pingTimerRef.current)
      pingTimerRef.current = null
    }
  }, [])

  const handleAlert = useCallback(
    (alert: RetentionAlertMessage) => {
      if (seenAlertIdsRef.current.has(alert.alert_id)) return
      seenAlertIdsRef.current.add(alert.alert_id)
      setSeenVersion((v) => v + 1)

      setDiagnostics((prev) => ({ ...prev, lastAlertId: alert.alert_id }))

      void queryClient.invalidateQueries({ queryKey: ['alerts'] })
      void queryClient.invalidateQueries({ queryKey: queryKeys.portfolio.summary })

      if (!toastOnReconnectRef.current) {
        showRetentionAlertToast(alert)
      }
    },
    [queryClient],
  )

  const schedulePing = useCallback((socket: WebSocket) => {
    if (pingTimerRef.current !== null) window.clearInterval(pingTimerRef.current)
    pingTimerRef.current = window.setInterval(() => {
      if (socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: 'PING' }))
      }
    }, WS_CONSTANTS.PING_INTERVAL_MS)
  }, [])

  const connect = useCallback(() => {
    const url = getEnv().wsBaseUrl
    if (globalSocket && globalSocketUrl === url && globalSocket.readyState <= WebSocket.OPEN) {
      return
    }

    if (globalSocket) {
      globalSocket.close()
      globalSocket = null
    }

    setState('CONNECTING')
    setDiagnostics((prev) => ({ ...prev, url, state: 'CONNECTING' }))

    if (import.meta.env.DEV) {
      console.info('[RetainAI WS] Connecting…')
    }

    const socket = new WebSocket(url)
    globalSocket = socket
    globalSocketUrl = url

    socket.onopen = () => {
      if (!mountedRef.current) return
      reconnectDelayRef.current = WS_CONSTANTS.INITIAL_RECONNECT_MS
      toastOnReconnectRef.current = false
      const now = new Date().toISOString()
      setState('CONNECTED')
      setDiagnostics((prev) => ({
        ...prev,
        state: 'CONNECTED',
        lastConnectedAt: now,
        reconnectAttempt: 0,
      }))
      schedulePing(socket)
    }

    socket.onmessage = (event) => {
      if (!mountedRef.current) return
      try {
        const parsed = parseWebSocketMessage(JSON.parse(String(event.data)))
        if (!parsed) return
        if (parsed.type === 'PONG') {
          setDiagnostics((prev) => ({ ...prev, lastPongAt: parsed.timestamp || new Date().toISOString() }))
          return
        }
        if (parsed.type === 'CONNECTED') {
          setDiagnostics((prev) => {
            if (prev.reconnectAttempt > 0) {
              toastOnReconnectRef.current = true
              window.setTimeout(() => {
                toastOnReconnectRef.current = false
              }, 2000)
            }
            return prev
          })
          return
        }
        if (parsed.type === 'RETENTION_ALERT') {
          handleAlert(parsed)
        }
      } catch {
        if (import.meta.env.DEV) console.warn('[RetainAI WS] Malformed message ignored')
      }
    }

    socket.onerror = () => {
      if (!mountedRef.current) return
      setState('ERROR')
      setDiagnostics((prev) => ({ ...prev, state: 'ERROR' }))
    }

    socket.onclose = () => {
      if (!mountedRef.current) return
      globalSocket = null
      clearTimers()
      setState('RECONNECTING')
      const attempt = reconnectDelayRef.current
      setDiagnostics((prev) => ({
        ...prev,
        state: 'RECONNECTING',
        reconnectAttempt: prev.reconnectAttempt + 1,
      }))
      reconnectTimerRef.current = window.setTimeout(() => {
        reconnectDelayRef.current = Math.min(
          reconnectDelayRef.current * 2,
          WS_CONSTANTS.MAX_RECONNECT_MS,
        )
        connect()
      }, attempt)
    }
  }, [clearTimers, handleAlert, schedulePing])

  const reconnect = useCallback(() => {
    reconnectDelayRef.current = WS_CONSTANTS.INITIAL_RECONNECT_MS
    clearTimers()
    if (globalSocket) {
      globalSocket.close()
      globalSocket = null
    }
    connect()
  }, [clearTimers, connect])

  useEffect(() => {
    mountedRef.current = true
    subscriberCount += 1
    if (subscriberCount === 1) connect()

    return () => {
      mountedRef.current = false
      subscriberCount -= 1
      clearTimers()
      if (subscriberCount === 0 && globalSocket) {
        globalSocket.close()
        globalSocket = null
        globalSocketUrl = null
      }
    }
  }, [clearTimers, connect])

  const value = useMemo<AlertsWebSocketContextValue>(
    () => ({
      state,
      diagnostics,
      seenAlertIds: seenAlertIdsRef.current,
      reconnect,
    }),
    [diagnostics, reconnect, state],
  )

  return (
    <AlertsWebSocketContext.Provider value={value}>{children}</AlertsWebSocketContext.Provider>
  )
}

export function useAlertsWebSocket(): AlertsWebSocketContextValue {
  const context = useContext(AlertsWebSocketContext)
  if (!context) {
    throw new Error('useAlertsWebSocket must be used within AlertsWebSocketProvider')
  }
  return context
}

/** Reset global socket state for tests only */
export function __resetAlertsWebSocketForTests(): void {
  if (globalSocket) {
    globalSocket.close()
    globalSocket = null
    globalSocketUrl = null
  }
  subscriberCount = 0
}
