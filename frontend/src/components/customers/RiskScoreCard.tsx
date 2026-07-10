import type { ScoreBand } from '../../types/api'
import { formatINR } from '../../utils/currency'
import { scoreBandLabel, scoreBandVariant } from '../../utils/risk'
import { Badge } from '../ui/Badge'
import { Card, CardContent } from '../ui/Card'
import { BANKING_TOOLTIPS, Tooltip } from '../ui/Tooltip'

export interface RiskScoreCardProps {
  label: string
  score: number
  band?: ScoreBand
  explanation: string
  tooltip?: string
}

export function RiskScoreCard({ label, score, band, explanation, tooltip }: RiskScoreCardProps) {
  const content = (
    <Card className="h-full">
      <CardContent className="space-y-2">
        <p className="text-sm font-medium text-slate-500">{label}</p>
        <div className="flex items-baseline gap-2">
          <p className="text-3xl font-semibold text-slate-900">{score}</p>
          {band ? <Badge variant={scoreBandVariant(band)}>{scoreBandLabel(band)}</Badge> : null}
        </div>
        <p className="text-xs text-slate-500">{explanation}</p>
      </CardContent>
    </Card>
  )

  if (tooltip) return <Tooltip content={tooltip}>{content}</Tooltip>
  return content
}

export function RiskScoreGrid({
  churnScore,
  churnBand,
  valueScore,
  valueBand,
  priorityScore,
  decision,
  revenueAtRisk,
  expectedNetBenefit,
  topOffer,
}: {
  churnScore: number
  churnBand?: ScoreBand
  valueScore: number
  valueBand?: ScoreBand
  priorityScore: number
  decision: string
  revenueAtRisk: number
  expectedNetBenefit: number | null
  topOffer: string | null
}) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <RiskScoreCard
        label="Churn score"
        score={churnScore}
        band={churnBand}
        explanation="Backend-computed churn risk."
        tooltip={BANKING_TOOLTIPS.churnScore}
      />
      <RiskScoreCard
        label="Customer value"
        score={valueScore}
        band={valueBand}
        explanation="Backend-computed relationship value."
        tooltip={BANKING_TOOLTIPS.customerValue}
      />
      <RiskScoreCard
        label="Priority score"
        score={priorityScore}
        explanation={`Decision: ${decision}`}
        tooltip={BANKING_TOOLTIPS.priorityScore}
      />
      <Card>
        <CardContent className="space-y-2">
          <p className="text-sm font-medium text-slate-500">Financial impact</p>
          <p className="text-sm">
            Revenue at risk: <strong>{formatINR(revenueAtRisk)}</strong>
          </p>
          <p className="text-sm">
            Expected net benefit:{' '}
            <strong>{expectedNetBenefit != null ? formatINR(expectedNetBenefit) : '—'}</strong>
          </p>
          <p className="text-xs text-slate-500">Top offer: {topOffer ?? 'None eligible'}</p>
        </CardContent>
      </Card>
    </div>
  )
}
