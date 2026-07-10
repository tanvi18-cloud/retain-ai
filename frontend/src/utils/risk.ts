import type {
  RecommendationDecision,
  RecommendationStatus,
  ScoreBand,
} from '../types/api'

export type BadgeVariant = 'neutral' | 'success' | 'warning' | 'danger' | 'info'

export function scoreBandLabel(band: ScoreBand): string {
  const labels: Record<ScoreBand, string> = {
    LOW: 'Low',
    MEDIUM: 'Medium',
    HIGH: 'High',
    CRITICAL: 'Critical',
  }
  return labels[band]
}

export function scoreBandVariant(band: ScoreBand): BadgeVariant {
  const variants: Record<ScoreBand, BadgeVariant> = {
    LOW: 'success',
    MEDIUM: 'info',
    HIGH: 'warning',
    CRITICAL: 'danger',
  }
  return variants[band]
}

export function riskLabelFromScore(score: number): string {
  if (score >= 75) return 'Critical risk'
  if (score >= 50) return 'High risk'
  if (score >= 25) return 'Medium risk'
  return 'Low risk'
}

export function valueLabelFromScore(score: number): string {
  if (score >= 75) return 'High value'
  if (score >= 50) return 'Above average'
  if (score >= 25) return 'Moderate value'
  return 'Lower value'
}

export function decisionLabel(decision: RecommendationDecision): string {
  const labels: Record<RecommendationDecision, string> = {
    RETAIN: 'Retain',
    REVIEW: 'RM review',
    MONITOR: 'Monitor',
    NO_ACTION: 'No action',
  }
  return labels[decision]
}

export function decisionVariant(decision: RecommendationDecision): BadgeVariant {
  const variants: Record<RecommendationDecision, BadgeVariant> = {
    RETAIN: 'danger',
    REVIEW: 'warning',
    MONITOR: 'info',
    NO_ACTION: 'neutral',
  }
  return variants[decision]
}

export function recommendationStatusLabel(status: RecommendationStatus): string {
  const labels: Record<RecommendationStatus, string> = {
    NEW: 'New',
    REVIEWED: 'Reviewed',
    APPROVED: 'Approved for discussion',
    REJECTED: 'Rejected',
    CONTACTED: 'Contacted',
    CLOSED: 'Closed',
  }
  return labels[status]
}

export function recommendationStatusVariant(
  status: RecommendationStatus,
): BadgeVariant {
  const variants: Record<RecommendationStatus, BadgeVariant> = {
    NEW: 'info',
    REVIEWED: 'neutral',
    APPROVED: 'success',
    REJECTED: 'danger',
    CONTACTED: 'warning',
    CLOSED: 'neutral',
  }
  return variants[status]
}

export function segmentLabel(segment: string): string {
  return segment.replace(/_/g, ' ')
}
