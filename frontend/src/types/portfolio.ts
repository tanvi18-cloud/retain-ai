import type { CustomerSegment, RecommendationDecision } from './api'

export interface PortfolioSummary {
  total_customers: number
  immediate_intervention_count: number
  review_count: number
  monitor_count: number
  no_action_count: number
  total_revenue_at_risk: number
  total_positive_expected_net_benefit: number
  open_alerts: number
  unacknowledged_alerts: number
  high_value_high_risk_count: number
  generated_at: string
}

export interface PortfolioCustomerRow {
  customer_id: string
  full_name: string
  segment: CustomerSegment
  relationship_start_date: string
  churn_score: number
  value_score: number
  priority_score: number
  decision: RecommendationDecision
  primary_trigger: string | null
  recommended_action: string
  top_eligible_offer_id: string | null
  top_eligible_offer_name: string | null
  revenue_at_risk: number
  expected_net_benefit: number | null
  recommendation_status: string | null
  has_data_warning: boolean
  last_analyzed_at: string | null
}

export type PortfolioSortField =
  | 'customer_id'
  | 'full_name'
  | 'churn_score'
  | 'value_score'
  | 'priority_score'
  | 'revenue_at_risk'
  | 'expected_net_benefit'

export type SortOrder = 'asc' | 'desc'

export interface PortfolioCustomersParams {
  page?: number
  page_size?: number
  search?: string
  segment?: CustomerSegment
  decision?: RecommendationDecision
  trigger_type?: string
  minimum_priority?: number
  sort_by?: PortfolioSortField
  sort_order?: SortOrder
}
