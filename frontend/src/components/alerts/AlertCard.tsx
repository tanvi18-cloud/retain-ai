import { Link } from 'react-router-dom'

import type { AlertSummary } from '../../types/alert'
import { formatDateTime } from '../../utils/date'
import { cn } from '../../utils/cn'
import { Badge } from '../ui/Badge'
import { Button } from '../ui/Button'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '../ui/Card'
import {
  alertTypeLabel,
  notificationStatusLabel,
  notificationStatusVariant,
  severityLabel,
  severityVariant,
} from './AlertTable'

export interface AlertCardProps {
  alert: AlertSummary
  showAcknowledge?: boolean
  onAcknowledge?: (alertId: string) => void
  acknowledging?: boolean
  className?: string
}

export function AlertCard({
  alert,
  showAcknowledge = false,
  onAcknowledge,
  acknowledging = false,
  className,
}: AlertCardProps) {
  const canAcknowledge = showAcknowledge && !alert.acknowledged && onAcknowledge != null

  return (
    <Card className={cn('flex flex-col', className)}>
      <CardHeader className="space-y-3">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <Badge variant={severityVariant(alert.severity)}>{severityLabel(alert.severity)}</Badge>
          <Badge variant={alert.acknowledged ? 'success' : 'warning'}>
            {alert.acknowledged ? 'Acknowledged' : 'Unacknowledged'}
          </Badge>
        </div>
        <CardTitle className="text-sm leading-snug">{alert.title}</CardTitle>
      </CardHeader>
      <CardContent className="grid flex-1 gap-3 text-sm">
        <div>
          <p className="text-xs text-slate-500">Customer</p>
          <p className="font-medium text-slate-900">{alert.customer_id}</p>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <p className="text-xs text-slate-500">Alert type</p>
            <Badge variant="neutral" className="mt-1">
              {alertTypeLabel(alert.alert_type)}
            </Badge>
          </div>
          <div>
            <p className="text-xs text-slate-500">Priority</p>
            <p className="font-semibold text-slate-900">
              {alert.priority_score != null ? alert.priority_score : '—'}
            </p>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <p className="text-xs text-slate-500">Notification</p>
            <Badge variant={notificationStatusVariant(alert.notification_status)} className="mt-1">
              {notificationStatusLabel(alert.notification_status)}
            </Badge>
          </div>
          <div>
            <p className="text-xs text-slate-500">Created</p>
            <p className="font-medium text-slate-900">{formatDateTime(alert.created_at)}</p>
          </div>
        </div>
      </CardContent>
      <CardFooter className="flex flex-wrap gap-2">
        <Link
          to={`/customers/${alert.customer_id}`}
          className="inline-flex h-8 items-center rounded-lg border border-slate-300 bg-white px-3 text-sm font-medium text-slate-800 hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
        >
          View customer
        </Link>
        {alert.recommendation_id ? (
          <Link
            to={`/customers/${alert.customer_id}`}
            className="inline-flex h-8 items-center rounded-lg border border-slate-300 bg-white px-3 text-sm font-medium text-slate-800 hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
          >
            View recommendation
          </Link>
        ) : null}
        {canAcknowledge ? (
          <Button
            size="sm"
            variant="secondary"
            loading={acknowledging}
            onClick={() => onAcknowledge(alert.alert_id)}
          >
            Acknowledge
          </Button>
        ) : null}
      </CardFooter>
    </Card>
  )
}
