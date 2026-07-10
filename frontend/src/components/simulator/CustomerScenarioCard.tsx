import { AlertTriangle, Info } from 'lucide-react'

import { Badge } from '../ui/Badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/Card'

export type ScenarioCustomerId = 'C001' | 'C004' | 'C008' | 'C010'

interface ScenarioSummary {
  title: string
  headline: string
  signals: string[]
  notes: string[]
  severity: 'high' | 'medium' | 'low' | 'stable'
}

const SCENARIOS: Record<ScenarioCustomerId, ScenarioSummary> = {
  C001: {
    title: 'C001 — Priority home-loan attrition',
    headline: 'External home-loan shopping with balance decline',
    signals: [
      'High-severity external home-loan inquiry',
      'Balance decline over 30 days',
      'High-value priority relationship',
    ],
    notes: [
      'Urgent RM retention review recommended.',
      'Home-loan processing-fee waiver may be discussed as an RM option.',
    ],
    severity: 'high',
  },
  C004: {
    title: 'C004 — Distressed borrower',
    headline: 'Elevated DPD with lending restrictions expected',
    signals: [
      '60 days past due on credit profile',
      'High churn risk indicators',
      'Repayment support is the primary path',
    ],
    notes: [
      'New lending products are policy-restricted for this customer.',
      'Focus on repayment support — do not promise new lending approval.',
    ],
    severity: 'high',
  },
  C008: {
    title: 'C008 — Fixed deposit renewal',
    headline: 'FD maturity opportunity with external outflow risk',
    signals: [
      'Large fixed deposit approaching maturity',
      'Recent external transfer pattern',
      'High customer value depositor',
    ],
    notes: [
      'Proactive pre-maturity call recommended.',
      'FD renewal incentive aligns with retention scenario.',
    ],
    severity: 'medium',
  },
  C010: {
    title: 'C010 — Stable relationship',
    headline: 'No significant risk signals detected',
    signals: [
      'Stable transaction activity',
      'No material bureau triggers',
      'Low priority score supports monitoring',
    ],
    notes: [
      'Routine monitoring is appropriate.',
      'No urgent retention action expected from baseline signals.',
    ],
    severity: 'stable',
  },
}

const SEVERITY_VARIANT = {
  high: 'danger',
  medium: 'warning',
  low: 'info',
  stable: 'success',
} as const

const SEVERITY_LABEL = {
  high: 'High urgency',
  medium: 'Moderate urgency',
  low: 'Low urgency',
  stable: 'Stable',
} as const

export interface CustomerScenarioCardProps {
  customerId: ScenarioCustomerId
}

export function CustomerScenarioCard({ customerId }: CustomerScenarioCardProps) {
  const scenario = SCENARIOS[customerId]

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <CardTitle>{scenario.title}</CardTitle>
            <CardDescription>{scenario.headline}</CardDescription>
          </div>
          <Badge variant={SEVERITY_VARIANT[scenario.severity]}>
            {SEVERITY_LABEL[scenario.severity]}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="rounded-lg bg-amber-50 px-3 py-2 ring-1 ring-amber-200">
          <p className="flex items-center gap-2 text-xs font-medium text-amber-900">
            <Info className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
            Synthetic demonstration scenario — fictional customer data
          </p>
        </div>

        <div>
          <p className="text-sm font-medium text-slate-900">Key signals</p>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-600">
            {scenario.signals.map((signal) => (
              <li key={signal}>{signal}</li>
            ))}
          </ul>
        </div>

        <div>
          <p className="text-sm font-medium text-slate-900">RM guidance</p>
          <ul className="mt-2 space-y-2">
            {scenario.notes.map((note) => (
              <li
                key={note}
                className="flex items-start gap-2 text-sm text-slate-600"
              >
                <AlertTriangle
                  className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-600"
                  aria-hidden="true"
                />
                <span>{note}</span>
              </li>
            ))}
          </ul>
        </div>
      </CardContent>
    </Card>
  )
}

export function isScenarioCustomerId(value: string): value is ScenarioCustomerId {
  return value === 'C001' || value === 'C004' || value === 'C008' || value === 'C010'
}
