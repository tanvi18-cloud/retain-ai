import type { AlertType, NotificationStatus, Severity } from './api'

export type AlertSeverity = Severity

export interface AlertSummary {
  alert_id: string
  customer_id: string
  event_id: string | null
  recommendation_id: string | null
  alert_type: AlertType
  severity: AlertSeverity
  title: string
  priority_score: number | null
  acknowledged: boolean
  notification_status: NotificationStatus
  created_at: string
}

export interface AlertDetail extends AlertSummary {
  message: string
  assigned_rm_id: string
  assigned_rm_email: string | null
  recommended_action: string | null
  recommended_offer_id: string | null
  acknowledged_at: string | null
  acknowledged_by: string | null
}

export interface AlertAcknowledgementRequest {
  rm_id: string
  note?: string | null
}

export interface WebSocketConnectedMessage {
  type: 'CONNECTED'
  message: string
  timestamp: string
}

export interface WebSocketPongMessage {
  type: 'PONG'
  timestamp: string
}

export interface WebSocketPingMessage {
  type: 'PING'
}

export interface RetentionAlertMessage {
  type: 'RETENTION_ALERT'
  alert_type: AlertType | null
  alert_id: string
  event_id: string | null
  recommendation_id: string | null
  customer_id: string
  severity: AlertSeverity
  title: string
  priority_score: number
  recommended_action: string
  recommended_offer: string | null
  expected_net_benefit: number | null
  created_at: string
}

export type WebSocketInboundMessage =
  | WebSocketConnectedMessage
  | WebSocketPongMessage
  | RetentionAlertMessage

export type WebSocketConnectionState =
  | 'CONNECTING'
  | 'CONNECTED'
  | 'RECONNECTING'
  | 'DISCONNECTED'
  | 'ERROR'
