import type { RecommendationDetail } from '../../types/recommendation'
import { formatINR } from '../../utils/currency'
import { formatDateTime, formatPercentage } from '../../utils/date'
import {
  decisionLabel,
  decisionVariant,
  recommendationStatusLabel,
  recommendationStatusVariant,
} from '../../utils/risk'
import { Badge } from '../ui/Badge'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card'
import { EmptyState } from '../ui/EmptyState'

function getTalkingPoints(detail: RecommendationDetail): string[] {
  const brief = detail.rm_brief_json
  const points = brief.talking_points
  if (Array.isArray(points)) {
    return points.filter((p): p is string => typeof p === 'string')
  }
  return []
}

function getEvidenceReferences(detail: RecommendationDetail): string[] {
  const refs = detail.evidence_json.evidence_references
  if (!Array.isArray(refs)) return []
  return refs.map((ref) => {
    if (typeof ref === 'object' && ref !== null && 'field' in ref) {
      const item = ref as { field: string; observed_value?: unknown }
      return `${item.field}: ${String(item.observed_value ?? '—')}`
    }
    return String(ref)
  })
}

export interface RecommendationPanelProps {
  recommendation: RecommendationDetail | null
  onRunFullAnalysis?: () => void
  loading?: boolean
}

export function RecommendationPanel({
  recommendation,
  onRunFullAnalysis,
  loading,
}: RecommendationPanelProps) {
  if (!recommendation) {
    if (loading) {
      return (
        <Card>
          <CardHeader>
            <CardTitle>Latest recommendation</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-slate-500">Loading recommendation…</p>
          </CardContent>
        </Card>
      )
    }

    return (
      <EmptyState
        title="No recommendation yet"
        description="Run a full agentic analysis to generate a persisted retention recommendation for this customer."
        action={
          onRunFullAnalysis
            ? { label: 'Generate recommendation', onClick: onRunFullAnalysis }
            : undefined
        }
      />
    )
  }

  const talkingPoints = getTalkingPoints(recommendation)
  const evidenceRefs = getEvidenceReferences(recommendation)

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-center gap-2">
          <CardTitle>Latest recommendation</CardTitle>
          <Badge variant={decisionVariant(recommendation.decision)}>
            {decisionLabel(recommendation.decision)}
          </Badge>
          <Badge variant={recommendationStatusVariant(recommendation.status)}>
            {recommendationStatusLabel(recommendation.status)}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <section>
          <h4 className="text-sm font-semibold text-slate-700">Executive summary</h4>
          <p className="mt-1 text-sm text-slate-600">{recommendation.summary}</p>
        </section>

        {recommendation.investigation_summary ? (
          <section>
            <h4 className="text-sm font-semibold text-slate-700">Investigation summary</h4>
            <p className="mt-1 text-sm text-slate-600">{recommendation.investigation_summary}</p>
          </section>
        ) : null}

        <dl className="grid gap-3 sm:grid-cols-2 text-sm">
          <div>
            <dt className="text-slate-500">Recommended offer</dt>
            <dd className="font-medium">{recommendation.recommended_offer_id ?? '—'}</dd>
          </div>
          <div>
            <dt className="text-slate-500">Alternate offer</dt>
            <dd className="font-medium">{recommendation.alternate_offer_id ?? '—'}</dd>
          </div>
          <div>
            <dt className="text-slate-500">Expected net benefit</dt>
            <dd className="font-medium">{formatINR(recommendation.expected_net_benefit)}</dd>
          </div>
          <div>
            <dt className="text-slate-500">Revenue at risk</dt>
            <dd className="font-medium">{formatINR(recommendation.revenue_at_risk)}</dd>
          </div>
          <div>
            <dt className="text-slate-500">Confidence</dt>
            <dd className="font-medium">{formatPercentage(recommendation.confidence * 100, 0)}</dd>
          </div>
          <div>
            <dt className="text-slate-500">Created by</dt>
            <dd className="font-medium">{recommendation.created_by_mode}</dd>
          </div>
          <div>
            <dt className="text-slate-500">Created</dt>
            <dd className="font-medium">{formatDateTime(recommendation.created_at)}</dd>
          </div>
        </dl>

        {recommendation.policy_warnings_json.length > 0 ? (
          <section>
            <h4 className="text-sm font-semibold text-amber-800">Policy warnings</h4>
            <ul className="mt-1 list-disc pl-5 text-sm text-amber-900">
              {recommendation.policy_warnings_json.map((w) => (
                <li key={w}>{w}</li>
              ))}
            </ul>
          </section>
        ) : null}

        {recommendation.validation_warnings_json.length > 0 ? (
          <section>
            <h4 className="text-sm font-semibold text-slate-700">Validation warnings</h4>
            <ul className="mt-1 list-disc pl-5 text-sm text-slate-600">
              {recommendation.validation_warnings_json.map((w) => (
                <li key={w}>{w}</li>
              ))}
            </ul>
          </section>
        ) : null}

        {evidenceRefs.length > 0 ? (
          <section>
            <h4 className="text-sm font-semibold text-slate-700">Evidence references</h4>
            <ul className="mt-1 list-disc pl-5 text-sm text-slate-600">
              {evidenceRefs.map((ref) => (
                <li key={ref}>{ref}</li>
              ))}
            </ul>
          </section>
        ) : null}

        {talkingPoints.length > 0 ? (
          <section>
            <h4 className="text-sm font-semibold text-slate-700">RM talking points</h4>
            <ul className="mt-1 list-disc pl-5 text-sm text-slate-600">
              {talkingPoints.map((point) => (
                <li key={point}>{point}</li>
              ))}
            </ul>
          </section>
        ) : null}

        <p className="text-xs text-slate-500">{recommendation.eligibility_disclaimer}</p>
        {loading ? <p className="text-sm text-slate-500">Refreshing…</p> : null}
      </CardContent>
    </Card>
  )
}
