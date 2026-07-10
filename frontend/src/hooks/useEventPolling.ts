import { useEffect, useRef } from 'react'

import { getEvent } from '../api/events'
import { ApiError } from '../api/client'
import type { EventStatus, IncomingEventDetail } from '../types/event'

const PRODUCTION_POLL_MS = 2000
const TEST_POLL_MS = 10
const MAX_POLLS = 60

function getPollIntervalMs(): number {
  return import.meta.env.MODE === 'test' ? TEST_POLL_MS : PRODUCTION_POLL_MS
}

interface UseEventPollingOptions {
  eventId: string | null
  onUpdate: (detail: IncomingEventDetail) => void
  onComplete: (detail: IncomingEventDetail) => void
  onFailed: (detail: IncomingEventDetail) => void
  onError: (message: string) => void
  onTimeout: () => void
}

export function useEventPolling({
  eventId,
  onUpdate,
  onComplete,
  onFailed,
  onError,
  onTimeout,
}: UseEventPollingOptions) {
  const pollCountRef = useRef(0)
  const timerRef = useRef<number | null>(null)
  const inFlightRef = useRef(false)

  const callbacksRef = useRef({ onUpdate, onComplete, onFailed, onError, onTimeout })
  callbacksRef.current = { onUpdate, onComplete, onFailed, onError, onTimeout }

  useEffect(() => {
    if (!eventId) return

    pollCountRef.current = 0
    let cancelled = false

    const clearTimer = () => {
      if (timerRef.current !== null) {
        window.clearTimeout(timerRef.current)
        timerRef.current = null
      }
    }

    const schedule = (delay: number) => {
      clearTimer()
      timerRef.current = window.setTimeout(() => void poll(), delay)
    }

    const poll = async () => {
      if (cancelled || inFlightRef.current) return
      inFlightRef.current = true
      try {
        const detail = await getEvent(eventId)
        if (cancelled) return
        callbacksRef.current.onUpdate(detail)

        if (detail.status === 'COMPLETED') {
          clearTimer()
          callbacksRef.current.onComplete(detail)
          return
        }
        if (detail.status === 'FAILED') {
          clearTimer()
          callbacksRef.current.onFailed(detail)
          return
        }

        pollCountRef.current += 1
        if (pollCountRef.current >= MAX_POLLS) {
          clearTimer()
          callbacksRef.current.onTimeout()
          return
        }
        schedule(getPollIntervalMs())
      } catch (error) {
        if (cancelled) return
        clearTimer()
        const message = error instanceof ApiError ? error.message : 'Event polling failed'
        callbacksRef.current.onError(message)
      } finally {
        inFlightRef.current = false
      }
    }

    schedule(getPollIntervalMs())
    return () => {
      cancelled = true
      clearTimer()
    }
  }, [eventId])
}

export function isTerminalEventStatus(status: EventStatus): boolean {
  return status === 'COMPLETED' || status === 'FAILED'
}
