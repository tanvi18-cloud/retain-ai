import { RefreshCw } from 'lucide-react'

import { useAlertsWebSocket } from '../../hooks/useAlertsWebSocket'
import { formatDateTime } from '../../utils/date'
import { Badge } from '../ui/Badge'
import { Button } from '../ui/Button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/Card'

function sanitizeWsUrl(url: string): string {
  try {
    const parsed = new URL(url)
    if (parsed.search) {
      parsed.search = '?[redacted]'
    }
    if (parsed.password) {
      parsed.password = '[redacted]'
    }
    return parsed.toString()
  } catch {
    return url.replace(/([?&][^=]+)=([^&]+)/g, '$1[redacted]')
  }
}

const STATE_LABELS = {
  CONNECTING: 'Connecting',
  CONNECTED: 'Connected',
  RECONNECTING: 'Reconnecting',
  DISCONNECTED: 'Disconnected',
  ERROR: 'Error',
} as const

export function WebSocketDiagnostics() {
  const { state, diagnostics, seenAlertIds, reconnect } = useAlertsWebSocket()

  if (!import.meta.env.DEV) {
    return null
  }

  return (
    <Card className="border-dashed border-amber-300 bg-amber-50/40">
      <CardHeader>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <CardTitle>WebSocket diagnostics</CardTitle>
            <CardDescription>Development only — uses the shared alert connection</CardDescription>
          </div>
          <Badge variant="warning">DEV</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <dl className="grid gap-3 text-sm sm:grid-cols-2">
          <div className="sm:col-span-2">
            <dt className="text-xs text-slate-500">WebSocket URL</dt>
            <dd className="break-all font-mono text-xs text-slate-800">
              {sanitizeWsUrl(diagnostics.url)}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-slate-500">Connection state</dt>
            <dd className="font-medium text-slate-900">{STATE_LABELS[state]}</dd>
          </div>
          <div>
            <dt className="text-xs text-slate-500">Reconnect attempt</dt>
            <dd className="font-medium text-slate-900">{diagnostics.reconnectAttempt}</dd>
          </div>
          <div>
            <dt className="text-xs text-slate-500">Last connected</dt>
            <dd className="font-medium text-slate-900">
              {formatDateTime(diagnostics.lastConnectedAt)}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-slate-500">Last PONG</dt>
            <dd className="font-medium text-slate-900">
              {formatDateTime(diagnostics.lastPongAt)}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-slate-500">Last alert ID</dt>
            <dd className="font-mono text-xs text-slate-800">
              {diagnostics.lastAlertId ?? '—'}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-slate-500">Seen alert IDs</dt>
            <dd className="font-medium text-slate-900">{seenAlertIds.size}</dd>
          </div>
        </dl>

        <Button variant="outline" size="sm" onClick={reconnect} className="gap-2">
          <RefreshCw className="h-4 w-4" aria-hidden="true" />
          Manual reconnect
        </Button>
      </CardContent>
    </Card>
  )
}
