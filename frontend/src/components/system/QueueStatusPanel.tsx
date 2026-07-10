import { useQuery } from '@tanstack/react-query'
import { Layers } from 'lucide-react'

import { fetchQueueStatus } from '../../api/system'
import { formatDateTime } from '../../utils/date'
import { queryKeys } from '../../utils/queryKeys'
import { ErrorState } from '../ui/ErrorState'
import { Skeleton } from '../ui/Skeleton'
import { StatusCard } from './StatusCard'

const POLL_INTERVAL_MS = 15_000

export function QueueStatusPanel() {
  const query = useQuery({
    queryKey: queryKeys.system.queue,
    queryFn: fetchQueueStatus,
    refetchInterval: POLL_INTERVAL_MS,
    staleTime: 10_000,
  })

  if (query.isLoading) {
    return (
      <StatusCard
        title="Event queue"
        statusLabel="Loading…"
        state="loading"
        icon={<Layers className="h-4 w-4" aria-hidden="true" />}
        description="Incoming event worker and queue metrics"
      >
        <div className="space-y-2">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
        </div>
      </StatusCard>
    )
  }

  if (query.isError || !query.data) {
    return (
      <div className="space-y-3">
        <StatusCard
          title="Event queue"
          statusLabel="Unavailable"
          state="error"
          icon={<Layers className="h-4 w-4" aria-hidden="true" />}
          description="Incoming event worker and queue metrics"
        />
        <ErrorState
          title="Queue status unavailable"
          message="Unable to load queue metrics."
          onRetry={() => query.refetch()}
        />
      </div>
    )
  }

  const data = query.data
  const hasBacklog = data.queue_size > 0 || data.processing_count > 0

  return (
    <StatusCard
      title="Event queue"
      statusLabel={hasBacklog ? 'Processing backlog' : 'Idle'}
      state={hasBacklog ? 'warning' : 'healthy'}
      icon={<Layers className="h-4 w-4" aria-hidden="true" />}
      description="Incoming event worker and queue metrics"
    >
      <dl className="grid gap-3 text-sm sm:grid-cols-2">
        <div>
          <dt className="text-xs text-slate-500">Workers</dt>
          <dd className="font-semibold text-slate-900">{data.worker_count}</dd>
        </div>
        <div>
          <dt className="text-xs text-slate-500">Queue size</dt>
          <dd className="font-semibold text-slate-900">{data.queue_size}</dd>
        </div>
        <div>
          <dt className="text-xs text-slate-500">Processing</dt>
          <dd className="font-semibold text-slate-900">{data.processing_count}</dd>
        </div>
        <div>
          <dt className="text-xs text-slate-500">Completed (startup)</dt>
          <dd className="font-semibold text-slate-900">
            {data.completed_count_since_startup}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-slate-500">Failed (startup)</dt>
          <dd className="font-semibold text-slate-900">
            {data.failed_count_since_startup}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-slate-500">Started at</dt>
          <dd className="font-semibold text-slate-900">
            {formatDateTime(data.started_at)}
          </dd>
        </div>
      </dl>
    </StatusCard>
  )
}
