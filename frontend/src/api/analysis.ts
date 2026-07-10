import { get, post } from './client'
import type {
  AnalysisExecutionAcceptedResponse,
  AnalysisExecutionDetail,
  RulesOnlyAnalysisResponse,
} from '../types/analysis'

export function runRulesOnlyAnalysis(customerId: string) {
  return post<RulesOnlyAnalysisResponse>(`/analysis/${customerId}/rules-only`)
}

export interface FullAnalysisRequest {
  notifications_enabled?: boolean
  force_reanalysis?: boolean
  reason?: string | null
  idempotency_key?: string | null
}

export function runFullAnalysis(customerId: string, body: FullAnalysisRequest = {}) {
  return post<AnalysisExecutionAcceptedResponse>(`/analysis/${customerId}`, body)
}

export function fetchAnalysisExecution(executionId: string) {
  return get<AnalysisExecutionDetail>(`/analysis/executions/${executionId}`)
}
