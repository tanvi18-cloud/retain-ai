import { get, post } from './client'
import type { PaginatedResponse } from '../types/api'
import type {
  EventStatus,
  EventType,
  IncomingEventCreate,
  IncomingEventDetail,
  IncomingEventResponse,
  IncomingEventSummary,
} from '../types/event'

export function createEvent(body: IncomingEventCreate) {
  return post<IncomingEventResponse>('/events', body)
}

export interface EventsListParams {
  page?: number
  page_size?: number
  customer_id?: string
  event_type?: EventType
  status?: EventStatus
  source_system?: string
  sort_order?: 'asc' | 'desc'
}

export function listEvents(params: EventsListParams = {}) {
  return get<PaginatedResponse<IncomingEventSummary>>('/events', { ...params })
}

export function getEvent(eventId: string) {
  return get<IncomingEventDetail>(`/events/${eventId}`)
}

export function retryEvent(eventId: string) {
  return post<IncomingEventResponse>(`/events/${eventId}/retry`)
}
