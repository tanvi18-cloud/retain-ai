import type {
  CreatedByMode,
  RecommendationDecision,
  RecommendationStatus,
} from './api'

export interface RecommendationSummary {
  recommendation_id: string
  customer_id: string
  churn_score: number
  value_score: number
  priority_score: number
  decision: RecommendationDecision
  status: RecommendationStatus
  recommended_offer_id: string | null
}

export interface EvidenceReference {
  source_system: string
  source_type: string
  reference_id: string | null
  field: string
  observed_value: unknown
  timestamp: string | null
}

export interface RecommendationDetail {
  recommendation_id: string
  customer_id: string
  triggering_event_id: string | null
  analysis_execution_id: string | null
  churn_score: number
  value_score: number
  priority_score: number
  decision: RecommendationDecision
  recommended_offer_id: string | null
  alternate_offer_id: string | null
  revenue_at_risk: number
  expected_net_benefit: number
  confidence: number
  summary: string
  investigation_summary: string | null
  evidence_json: Record<string, unknown>
  rm_brief_json: Record<string, unknown>
  policy_warnings_json: string[]
  validation_warnings_json: string[]
  created_by_mode: CreatedByMode
  calculation_version: string | null
  policy_version: string | null
  eligibility_disclaimer: string
  status: RecommendationStatus
  created_at: string
  updated_at: string
  interactions: import('./customer').Interaction[]
}

export interface RecommendationActionResponse {
  recommendation_id: string
  status: string
  interaction_id: string
  message: string
}

export interface RecommendationActionRequest {
  rm_id: string
  notes?: string | null
  idempotency_key?: string | null
}

export interface RecommendationRejectRequest extends RecommendationActionRequest {
  rejection_reason: string
}

export interface RecommendationContactedRequest extends RecommendationActionRequest {
  offer_presented?: boolean
  customer_response?: string | null
  contact_channel?: string | null
  follow_up_date?: string | null
}

export interface RecommendationCloseRequest extends RecommendationActionRequest {
  closing_note: string
}
