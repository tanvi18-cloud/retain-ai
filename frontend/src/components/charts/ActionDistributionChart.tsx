import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import type { PortfolioSummary } from '../../types/portfolio'
import { decisionLabel } from '../../utils/risk'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/Card'

export interface ActionDistributionChartProps {
  summary: PortfolioSummary
}

export function ActionDistributionChart({ summary }: ActionDistributionChartProps) {
  const data = [
    { decision: 'RETAIN', label: decisionLabel('RETAIN'), count: summary.immediate_intervention_count },
    { decision: 'REVIEW', label: decisionLabel('REVIEW'), count: summary.review_count },
    { decision: 'MONITOR', label: decisionLabel('MONITOR'), count: summary.monitor_count },
    { decision: 'NO_ACTION', label: decisionLabel('NO_ACTION'), count: summary.no_action_count },
  ]

  const total = data.reduce((sum, item) => sum + item.count, 0)

  return (
    <Card>
      <CardHeader>
        <CardTitle>Action distribution</CardTitle>
        <CardDescription>Retention decisions across the portfolio.</CardDescription>
      </CardHeader>
      <CardContent>
        <p className="mb-3 text-sm text-slate-600" aria-label="Action distribution summary">
          {total} customers: {data.map((d) => `${d.label} ${d.count}`).join(', ')}
        </p>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="label" tick={{ fontSize: 12 }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="count" fill="#334155" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}
