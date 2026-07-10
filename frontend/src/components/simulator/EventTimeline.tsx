import { Check, Circle, Loader2, X } from 'lucide-react'

import type { EventStatus, IncomingEventDetail } from '../../types/event'
import { formatDateTime } from '../../utils/date'
import { cn } from '../../utils/cn'
import { Badge } from '../ui/Badge'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card'

const PIPELINE_STEPS: EventStatus[] = [
  'RECEIVED',
  'QUEUED',
  'PROCESSING',
  'COMPLETED',
  'FAILED',
]

const STEP_LABELS: Record<EventStatus, string> = {
  RECEIVED: 'Received',
  QUEUED: 'Queued',
  PROCESSING: 'Processing',
  COMPLETED: 'Completed',
  FAILED: 'Failed',
}

interface TimelineStep {
  status: EventStatus
  timestamp: string | null
  isCurrent: boolean
  isComplete: boolean
  isFailedTerminal: boolean
}

function stepIndex(status: EventStatus): number {
  return PIPELINE_STEPS.indexOf(status)
}

function buildSteps(detail: IncomingEventDetail): TimelineStep[] {
  const currentIndex = stepIndex(detail.status)
  const isFailed = detail.status === 'FAILED'
  const visibleSteps: EventStatus[] = isFailed
    ? ['RECEIVED', 'QUEUED', 'PROCESSING', 'FAILED']
    : ['RECEIVED', 'QUEUED', 'PROCESSING', 'COMPLETED']

  const timestampFor = (status: EventStatus): string | null => {
    switch (status) {
      case 'RECEIVED':
        return detail.created_at
      case 'QUEUED':
        return detail.queued_at
      case 'PROCESSING':
        return detail.processing_started_at
      case 'COMPLETED':
      case 'FAILED':
        return detail.processed_at
      default:
        return null
    }
  }

  return visibleSteps.map((status) => {
    const index = stepIndex(status)
    const isCurrent = detail.status === status
    const isComplete = !isCurrent && index < currentIndex
    return {
      status,
      timestamp: timestampFor(status),
      isCurrent,
      isComplete,
      isFailedTerminal: status === 'FAILED' && isFailed,
    }
  })
}

function extractRecommendationId(
  analysis: Record<string, unknown> | null,
): string | null {
  if (!analysis) return null
  const id = analysis.recommendation_id
  return typeof id === 'string' && id.length > 0 ? id : null
}

export interface EventTimelineProps {
  detail: IncomingEventDetail | null
  liveStatusText?: string
}

export function EventTimeline({ detail, liveStatusText }: EventTimelineProps) {
  if (!detail) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Event status</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-slate-500">
            Submit an event to track processing status.
          </p>
        </CardContent>
      </Card>
    )
  }

  const steps = buildSteps(detail)
  const recommendationId = extractRecommendationId(detail.analysis_result_json)

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <CardTitle>Event status</CardTitle>
          <Badge
            variant={
              detail.status === 'COMPLETED'
                ? 'success'
                : detail.status === 'FAILED'
                  ? 'danger'
                  : 'info'
            }
          >
            {STEP_LABELS[detail.status]}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div
          role="list"
          aria-label="Event processing timeline"
          className="space-y-3"
          aria-live="polite"
        >
          {steps.map((step) => (
            <div
              key={step.status}
              role="listitem"
              aria-current={step.isCurrent ? 'step' : undefined}
              className={cn(
                'flex gap-3 rounded-lg border p-3',
                step.isCurrent && 'border-sky-300 bg-sky-50',
                step.isComplete && 'border-emerald-200 bg-emerald-50/50',
                step.isFailedTerminal && 'border-red-200 bg-red-50',
                !step.isCurrent && !step.isComplete && !step.isFailedTerminal && 'border-slate-200',
              )}
            >
              <span className="mt-0.5 shrink-0" aria-hidden="true">
                {step.isFailedTerminal ? (
                  <X className="h-5 w-5 text-red-600" />
                ) : step.isComplete ? (
                  <Check className="h-5 w-5 text-emerald-600" />
                ) : step.isCurrent ? (
                  <Loader2 className="h-5 w-5 animate-spin text-sky-600" />
                ) : (
                  <Circle className="h-5 w-5 text-slate-300" />
                )}
              </span>
              <div className="min-w-0 flex-1">
                <p className="font-medium text-slate-900">{STEP_LABELS[step.status]}</p>
                <p className="text-xs text-slate-500">
                  {step.timestamp
                    ? formatDateTime(step.timestamp)
                    : step.isCurrent
                      ? 'In progress…'
                      : 'Pending'}
                </p>
                {step.isCurrent && liveStatusText ? (
                  <p className="mt-1 text-xs text-slate-600">{liveStatusText}</p>
                ) : null}
              </div>
            </div>
          ))}
        </div>

        <dl className="grid gap-2 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-xs text-slate-500">Event ID</dt>
            <dd className="font-mono text-xs text-slate-800">{detail.event_id}</dd>
          </div>
          {detail.execution_id ? (
            <div>
              <dt className="text-xs text-slate-500">Execution ID</dt>
              <dd className="font-mono text-xs text-slate-800">{detail.execution_id}</dd>
            </div>
          ) : null}
          {recommendationId ? (
            <div>
              <dt className="text-xs text-slate-500">Recommendation ID</dt>
              <dd className="font-mono text-xs text-slate-800">{recommendationId}</dd>
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
      </CardContent>
    </Card>
  )
}
