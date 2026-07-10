import type { CustomerSegment, PreferredChannel } from './api'

export interface CustomerSummary {
  customer_id: string
  full_name: string
  segment: CustomerSegment
  assigned_rm_name: string
  estimated_annual_value: number
  preferred_channel: PreferredChannel
}

export interface CustomerDetail {
  customer_id: string
  full_name: string
  segment: CustomerSegment
  relationship_start_date: string
  assigned_rm_id: string
  assigned_rm_name: string
  assigned_rm_email: string
  communication_consent: boolean
  preferred_channel: PreferredChannel
  estimated_annual_value: number
  created_at: string
  updated_at: string
}

export interface Account {
  account_id: string
  customer_id: string
  account_type: string
  current_balance: number
  average_balance_90d: number
  salary_account: boolean
  status: string
  fixed_deposit_maturity_date: string | null
  created_at: string
  updated_at: string
}

export interface CreditProfile {
  credit_profile_id: string
  customer_id: string
  credit_score: number
  max_dpd_12m: number
  credit_utilization_pct: number
  active_loans: number
  recent_credit_inquiries: number
  default_flag: boolean
  last_updated: string
}

export interface BureauTrigger {
  bureau_trigger_id: string
  customer_id: string
  product_type: string
  trigger_type: string
  institution_category: string
  amount_band: string
  severity: import('./api').Severity
  trigger_date: string
  source: string
  processed: boolean
  created_at: string
}

export interface TransactionFeature {
  transaction_feature_id: string
  customer_id: string
  salary_received_current_month: boolean
  balance_change_pct_30d: number
  monthly_inflow: number
  monthly_outflow: number
  external_transfer_amount_30d: number
  card_spend_change_pct_30d: number
  forex_spend_30d: number
  competitor_transfer_detected: boolean
  product_inactivity_days: number
  last_updated: string
}

export interface Interaction {
  interaction_id: string
  customer_id: string
  recommendation_id: string | null
  rm_id: string
  action_type: string
  notes: string | null
  offer_presented: boolean
  customer_response: string | null
  created_at: string
}

export interface DataFreshnessSource {
  last_updated: string | null
  status: import('./api').FreshnessStatus
}

export interface DataFreshness {
  core_banking: DataFreshnessSource
  credit_history: DataFreshnessSource
  bureau_triggers: DataFreshnessSource
  transaction_history: DataFreshnessSource
}

export interface Customer360 {
  customer: CustomerDetail
  accounts: Account[]
  credit_profile: CreditProfile | null
  bureau_triggers: BureauTrigger[]
  transaction_features: TransactionFeature | null
  recommendations: import('./recommendation').RecommendationSummary[]
  interactions: Interaction[]
  data_freshness: DataFreshness
  data_warnings: string[]
}
