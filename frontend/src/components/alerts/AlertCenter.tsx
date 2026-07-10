import { useMemo, type ReactNode } from 'react'

import type { AlertSummary } from '../../types/alert'
import { cn } from '../../utils/cn'
import { AlertCard } from './AlertCard'
import { AlertFilters, type AlertFiltersState } from './AlertFilters'
import { AlertTable } from './AlertTable'

export type AlertTab = 'all' | 'unacknowledged' | 'high_priority' | 'acknowledged'

export interface AlertCenterProps {
  alerts: AlertSummary[]
  loading?: boolean
  activeTab: AlertTab
  onTabChange: (tab: AlertTab) => void
  filters: AlertFiltersState
  onFiltersChange: (filters: AlertFiltersState) => void
  onClearFilters?: () => void
  onAcknowledge?: (alertId: string) => void
  acknowledgingId?: string | null
  sortKey?: string
  sortOrder?: 'asc' | 'desc'
  onSort?: (key: string) => void
  emptyState?: ReactNode
}

const TABS: { id: AlertTab; label: string }[] = [
  { id: 'all', label: 'All' },
  { id: 'unacknowledged', label: 'Unacknowledged' },
  { id: 'high_priority', label: 'High Priority' },
  { id: 'acknowledged', label: 'Acknowledged' },
]

function isHighPriorityAlert(alert: AlertSummary): boolean {
  if (alert.severity === 'HIGH' || alert.severity === 'CRITICAL') return true
  return alert.priority_score != null && alert.priority_score >= 75
}

function filterAlertsByTab(alerts: AlertSummary[], tab: AlertTab): AlertSummary[] {
  switch (tab) {
    case 'unacknowledged':
      return alerts.filter((alert) => !alert.acknowledged)
    case 'acknowledged':
      return alerts.filter((alert) => alert.acknowledged)
    case 'high_priority':
      return alerts.filter(isHighPriorityAlert)
    default:
      return alerts
  }
}

export function AlertCenter({
  alerts,
  loading,
  activeTab,
  onTabChange,
  filters,
  onFiltersChange,
  onClearFilters,
  onAcknowledge,
  acknowledgingId,
  sortKey,
  sortOrder,
  onSort,
  emptyState,
}: AlertCenterProps) {
  const visibleAlerts = useMemo(
    () => filterAlertsByTab(alerts, activeTab),
    [alerts, activeTab],
  )

  return (
    <div className="space-y-4">
      <div
        role="tablist"
        aria-label="Alert views"
        className="flex flex-wrap gap-1 border-b border-slate-200"
      >
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={activeTab === tab.id}
            aria-controls={`alert-tabpanel-${tab.id}`}
            id={`alert-tab-${tab.id}`}
            className={cn(
              'rounded-t-lg px-4 py-2 text-sm font-medium transition-colors',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400',
              activeTab === tab.id
                ? 'border-b-2 border-slate-900 text-slate-900'
                : 'text-slate-500 hover:text-slate-800',
            )}
            onClick={() => onTabChange(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <AlertFilters values={filters} onChange={onFiltersChange} onClear={onClearFilters} />

      <div
        role="tabpanel"
        id={`alert-tabpanel-${activeTab}`}
        aria-labelledby={`alert-tab-${activeTab}`}
        className="space-y-4"
      >
        <div className="hidden md:block">
          <AlertTable
            rows={visibleAlerts}
            loading={loading}
            sortKey={sortKey}
            sortOrder={sortOrder}
            onSort={onSort}
            onAcknowledge={onAcknowledge}
            acknowledgingId={acknowledgingId}
            emptyState={emptyState}
          />
        </div>

        <div className="grid gap-4 md:hidden">
          {loading ? (
            Array.from({ length: 3 }).map((_, index) => (
              <div
                key={`alert-card-skeleton-${index}`}
                className="h-56 animate-pulse rounded-xl border border-slate-200 bg-slate-100"
              />
            ))
          ) : visibleAlerts.length === 0 ? (
            (emptyState ?? (
              <p className="rounded-xl border border-dashed border-slate-200 bg-slate-50 px-6 py-12 text-center text-sm text-slate-500">
                No alerts match the current view.
              </p>
            ))
          ) : (
            visibleAlerts.map((alert) => (
              <AlertCard
                key={alert.alert_id}
                alert={alert}
                showAcknowledge={onAcknowledge != null}
                onAcknowledge={onAcknowledge}
                acknowledging={acknowledgingId === alert.alert_id}
              />
            ))
          )}
        </div>
      </div>
    </div>
  )
}
