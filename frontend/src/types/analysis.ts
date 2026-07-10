import type {
  AnalysisExecutionMode,
  AnalysisExecutionStatus,
  CustomerSegment,
  RecommendationDecision,
  ScoreBand,
} from './api'

export interface RuleContribution {
  rule_code: string
  description: string
  points: number
  observed_value: unknown
  source_system: string
  source_reference: string | null
  triggered: boolean
}

export interface ScoreResult {
  score: number
  band: ScoreBand
  contributions: RuleContribution[]
  calculation_version: string
  calculated_at: string
}

export interface PriorityResult {
  churn_score: number
  value_score: number
  churn_weight: number
  value_weight: number
  priority_score: number
  decision: RecommendationDecision
  explanation: string
  calculation_version: string
  calculated_at: string
}

export interface EligibilityReason {
  code: string
  description: string
  observed_value: string | null
}

export interface EligibleOffer {
  offer_id: string
  offer_name: string
  product_type: string
  description: string
  estimated_cost: number
  expected_retention_uplift: number
  eligibility_reasons: EligibilityReason[]
  requires_rm_approval: boolean
}

export interface RejectedOffer {
  offer_id: string
  offer_name: string
  product_type: string
  reason_codes: string[]
  explanations: string[]
}

export interface EligibilityResult {
  customer_id: string
  eligible_offers: EligibleOffer[]
  rejected_offers: RejectedOffer[]
  policy_warnings: string[]
  policy_version: string
  evaluated_at: string
}

export interface RetentionFinancials {
  annual_customer_value: number
  churn_probability: number
  revenue_at_risk: number
  expected_retention_uplift: number
  estimated_offer_cost: number
  expected_gross_retention_value: number
  expected_net_benefit: number
  financially_positive: boolean
  assumptions: string[]
  calculated_at: string
}

export interface OfferFinancialOption {
  offer_id: string
  offer_name: string
  product_type: string
  financials: RetentionFinancials
}

export interface RulesOnlyAnalysisResponse {
  customer_id: string
  customer_name: string
  customer_segment: CustomerSegment
  customer_360_warnings: string[]
  churn_result: ScoreResult
  value_result: ScoreResult
  priority_result: PriorityResult
  eligibility_result: EligibilityResult
  financial_options: OfferFinancialOption[]
  top_risk_signals: string[]
  primary_trigger: string | null
  suggested_action: string
  generated_at: string
  analysis_version: string
}

export interface AnalysisExecutionAcceptedResponse {
  execution_id: string
  customer_id: string
  status: AnalysisExecutionStatus
  queued_at: string
  status_url: string
}

export interface AnalysisExecutionDetail {
  execution_id: string
  customer_id: string
  event_id: string | null
  mode: AnalysisExecutionMode
  status: AnalysisExecutionStatus
  current_step: string | null
  recommendation_id: string | null
  priority_score: number | null
  started_at: string | null
  completed_at: string | null
  error_code: string | null
  safe_error_message: string | null
  validation_warnings: string[]
  status_url: string
  recommendation_url: string | null
  created_at: string
  updated_at: string
}
