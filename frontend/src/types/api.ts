export type CustomerSegment = 'STANDARD' | 'MASS_AFFLUENT' | 'PRIORITY' | 'PRIVATE'

export type PreferredChannel = 'EMAIL' | 'PHONE' | 'SMS'

export type Severity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'

export type RecommendationDecision = 'RETAIN' | 'REVIEW' | 'MONITOR' | 'NO_ACTION'

export type RecommendationStatus =
  | 'NEW'
  | 'REVIEWED'
  | 'APPROVED'
  | 'REJECTED'
  | 'CONTACTED'
  | 'CLOSED'

export type FreshnessStatus = 'FRESH' | 'STALE' | 'MISSING'

export type ScoreBand = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'

export type AnalysisExecutionMode = 'RULES_ONLY' | 'AGENTIC'

export type AnalysisExecutionStatus = 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED'

export type CreatedByMode = 'MOCK' | 'QWEN' | 'RULES_ONLY'

export type AlertType = 'RULES_PREVIEW' | 'AGENT_RECOMMENDATION' | 'SYSTEM'

export type NotificationStatus =
  | 'PENDING'
  | 'SENT'
  | 'PARTIAL'
  | 'FAILED'
  | 'NOT_REQUIRED'

export interface ApiErrorPayload {
  code: string
  message: string
  details: Record<string, unknown>
}

export interface ApiErrorResponse {
  error: ApiErrorPayload
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface HealthResponse {
  status: string
  service: string
  environment: string
  version: string
}

export interface AlertSummary {
  alert_id: string
  customer_id: string
  event_id: string | null
  recommendation_id: string | null
  alert_type: AlertType
  severity: Severity
  title: string
  priority_score: number | null
  acknowledged: boolean
  notification_status: NotificationStatus
  created_at: string
}
