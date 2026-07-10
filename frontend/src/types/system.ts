import type { LLMMode } from './chat'
import type { HealthResponse } from './api'

export type HealthStatus = HealthResponse

export interface LLMStatus {
  mode: LLMMode
  configured_model: string
  endpoint_host: string
  available: boolean
  last_checked_at: string
  error_message: string | null
  crewai_version: string | null
}

export interface NotificationSystemStatus {
  email_notifications_enabled: boolean
  smtp_host: string
  smtp_port: number
  smtp_configured: boolean
  websocket_connections: number
  alert_priority_threshold: number
}

export interface QueueSystemStatus {
  worker_count: number
  queue_size: number
  processing_count: number
  completed_count_since_startup: number
  failed_count_since_startup: number
  started_at: string
}
