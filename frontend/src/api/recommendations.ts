import { get, post } from './client'
import type { PaginatedResponse, RecommendationDecision, RecommendationStatus } from '../types/api'
import type {
  RecommendationActionRequest,
  RecommendationActionResponse,
  RecommendationCloseRequest,
  RecommendationContactedRequest,
  RecommendationDetail,
  RecommendationRejectRequest,
  RecommendationSummary,
} from '../types/recommendation'

export interface RecommendationsListParams {
  page?: number
  page_size?: number
  customer_id?: string
  status?: RecommendationStatus
  decision?: RecommendationDecision
  minimum_priority?: number
  sort_by?: 'created_at' | 'priority_score'
  sort_order?: 'asc' | 'desc'
}

export function fetchRecommendations(params: RecommendationsListParams = {}) {
  return get<PaginatedResponse<RecommendationSummary>>('/recommendations', { ...params })
}

export function fetchRecommendation(recommendationId: string) {
  return get<RecommendationDetail>(`/recommendations/${recommendationId}`)
}

export function reviewRecommendation(
  recommendationId: string,
  body: RecommendationActionRequest,
) {
  return post<RecommendationActionResponse>(`/recommendations/${recommendationId}/review`, body)
}

export function approveRecommendation(
  recommendationId: string,
  body: RecommendationActionRequest,
) {
  return post<RecommendationActionResponse>(`/recommendations/${recommendationId}/approve`, body)
}

export function rejectRecommendation(
  recommendationId: string,
  body: RecommendationRejectRequest,
) {
  return post<RecommendationActionResponse>(`/recommendations/${recommendationId}/reject`, body)
}

export function contactedRecommendation(
  recommendationId: string,
  body: RecommendationContactedRequest,
) {
  return post<RecommendationActionResponse>(`/recommendations/${recommendationId}/contacted`, body)
}

export function closeRecommendation(
  recommendationId: string,
  body: RecommendationCloseRequest,
) {
  return post<RecommendationActionResponse>(`/recommendations/${recommendationId}/close`, body)
}
