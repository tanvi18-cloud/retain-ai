export type EventType =
  | 'EXTERNAL_HOME_LOAN_INQUIRY'
  | 'EXTERNAL_CARD_INQUIRY'
  | 'SALARY_CREDIT_STOPPED'
  | 'SALARY_CREDIT_RESUMED'
  | 'LARGE_EXTERNAL_TRANSFER'
  | 'FIXED_DEPOSIT_MATURITY'
  | 'FOREX_SPEND_INCREASE'
  | 'DPD_CHANGED'
  | 'PRODUCT_USAGE_DECLINE'
  | 'BALANCE_DECLINE'
  | 'INVESTMENT_TRANSFER_INCREASE'
  | 'MANUAL_REANALYSIS'

export type EventStatus = 'RECEIVED' | 'QUEUED' | 'PROCESSING' | 'COMPLETED' | 'FAILED'

export type EventSeverity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'

export interface IncomingEventCreate {
  customer_id: string
  event_type: EventType
  source_system: string
  payload: EventPayload
  idempotency_key?: string | null
  notifications_enabled?: boolean
}

export interface IncomingEventResponse {
  event_id: string
  customer_id: string
  event_type: EventType
  source_system: string
  status: EventStatus
  execution_id: string | null
  created_at: string
  queued_at: string | null
  processing_started_at: string | null
  processed_at: string | null
  error_message: string | null
  duplicate: boolean
  analysis_summary: Record<string, unknown> | null
}

export interface IncomingEventSummary {
  event_id: string
  customer_id: string
  event_type: string
  source_system: string
  status: EventStatus
  created_at: string
}

export interface IncomingEventDetail {
  event_id: string
  customer_id: string
  event_type: string
  source_system: string
  payload_json: Record<string, unknown>
  idempotency_key: string | null
  execution_id: string | null
  analysis_result_json: Record<string, unknown> | null
  status: EventStatus
  error_message: string | null
  retry_count: number
  notifications_enabled: boolean
  created_at: string
  queued_at: string | null
  processing_started_at: string | null
  processed_at: string | null
}

export interface ExternalHomeLoanInquiryPayload {
  severity: EventSeverity
  amount_band?: string | null
  institution_category?: string | null
  trigger_date?: string | null
}

export interface ExternalCardInquiryPayload {
  severity: EventSeverity
  card_type?: string | null
  trigger_date?: string | null
}

export interface SalaryCreditStoppedPayload {
  effective_month?: string | null
  previous_monthly_salary?: number | null
}

export interface SalaryCreditResumedPayload {
  effective_month?: string | null
}

export interface LargeExternalTransferPayload {
  amount: number
  destination_category?: string | null
  transaction_date?: string | null
}

export interface FixedDepositMaturityPayload {
  account_id?: string | null
  maturity_date: string
  maturity_amount?: number | null
  external_outflow_detected?: boolean | null
}

export interface ForexSpendIncreasePayload {
  forex_spend_30d: number
  percentage_increase?: number | null
  travel_trigger_detected?: boolean | null
}

export interface DpdChangedPayload {
  previous_dpd?: number | null
  new_dpd: number
}

export interface ProductUsageDeclinePayload {
  product_inactivity_days: number
  card_spend_change_pct_30d?: number | null
}

export interface BalanceDeclinePayload {
  balance_change_pct_30d: number
}

export interface InvestmentTransferIncreasePayload {
  external_transfer_amount_30d: number
  destination_category: string
  percentage_increase?: number | null
}

export interface ManualReanalysisPayload {
  reason?: string | null
}

export type EventPayload =
  | ExternalHomeLoanInquiryPayload
  | ExternalCardInquiryPayload
  | SalaryCreditStoppedPayload
  | SalaryCreditResumedPayload
  | LargeExternalTransferPayload
  | FixedDepositMaturityPayload
  | ForexSpendIncreasePayload
  | DpdChangedPayload
  | ProductUsageDeclinePayload
  | BalanceDeclinePayload
  | InvestmentTransferIncreasePayload
  | ManualReanalysisPayload
  | Record<string, unknown>

export interface QueueStatus {
  worker_count: number
  queue_size: number
  processing_count: number
  completed_count_since_startup: number
  failed_count_since_startup: number
  started_at: string
}
