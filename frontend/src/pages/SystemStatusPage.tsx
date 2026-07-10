import { useQuery } from '@tanstack/react-query'

import { fetchHealth } from '../api/system'
import { getEnv } from '../api/env'
import { ConnectionStatus } from '../components/system/ConnectionStatus'
import { LLMStatusPanel } from '../components/system/LLMStatusPanel'
import { NotificationStatusPanel } from '../components/system/NotificationStatusPanel'
import { QueueStatusPanel } from '../components/system/QueueStatusPanel'
import { StatusCard } from '../components/system/StatusCard'
import { WebSocketDiagnostics } from '../components/system/WebSocketDiagnostics'
import { PageHeader } from '../components/layout/PageHeader'
import { useDocumentTitle } from '../hooks/useDocumentTitle'
import { queryKeys } from '../utils/queryKeys'

export function SystemStatusPage() {
  useDocumentTitle('System Status')
  const env = getEnv()

  const healthQuery = useQuery({
    queryKey: queryKeys.health,
    queryFn: fetchHealth,
    refetchInterval: 30_000,
  })

  if (!env.enableSystemPage) {
    return <p className="text-sm text-slate-500">System status page is disabled.</p>
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="System Status"
        description="Operational diagnostics for API, queue, LLM, notifications, and live alerts. No secrets are displayed."
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <StatusCard
          title="API"
          statusLabel={healthQuery.data?.status ?? '—'}
          description={`${env.appName} v${env.appVersion} · ${healthQuery.data?.environment ?? '—'}`}
          state={healthQuery.isError ? 'error' : healthQuery.isLoading ? 'loading' : 'healthy'}
        />
        <StatusCard
          title="Synthetic dataset"
          statusLabel="Loaded"
          description="Retail banking demo data for local RM workflow testing."
          state="neutral"
        />
      </div>

      <ConnectionStatus />
      <div className="grid gap-6 xl:grid-cols-2">
        <LLMStatusPanel />
        <QueueStatusPanel />
      </div>
      <NotificationStatusPanel />
      <WebSocketDiagnostics />
    </div>
  )
}
