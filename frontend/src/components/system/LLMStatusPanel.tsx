import { useQuery } from '@tanstack/react-query'
import { Bot } from 'lucide-react'

import { fetchLLMStatus } from '../../api/system'
import { formatDateTime } from '../../utils/date'
import { queryKeys } from '../../utils/queryKeys'
import { Badge } from '../ui/Badge'
import { ErrorState } from '../ui/ErrorState'
import { Skeleton } from '../ui/Skeleton'
import { StatusCard } from './StatusCard'

const POLL_INTERVAL_MS = 30_000

export function LLMStatusPanel() {
  const query = useQuery({
    queryKey: queryKeys.system.llm,
    queryFn: fetchLLMStatus,
    refetchInterval: POLL_INTERVAL_MS,
    staleTime: 15_000,
  })

  if (query.isLoading) {
    return (
      <StatusCard
        title="LLM / agent runtime"
        statusLabel="Loading…"
        state="loading"
        icon={<Bot className="h-4 w-4" aria-hidden="true" />}
        description="Mock or Qwen agent configuration and availability"
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
          title="LLM / agent runtime"
          statusLabel="Unavailable"
          state="error"
          icon={<Bot className="h-4 w-4" aria-hidden="true" />}
          description="Mock or Qwen agent configuration and availability"
        />
        <ErrorState
          title="LLM status unavailable"
          message="Unable to load agent runtime status."
          onRetry={() => query.refetch()}
        />
      </div>
    )
  }

  const data = query.data

  return (
    <StatusCard
      title="LLM / agent runtime"
      statusLabel={data.available ? `${data.mode} available` : `${data.mode} unavailable`}
      state={data.available ? 'healthy' : 'warning'}
      icon={<Bot className="h-4 w-4" aria-hidden="true" />}
      description="Mock or Qwen agent configuration and availability"
    >
      <div className="flex flex-wrap gap-2">
        <Badge variant={data.mode === 'MOCK' ? 'neutral' : 'info'}>{data.mode} mode</Badge>
        <Badge variant={data.available ? 'success' : 'warning'}>
          {data.available ? 'Available' : 'Unavailable'}
        </Badge>
      </div>

      <dl className="mt-3 grid gap-3 text-sm sm:grid-cols-2">
        <div>
          <dt className="text-xs text-slate-500">Configured model</dt>
          <dd className="font-medium text-slate-900">{data.configured_model}</dd>
        </div>
        <div>
          <dt className="text-xs text-slate-500">Endpoint host</dt>
          <dd className="font-medium text-slate-900">{data.endpoint_host}</dd>
        </div>
        <div>
          <dt className="text-xs text-slate-500">Last checked</dt>
          <dd className="font-medium text-slate-900">
            {formatDateTime(data.last_checked_at)}
          </dd>
        </div>
        {data.crewai_version ? (
          <div>
            <dt className="text-xs text-slate-500">CrewAI version</dt>
            <dd className="font-medium text-slate-900">{data.crewai_version}</dd>
          </div>
        ) : null}
      </dl>

      {data.error_message ? (
        <p className="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
          {data.error_message}
        </p>
      ) : null}
    </StatusCard>
  )
}
