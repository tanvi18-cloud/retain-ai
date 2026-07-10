import { useEffect, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'

import { fetchAnalysisExecution } from '../api/analysis'
import { ApiError } from '../api/client'
import {
  ANALYSIS_POLL_MAX_ATTEMPTS,
  getAnalysisPollIntervalMs,
} from '../config/analysisPolling'
import type { AnalysisExecutionDetail } from '../types/analysis'
import { queryKeys } from '../utils/queryKeys'

interface UseAnalysisExecutionPollingOptions {
  executionId: string | null
  customerId: string
  onStatusChange: (status: string) => void
  onComplete: () => void
  onFailed: (message: string) => void
  onPollError: (message: string) => void
  onTimeout: () => void
}

export function useAnalysisExecutionPolling({
  executionId,
  customerId,
  onStatusChange,
  onComplete,
  onFailed,
  onPollError,
  onTimeout,
}: UseAnalysisExecutionPollingOptions) {
  const queryClient = useQueryClient()
  const pollCountRef = useRef(0)
  const timerRef = useRef<number | null>(null)
  const inFlightRef = useRef(false)
  const activeExecutionIdRef = useRef<string | null>(null)

  const onStatusChangeRef = useRef(onStatusChange)
  const onCompleteRef = useRef(onComplete)
  const onFailedRef = useRef(onFailed)
  const onPollErrorRef = useRef(onPollError)
  const onTimeoutRef = useRef(onTimeout)

  onStatusChangeRef.current = onStatusChange
  onCompleteRef.current = onComplete
  onFailedRef.current = onFailed
  onPollErrorRef.current = onPollError
  onTimeoutRef.current = onTimeout

  useEffect(() => {
    if (!executionId) {
      activeExecutionIdRef.current = null
      return
    }

    activeExecutionIdRef.current = executionId
    pollCountRef.current = 0
    let cancelled = false

    const clearScheduledPoll = () => {
      if (timerRef.current !== null) {
        window.clearTimeout(timerRef.current)
        timerRef.current = null
      }
    }

    const schedulePoll = (delayMs: number) => {
      clearScheduledPoll()
      timerRef.current = window.setTimeout(() => {
        void runPoll()
      }, delayMs)
    }

    const refreshQueries = async (detail: AnalysisExecutionDetail) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.customers.customer360(customerId) }),
        queryClient.invalidateQueries({
          queryKey: queryKeys.recommendations.list({ customer_id: customerId }),
        }),
      ])
      if (detail.recommendation_id) {
        await queryClient.invalidateQueries({
          queryKey: queryKeys.recommendations.detail(detail.recommendation_id),
        })
      }
    }

    const runPoll = async () => {
      if (cancelled || inFlightRef.current || activeExecutionIdRef.current !== executionId) {
        return
      }

      inFlightRef.current = true

      try {
        const detail = await fetchAnalysisExecution(executionId)

        if (cancelled || activeExecutionIdRef.current !== executionId) {
          return
        }

        onStatusChangeRef.current(detail.status)

        if (detail.status === 'COMPLETED') {
          clearScheduledPoll()
          await refreshQueries(detail)
          onCompleteRef.current()
          return
        }

        if (detail.status === 'FAILED') {
          clearScheduledPoll()
          onFailedRef.current(detail.safe_error_message ?? 'Analysis failed')
          return
        }

        pollCountRef.current += 1
        if (pollCountRef.current >= ANALYSIS_POLL_MAX_ATTEMPTS) {
          clearScheduledPoll()
          onTimeoutRef.current()
          return
        }

        schedulePoll(getAnalysisPollIntervalMs())
      } catch (error) {
        if (cancelled) return
        clearScheduledPoll()
        const message = error instanceof ApiError ? error.message : 'Polling failed'
        onPollErrorRef.current(message)
      } finally {
        inFlightRef.current = false
      }
    }

    schedulePoll(getAnalysisPollIntervalMs())

    return () => {
      cancelled = true
      clearScheduledPoll()
      if (activeExecutionIdRef.current === executionId) {
        activeExecutionIdRef.current = null
      }
    }
  }, [customerId, executionId, queryClient])
}
