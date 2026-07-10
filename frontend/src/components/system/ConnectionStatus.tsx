import { useQuery } from '@tanstack/react-query'
import { Plug, Radio } from 'lucide-react'
import type { ReactNode } from 'react'

import { fetchHealth } from '../../api/health'
import { useAlertsWebSocket } from '../../hooks/useAlertsWebSocket'
import { queryKeys } from '../../utils/queryKeys'
import { cn } from '../../utils/cn'
import { Badge, type BadgeVariant } from '../ui/Badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/Card'

type ConnectionState = 'connected' | 'checking' | 'unavailable' | 'reconnecting' | 'error'

const API_LABELS: Record<ConnectionState, string> = {
  connected: 'API Connected',
  checking: 'Checking API…',
  unavailable: 'API Unavailable',
  reconnecting: 'API reconnecting',
  error: 'API Unavailable',
}

const WS_LABELS: Record<ConnectionState, string> = {
  connected: 'Live alerts connected',
  checking: 'Connecting live alerts…',
  unavailable: 'Live alerts unavailable',
  reconnecting: 'Reconnecting',
  error: 'Live alerts unavailable',
}

const STATE_VARIANT: Record<ConnectionState, BadgeVariant> = {
  connected: 'success',
  checking: 'info',
  unavailable: 'danger',
  reconnecting: 'warning',
  error: 'danger',
}

const STATE_INDICATOR: Record<ConnectionState, string> = {
  connected: 'bg-emerald-500',
  checking: 'bg-sky-500 animate-pulse',
  unavailable: 'bg-red-500',
  reconnecting: 'bg-amber-500 animate-pulse',
  error: 'bg-red-500',
}

function mapWebSocketState(
  state: ReturnType<typeof useAlertsWebSocket>['state'],
): ConnectionState {
  switch (state) {
    case 'CONNECTED':
      return 'connected'
    case 'CONNECTING':
      return 'checking'
    case 'RECONNECTING':
      return 'reconnecting'
    case 'ERROR':
    case 'DISCONNECTED':
      return 'unavailable'
    default:
      return 'unavailable'
  }
}

function StatusRow({
  icon,
  label,
  state,
}: {
  icon: ReactNode
  label: string
  state: ConnectionState
}) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-lg border border-slate-200 px-3 py-2.5">
      <div className="flex items-center gap-2 text-sm text-slate-700">
        {icon}
        <span>{label}</span>
      </div>
      <Badge variant={STATE_VARIANT[state]} className="gap-1.5">
        <span
          className={cn('h-2 w-2 rounded-full', STATE_INDICATOR[state])}
          aria-hidden="true"
        />
        <span className="sr-only">Status: </span>
        {label}
      </Badge>
    </div>
  )
}

export interface ConnectionStatusProps {
  compact?: boolean
  className?: string
}

export function ConnectionStatus({ compact = false, className }: ConnectionStatusProps) {
  const healthQuery = useQuery({
    queryKey: queryKeys.health,
    queryFn: fetchHealth,
    refetchInterval: 60_000,
    retry: 1,
    staleTime: 30_000,
  })

  const { state: wsState } = useAlertsWebSocket()

  const apiState: ConnectionState =
    healthQuery.isFetching && !healthQuery.data
      ? 'checking'
      : healthQuery.isError || !healthQuery.data
        ? 'unavailable'
        : 'connected'

  const wsConnectionState = mapWebSocketState(wsState)

  if (compact) {
    return (
      <div
        className={cn('flex flex-wrap items-center gap-2', className)}
        aria-live="polite"
        aria-label="Connection status"
      >
        <Badge variant={STATE_VARIANT[apiState]} className="gap-1.5">
          <Plug className="h-3 w-3" aria-hidden="true" />
          {API_LABELS[apiState]}
        </Badge>
        <Badge variant={STATE_VARIANT[wsConnectionState]} className="gap-1.5">
          <Radio className="h-3 w-3" aria-hidden="true" />
          {WS_LABELS[wsConnectionState]}
        </Badge>
      </div>
    )
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Connection status</CardTitle>
        <CardDescription>API health and live alert WebSocket connectivity</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3" aria-live="polite">
        <StatusRow
          icon={<Plug className="h-4 w-4 text-slate-500" aria-hidden="true" />}
          label={API_LABELS[apiState]}
          state={apiState}
        />
        <StatusRow
          icon={<Radio className="h-4 w-4 text-slate-500" aria-hidden="true" />}
          label={WS_LABELS[wsConnectionState]}
          state={wsConnectionState}
        />
      </CardContent>
    </Card>
  )
}
