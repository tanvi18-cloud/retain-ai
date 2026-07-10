import { Link } from 'react-router-dom'
import type { ReactNode } from 'react'

import type { AlertSummary } from '../../types/alert'
import type { AlertType, NotificationStatus, Severity } from '../../types/api'
import { formatDateTime } from '../../utils/date'
import { Badge, type BadgeVariant } from '../ui/Badge'
import { Button } from '../ui/Button'
import { Table, type TableColumn } from '../ui/Table'

export function severityLabel(severity: Severity): string {
  const labels: Record<Severity, string> = {
    LOW: 'Low',
    MEDIUM: 'Medium',
    HIGH: 'High',
    CRITICAL: 'Critical',
  }
  return labels[severity]
}

export function severityVariant(severity: Severity): BadgeVariant {
  const variants: Record<Severity, BadgeVariant> = {
    LOW: 'success',
    MEDIUM: 'info',
    HIGH: 'warning',
    CRITICAL: 'danger',
  }
  return variants[severity]
}

export function alertTypeLabel(alertType: AlertType): string {
  const labels: Record<AlertType, string> = {
    RULES_PREVIEW: 'Rules preview',
    AGENT_RECOMMENDATION: 'Agent recommendation',
    SYSTEM: 'System',
  }
  return labels[alertType]
}

export function notificationStatusLabel(status: NotificationStatus): string {
  const labels: Record<NotificationStatus, string> = {
    PENDING: 'Pending',
    SENT: 'Sent',
    PARTIAL: 'Partial',
    FAILED: 'Failed',
    NOT_REQUIRED: 'Not required',
  }
  return labels[status]
}

export function notificationStatusVariant(status: NotificationStatus): BadgeVariant {
  const variants: Record<NotificationStatus, BadgeVariant> = {
    PENDING: 'warning',
    SENT: 'success',
    PARTIAL: 'warning',
    FAILED: 'danger',
    NOT_REQUIRED: 'neutral',
  }
  return variants[status]
}

export interface AlertTableProps {
  rows: AlertSummary[]
  loading?: boolean
  sortKey?: string
  sortOrder?: 'asc' | 'desc'
  onSort?: (key: string) => void
  onAcknowledge?: (alertId: string) => void
  acknowledgingId?: string | null
  emptyState?: ReactNode
}

export function AlertTable({
  rows,
  loading,
  sortKey,
  sortOrder,
  onSort,
  onAcknowledge,
  acknowledgingId,
  emptyState,
}: AlertTableProps) {
  const columns: TableColumn<AlertSummary>[] = [
    {
      key: 'title',
      header: 'Alert',
      render: (row) => (
        <div>
          <p className="font-medium text-slate-900">{row.title}</p>
          <p className="text-xs text-slate-500">{row.alert_id}</p>
        </div>
      ),
    },
    {
      key: 'customer_id',
      header: 'Customer',
      sortable: Boolean(onSort),
      render: (row) => <span className="font-medium">{row.customer_id}</span>,
    },
    {
      key: 'severity',
      header: 'Severity',
      sortable: Boolean(onSort),
      render: (row) => <Badge variant={severityVariant(row.severity)}>{severityLabel(row.severity)}</Badge>,
    },
    {
      key: 'alert_type',
      header: 'Type',
      render: (row) => <Badge variant="neutral">{alertTypeLabel(row.alert_type)}</Badge>,
    },
    {
      key: 'priority_score',
      header: 'Priority',
      sortable: Boolean(onSort),
      render: (row) => (
        <span className="font-semibold">{row.priority_score != null ? row.priority_score : '—'}</span>
      ),
    },
    {
      key: 'notification_status',
      header: 'Notification',
      render: (row) => (
        <Badge variant={notificationStatusVariant(row.notification_status)}>
          {notificationStatusLabel(row.notification_status)}
        </Badge>
      ),
    },
    {
      key: 'created_at',
      header: 'Created',
      sortable: Boolean(onSort),
      render: (row) => formatDateTime(row.created_at),
    },
    {
      key: 'acknowledged',
      header: 'Status',
      render: (row) => (
        <Badge variant={row.acknowledged ? 'success' : 'warning'}>
          {row.acknowledged ? 'Acknowledged' : 'Unacknowledged'}
        </Badge>
      ),
    },
    {
      key: 'actions',
      header: '',
      render: (row) => (
        <div className="flex flex-wrap gap-2">
          <Link
            to={`/customers/${row.customer_id}`}
            className="inline-flex h-8 items-center rounded-lg border border-slate-300 bg-white px-3 text-sm font-medium text-slate-800 hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
          >
            View customer
          </Link>
          {row.recommendation_id ? (
            <Link
              to={`/customers/${row.customer_id}`}
              className="inline-flex h-8 items-center rounded-lg border border-slate-300 bg-white px-3 text-sm font-medium text-slate-800 hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
            >
              View recommendation
            </Link>
          ) : null}
          {!row.acknowledged && onAcknowledge ? (
            <Button
              size="sm"
              variant="secondary"
              loading={acknowledgingId === row.alert_id}
              onClick={() => onAcknowledge(row.alert_id)}
            >
              Acknowledge
            </Button>
          ) : null}
        </div>
      ),
    },
  ]

  return (
    <Table
      columns={columns}
      data={rows}
      rowKey={(row) => row.alert_id}
      loading={loading}
      sortKey={sortKey}
      sortOrder={sortOrder}
      onSort={onSort}
      emptyState={emptyState}
    />
  )
}
