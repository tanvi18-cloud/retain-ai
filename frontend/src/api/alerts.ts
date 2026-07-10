import { get, patch } from './client'
import type { PaginatedResponse } from '../types/api'
import type {
  AlertAcknowledgementRequest,
  AlertDetail,
  AlertSummary,
} from '../types/alert'
import type { AlertType, Severity } from '../types/api'

export interface AlertsListParams {
  page?: number
  page_size?: number
  customer_id?: string
  severity?: Severity
  acknowledged?: boolean
  alert_type?: AlertType
  sort_order?: 'asc' | 'desc'
}

export function fetchAlerts(params: AlertsListParams = {}) {
  return get<PaginatedResponse<AlertSummary>>('/alerts', { ...params })
}

export function fetchAlert(alertId: string) {
  return get<AlertDetail>(`/alerts/${alertId}`)
}

export function acknowledgeAlert(alertId: string, body: AlertAcknowledgementRequest) {
  return patch<AlertDetail>(`/alerts/${alertId}/acknowledge`, body)
}
