import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip as RechartsTooltip,
  XAxis,
  YAxis,
  ZAxis,
} from 'recharts'

import type { PortfolioCustomerRow } from '../../types/portfolio'
import type { RecommendationDecision } from '../../types/api'
import { formatINR } from '../../utils/currency'
import { decisionLabel } from '../../utils/risk'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/Card'

const DECISION_SHAPES: Record<RecommendationDecision, string> = {
  RETAIN: 'circle',
  REVIEW: 'diamond',
  MONITOR: 'square',
  NO_ACTION: 'triangle',
}

const DECISION_COLORS: Record<RecommendationDecision, string> = {
  RETAIN: '#dc2626',
  REVIEW: '#d97706',
  MONITOR: '#0284c7',
  NO_ACTION: '#64748b',
}

interface MatrixPoint {
  customer_id: string
  full_name: string
  churn_score: number
  value_score: number
  priority_score: number
  decision: RecommendationDecision
  revenue_at_risk: number
}

export interface RiskValueMatrixProps {
  customers: PortfolioCustomerRow[]
}

export function RiskValueMatrix({ customers }: RiskValueMatrixProps) {
  const navigate = useNavigate()

  const points: MatrixPoint[] = useMemo(
    () =>
      customers.map((c) => ({
        customer_id: c.customer_id,
        full_name: c.full_name,
        churn_score: c.churn_score,
        value_score: c.value_score,
        priority_score: c.priority_score,
        decision: c.decision,
        revenue_at_risk: c.revenue_at_risk,
      })),
    [customers],
  )

  const quadrantSummary = useMemo(() => {
    const hvHr = points.filter((p) => p.value_score >= 50 && p.churn_score >= 50).length
    const hvLr = points.filter((p) => p.value_score >= 50 && p.churn_score < 50).length
    const lvHr = points.filter((p) => p.value_score < 50 && p.churn_score >= 50).length
    const lvLr = points.filter((p) => p.value_score < 50 && p.churn_score < 50).length
    return { hvHr, hvLr, lvHr, lvLr }
  }, [points])

  return (
    <Card>
      <CardHeader>
        <CardTitle>Risk–value matrix</CardTitle>
        <CardDescription>
          Each point is a customer. Shape and color indicate retention decision; size reflects
          revenue at risk.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid gap-4 lg:grid-cols-[1fr_220px]">
          <div className="h-80 w-full" aria-label="Risk value scatter chart">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 10, right: 10, bottom: 20, left: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis
                  type="number"
                  dataKey="value_score"
                  name="Customer value"
                  domain={[0, 100]}
                  label={{ value: 'Customer value score', position: 'insideBottom', offset: -5 }}
                />
                <YAxis
                  type="number"
                  dataKey="churn_score"
                  name="Churn risk"
                  domain={[0, 100]}
                  label={{
                    value: 'Churn risk score',
                    angle: -90,
                    position: 'insideLeft',
                  }}
                />
                <ZAxis type="number" dataKey="revenue_at_risk" range={[40, 400]} />
                <RechartsTooltip
                  cursor={{ strokeDasharray: '3 3' }}
                  content={({ active, payload }) => {
                    if (!active || !payload?.[0]) return null
                    const point = payload[0].payload as MatrixPoint
                    return (
                      <div className="rounded-lg border border-slate-200 bg-white p-3 text-xs shadow-lg">
                        <p className="font-semibold">{point.full_name}</p>
                        <p>{point.customer_id}</p>
                        <p>Churn: {point.churn_score}</p>
                        <p>Value: {point.value_score}</p>
                        <p>Priority: {point.priority_score}</p>
                        <p>Decision: {decisionLabel(point.decision)}</p>
                        <p>Revenue at risk: {formatINR(point.revenue_at_risk)}</p>
                      </div>
                    )
                  }}
                />
                {(Object.keys(DECISION_SHAPES) as RecommendationDecision[]).map((decision) => (
                  <Scatter
                    key={decision}
                    name={decisionLabel(decision)}
                    data={points.filter((p) => p.decision === decision)}
                    fill={DECISION_COLORS[decision]}
                    shape={DECISION_SHAPES[decision] as 'circle'}
                    onClick={(data) => {
                      const point = data as unknown as MatrixPoint
                      navigate(`/customers/${point.customer_id}`)
                    }}
                  >
                    {points
                      .filter((p) => p.decision === decision)
                      .map((entry) => (
                        <Cell key={entry.customer_id} fill={DECISION_COLORS[decision]} />
                      ))}
                  </Scatter>
                ))}
              </ScatterChart>
            </ResponsiveContainer>
          </div>

          <div className="space-y-3 text-sm" aria-label="Quadrant summary">
            <p className="font-medium text-slate-700">Quadrant summary</p>
            <ul className="space-y-2 text-slate-600">
              <li>High value / high risk: {quadrantSummary.hvHr}</li>
              <li>High value / low risk: {quadrantSummary.hvLr}</li>
              <li>Low value / high risk: {quadrantSummary.lvHr}</li>
              <li>Low value / low risk: {quadrantSummary.lvLr}</li>
            </ul>
            <ul className="space-y-1 border-t border-slate-100 pt-3 text-xs text-slate-500">
              {(Object.keys(DECISION_COLORS) as RecommendationDecision[]).map((d) => (
                <li key={d} className="flex items-center gap-2">
                  <span
                    className="inline-block h-2.5 w-2.5 rounded-full"
                    style={{ backgroundColor: DECISION_COLORS[d] }}
                    aria-hidden="true"
                  />
                  {decisionLabel(d)}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
