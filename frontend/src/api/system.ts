import { get } from './client'
import type { HealthResponse } from '../types/api'
import type {
  LLMStatus,
  NotificationSystemStatus,
  QueueSystemStatus,
} from '../types/system'

export function fetchHealth() {
  return get<HealthResponse>('/health')
}

export function fetchLLMStatus() {
  return get<LLMStatus>('/system/llm-status')
}

export function fetchQueueStatus() {
  return get<QueueSystemStatus>('/system/queue-status')
}

export function fetchNotificationStatus() {
  return get<NotificationSystemStatus>('/system/notification-status')
}
