import { ExternalLink, RotateCcw } from 'lucide-react'
import { Link } from 'react-router-dom'

import type { IncomingEventDetail } from '../../types/event'
import { formatDateTime } from '../../utils/date'
import { Badge } from '../ui/Badge'
import { Button } from '../ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card'

function extractRecommendationId(
  analysis: Record<string, unknown> | null,
): string | null {
  if (!analysis) return null
  const id = analysis.recommendation_id
  return typeof id === 'string' && id.length > 0 ? id : null
}

function formatSummaryValue(value: unknown): string {
  if (value === null || value === undefined) return '—'
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  if (typeof value === 'number') return String(value)
  if (typeof value === 'string') return value
  return JSON.stringify(value)
}

export interface EventResultCardProps {
  detail: IncomingEventDetail | null
  onRetry?: () => void
  retrying?: boolean
}

export function EventResultCard({ detail, onRetry, retrying }: EventResultCardProps) {
  if (!detail) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Result summary</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-slate-500">
            Results appear here after the event completes processing.
          </p>
        </CardContent>
      </Card>
    )
  }

  if (detail.status !== 'COMPLETED' && detail.status !== 'FAILED') {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Result summary</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-slate-500" aria-live="polite">
            Processing event — results will appear when complete.
          </p>
        </CardContent>
      </Card>
    )
  }

  const recommendationId = extractRecommendationId(detail.analysis_result_json)
  const summaryEntries = detail.analysis_result_json
    ? Object.entries(detail.analysis_result_json).filter(
        ([key]) => key !== 'recommendation_id' && key !== 'execution_id',
      )
    : []

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <CardTitle>Result summary</CardTitle>
          <Badge variant={detail.status === 'COMPLETED' ? 'success' : 'danger'}>
            {detail.status === 'COMPLETED' ? 'Completed' : 'Failed'}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <dl className="grid gap-3 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-xs text-slate-500">Customer</dt>
            <dd className="font-medium text-slate-900">{detail.customer_id}</dd>
          </div>
          <div>
            <dt className="text-xs text-slate-500">Event type</dt>
            <dd className="font-medium text-slate-900">{detail.event_type}</dd>
          </div>
          <div>
            <dt className="text-xs text-slate-500">Processed at</dt>
            <dd className="font-medium text-slate-900">
              {formatDateTime(detail.processed_at)}
            </dd>
          </div>
          {detail.retry_count > 0 ? (
            <div>
              <dt className="text-xs text-slate-500">Retry count</dt>
              <dd className="font-medium text-slate-900">{detail.retry_count}</dd>
            </div>
          ) : null}
        </dl>

        {detail.status === 'FAILED' && detail.error_message ? (
          <div
            role="alert"
            className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800"
          >
            {detail.error_message}
          </div>
        ) : null}

        {summaryEntries.length > 0 ? (
          <div>
            <p className="text-sm font-medium text-slate-900">Analysis snapshot</p>
            <dl className="mt-2 space-y-2">
              {summaryEntries.slice(0, 8).map(([key, value]) => (
                <div
                  key={key}
                  className="rounded-lg border border-slate-200 px-3 py-2"
                >
                  <dt className="text-xs text-slate-500">{key.replace(/_/g, ' ')}</dt>
                  <dd className="text-sm text-slate-800">{formatSummaryValue(value)}</dd>
                </div>
              ))}
            </dl>
          </div>
        ) : null}

        <div className="flex flex-wrap gap-2">
          <Link
            to={`/customers/${detail.customer_id}`}
            className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-800 hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
          >
            <ExternalLink className="h-4 w-4" aria-hidden="true" />
            View customer
          </Link>

          {recommendationId ? (
            <Link
              to={`/customers/${detail.customer_id}`}
              className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-800 hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
            >
              <ExternalLink className="h-4 w-4" aria-hidden="true" />
              View recommendation ({recommendationId})
            </Link>
          ) : null}

          {detail.status === 'FAILED' && onRetry ? (
            <Button
              variant="outline"
              onClick={onRetry}
              loading={retrying}
              className="gap-2"
            >
              <RotateCcw className="h-4 w-4" aria-hidden="true" />
              Retry event
            </Button>
          ) : null}
        </div>

        <p className="text-xs text-slate-500">
          Recommendations and offers are RM discussion options — not product approvals.
        </p>
      </CardContent>
    </Card>
  )
}
