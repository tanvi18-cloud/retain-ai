import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'

import { acknowledgeAlert, fetchAlerts } from '../api/alerts'
import { getRmUser } from '../api/env'
import { AlertCenter, type AlertTab } from '../components/alerts/AlertCenter'
import type { AlertFiltersState } from '../components/alerts/AlertFilters'
import { PageHeader } from '../components/layout/PageHeader'
import { ConfirmDialog } from '../components/ui/ConfirmDialog'
import { EmptyState } from '../components/ui/EmptyState'
import { ErrorState } from '../components/ui/ErrorState'
import { useDocumentTitle } from '../hooks/useDocumentTitle'
import type { AlertType, Severity } from '../types/api'
import { queryKeys } from '../utils/queryKeys'

export function AlertsPage() {
  useDocumentTitle('Retention Alerts')
  const queryClient = useQueryClient()
  const rm = getRmUser()
  const [searchParams, setSearchParams] = useSearchParams()
  const [ackTarget, setAckTarget] = useState<string | null>(null)

  const tab = (searchParams.get('tab') as AlertTab) || 'all'
  const page = Number(searchParams.get('page') ?? '1')
  const severity = (searchParams.get('severity') as Severity | null) ?? undefined
  const alertType = (searchParams.get('alert_type') as AlertType | null) ?? undefined
  const customerId = searchParams.get('customer_id') ?? undefined
  const acknowledgedParam = searchParams.get('acknowledged')
  const acknowledged =
    acknowledgedParam === 'true' ? true : acknowledgedParam === 'false' ? false : undefined

  const filters: AlertFiltersState = {
    severity,
    alert_type: alertType,
    customer_id: customerId,
    acknowledged,
  }

  const queryParams = useMemo(
    () => ({
      page,
      page_size: 20,
      severity,
      alert_type: alertType,
      customer_id: customerId,
      acknowledged: tab === 'unacknowledged' ? false : tab === 'acknowledged' ? true : acknowledged,
      sort_order: 'desc' as const,
    }),
    [page, severity, alertType, customerId, acknowledged, tab],
  )

  const query = useQuery({
    queryKey: queryKeys.alerts.list(queryParams),
    queryFn: () => fetchAlerts(queryParams),
  })

  const ackMutation = useMutation({
    mutationFn: (alertId: string) =>
      acknowledgeAlert(alertId, { rm_id: rm.id, note: null }),
    onSuccess: () => {
      toast.success('Alert acknowledged')
      setAckTarget(null)
      void queryClient.invalidateQueries({ queryKey: ['alerts'] })
      void queryClient.invalidateQueries({ queryKey: queryKeys.portfolio.summary })
    },
    onError: () => toast.error('Unable to acknowledge alert'),
  })

  const updateParam = (key: string, value: string | null) => {
    const next = new URLSearchParams(searchParams)
    if (!value) next.delete(key)
    else next.set(key, value)
    if (key !== 'page') next.set('page', '1')
    setSearchParams(next)
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Retention Alerts"
        description="Review, acknowledge, and act on portfolio retention alerts. Live alerts also appear via WebSocket."
      />

      {query.isError ? (
        <ErrorState message="Unable to load alerts." onRetry={() => query.refetch()} />
      ) : (
        <>
          <AlertCenter
            alerts={query.data?.items ?? []}
            loading={query.isLoading}
            activeTab={tab}
            onTabChange={(t) => updateParam('tab', t === 'all' ? null : t)}
            filters={filters}
            onFiltersChange={(f) => {
              updateParam('severity', f.severity ?? null)
              updateParam('alert_type', f.alert_type ?? null)
              updateParam('customer_id', f.customer_id ?? null)
              updateParam(
                'acknowledged',
                f.acknowledged === true ? 'true' : f.acknowledged === false ? 'false' : null,
              )
            }}
            onClearFilters={() => setSearchParams({ page: '1' })}
            onAcknowledge={(id) => setAckTarget(id)}
            acknowledgingId={ackMutation.isPending ? ackTarget : null}
            emptyState={
              <EmptyState
                title="No alerts found"
                description="Adjust filters or wait for new retention signals."
              />
            }
          />
          {query.data && query.data.pages > 1 ? (
            <div className="flex justify-between text-sm text-slate-500">
              <span>
                Page {query.data.page} of {query.data.pages}
              </span>
              <div className="flex gap-2">
                <button
                  type="button"
                  className="rounded border px-3 py-1 disabled:opacity-50"
                  disabled={page <= 1}
                  onClick={() => updateParam('page', String(page - 1))}
                >
                  Previous
                </button>
                <button
                  type="button"
                  className="rounded border px-3 py-1 disabled:opacity-50"
                  disabled={page >= query.data.pages}
                  onClick={() => updateParam('page', String(page + 1))}
                >
                  Next
                </button>
              </div>
            </div>
          ) : null}
        </>
      )}

      <ConfirmDialog
        open={Boolean(ackTarget)}
        onClose={() => setAckTarget(null)}
        onConfirm={() => ackTarget && ackMutation.mutate(ackTarget)}
        title="Acknowledge alert"
        description="Mark this alert as reviewed. This does not approve any product or credit action."
        confirmLabel="Acknowledge"
        loading={ackMutation.isPending}
      />
    </div>
  )
}
