import { useCallback, useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { createEvent, retryEvent } from '../api/events'
import {
  CustomerScenarioCard,
  isScenarioCustomerId,
} from '../components/simulator/CustomerScenarioCard'
import { EventForm } from '../components/simulator/EventForm'
import { EventResultCard } from '../components/simulator/EventResultCard'
import { EventTimeline } from '../components/simulator/EventTimeline'
import { PageHeader } from '../components/layout/PageHeader'
import { getEnv } from '../api/env'
import { useEventPolling } from '../hooks/useEventPolling'
import { useDocumentTitle } from '../hooks/useDocumentTitle'
import type { IncomingEventDetail, IncomingEventResponse } from '../types/event'
import { queryKeys } from '../utils/queryKeys'

export function SimulatorPage() {
  useDocumentTitle('Event Simulator')

  if (!getEnv().enableSimulator) {
    return (
      <p className="text-sm text-slate-500">Event simulator is disabled in this environment.</p>
    )
  }

  return <SimulatorContent />
}

function SimulatorContent() {
  const queryClient = useQueryClient()
  const [customerId, setCustomerId] = useState('C001')
  const [activeEventId, setActiveEventId] = useState<string | null>(null)
  const [eventDetail, setEventDetail] = useState<IncomingEventDetail | null>(null)
  const [lastResponse, setLastResponse] = useState<IncomingEventResponse | null>(null)

  const submitMutation = useMutation({
    mutationFn: createEvent,
    onSuccess: (response) => {
      setLastResponse(response)
      setActiveEventId(response.event_id)
      toast.success('Event queued for processing')
    },
    onError: () => toast.error('Unable to submit event'),
  })

  const retryMutation = useMutation({
    mutationFn: retryEvent,
    onSuccess: (response) => {
      setLastResponse(response)
      setActiveEventId(response.event_id)
      toast.message('Event retry queued')
    },
    onError: () => toast.error('Unable to retry event'),
  })

  const refreshCaches = useCallback(() => {
    void queryClient.invalidateQueries({ queryKey: queryKeys.portfolio.summary })
    void queryClient.invalidateQueries({ queryKey: ['alerts'] })
    void queryClient.invalidateQueries({ queryKey: queryKeys.customers.customer360(customerId) })
  }, [customerId, queryClient])

  useEventPolling({
    eventId: activeEventId,
    onUpdate: setEventDetail,
    onComplete: (detail) => {
      setEventDetail(detail)
      toast.success('Event processing completed')
      setActiveEventId(null)
      refreshCaches()
    },
    onFailed: (detail) => {
      setEventDetail(detail)
      toast.error(detail.error_message ?? 'Event processing failed')
      setActiveEventId(null)
    },
    onError: (message) => {
      toast.error(message)
      setActiveEventId(null)
    },
    onTimeout: () => {
      toast.error('Event status polling timed out')
      setActiveEventId(null)
    },
  })

  return (
    <div className="space-y-6">
      <PageHeader
        title="Event Simulator"
        description="Synthetic demonstration tool. Events update fictional customer data."
      />

      <div
        role="note"
        className="rounded-lg bg-amber-50 px-4 py-3 text-sm text-amber-900 ring-1 ring-amber-200"
      >
        Synthetic demonstration tool. Events update fictional customer data.
      </div>

      <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
        <div className="space-y-4">
          <label className="block text-sm font-medium text-slate-700" htmlFor="sim-customer">
            Customer
          </label>
          <select
            id="sim-customer"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            value={customerId}
            onChange={(e) => setCustomerId(e.target.value)}
          >
            {Array.from({ length: 10 }, (_, i) => {
              const id = `C${String(i + 1).padStart(3, '0')}`
              return (
                <option key={id} value={id}>
                  {id}
                </option>
              )
            })}
          </select>
          {isScenarioCustomerId(customerId) ? (
            <CustomerScenarioCard customerId={customerId} />
          ) : (
            <p className="text-sm text-slate-500">
              Select C001, C004, C008, or C010 for a synthetic scenario summary.
            </p>
          )}
        </div>

        <div className="space-y-6">
          <EventForm
            customerId={customerId}
            loading={submitMutation.isPending}
            onSubmit={(body) => submitMutation.mutate(body)}
          />
          {eventDetail ? (
            <>
              <EventTimeline detail={eventDetail} />
              <EventResultCard
                detail={eventDetail}
                onRetry={
                  eventDetail.status === 'FAILED'
                    ? () => retryMutation.mutate(eventDetail.event_id)
                    : undefined
                }
                retrying={retryMutation.isPending}
              />
            </>
          ) : lastResponse ? (
            <p className="text-sm text-slate-500" aria-live="polite">
              Event {lastResponse.event_id} submitted — polling for status…
            </p>
          ) : null}
        </div>
      </div>
    </div>
  )
}
