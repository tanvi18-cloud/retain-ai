import { useQuery } from '@tanstack/react-query'
import { Bell, Mail } from 'lucide-react'

import { fetchNotificationStatus } from '../../api/system'
import { queryKeys } from '../../utils/queryKeys'
import { Badge } from '../ui/Badge'
import { ErrorState } from '../ui/ErrorState'
import { Skeleton } from '../ui/Skeleton'
import { StatusCard } from './StatusCard'

const POLL_INTERVAL_MS = 30_000

export function NotificationStatusPanel() {
  const query = useQuery({
    queryKey: queryKeys.system.notification,
    queryFn: fetchNotificationStatus,
    refetchInterval: POLL_INTERVAL_MS,
    staleTime: 15_000,
  })

  if (query.isLoading) {
    return (
      <StatusCard
        title="Notifications"
        statusLabel="Loading…"
        state="loading"
        icon={<Bell className="h-4 w-4" aria-hidden="true" />}
        description="Email and WebSocket alert delivery configuration"
      >
        <div className="space-y-2">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-2/3" />
        </div>
      </StatusCard>
    )
  }

  if (query.isError || !query.data) {
    return (
      <div className="space-y-3">
        <StatusCard
          title="Notifications"
          statusLabel="Unavailable"
          state="error"
          icon={<Bell className="h-4 w-4" aria-hidden="true" />}
          description="Email and WebSocket alert delivery configuration"
        />
        <ErrorState
          title="Notification status unavailable"
          message="Unable to load notification configuration."
          onRetry={() => query.refetch()}
        />
      </div>
    )
  }

  const data = query.data
  const emailReady = data.email_notifications_enabled && data.smtp_configured

  return (
    <StatusCard
      title="Notifications"
      statusLabel={emailReady ? 'Email and live alerts enabled' : 'Partial configuration'}
      state={emailReady ? 'healthy' : 'warning'}
      icon={<Bell className="h-4 w-4" aria-hidden="true" />}
      description="Email and WebSocket alert delivery configuration"
    >
      <div className="flex flex-wrap gap-2">
        <Badge variant={data.email_notifications_enabled ? 'success' : 'neutral'}>
          Email {data.email_notifications_enabled ? 'enabled' : 'disabled'}
        </Badge>
        <Badge variant={data.smtp_configured ? 'success' : 'warning'}>
          SMTP {data.smtp_configured ? 'configured' : 'not configured'}
        </Badge>
      </div>

      <dl className="mt-3 grid gap-3 text-sm sm:grid-cols-2">
        <div>
          <dt className="flex items-center gap-1 text-xs text-slate-500">
            <Mail className="h-3 w-3" aria-hidden="true" />
            SMTP host
          </dt>
          <dd className="font-medium text-slate-900">{data.smtp_host || '—'}</dd>
        </div>
        <div>
          <dt className="text-xs text-slate-500">SMTP port</dt>
          <dd className="font-medium text-slate-900">{data.smtp_port}</dd>
        </div>
        <div>
          <dt className="text-xs text-slate-500">WebSocket clients</dt>
          <dd className="font-medium text-slate-900">{data.websocket_connections}</dd>
        </div>
        <div>
          <dt className="text-xs text-slate-500">Alert priority threshold</dt>
          <dd className="font-medium text-slate-900">{data.alert_priority_threshold}</dd>
        </div>
      </dl>

      <p className="mt-3 text-xs text-slate-500">
        Credentials and secrets are never displayed on this page.
      </p>
    </StatusCard>
  )
}
