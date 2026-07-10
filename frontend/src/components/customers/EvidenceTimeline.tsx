import type { RuleContribution } from '../../types/analysis'
import type { BureauTrigger } from '../../types/customer'
import type { EvidenceReference } from '../../types/recommendation'
import { formatDateTime } from '../../utils/date'
import { Badge } from '../ui/Badge'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card'

interface TimelineItem {
  id: string
  kind: 'observed' | 'interpretation'
  title: string
  detail: string
  source?: string
  observedValue?: string
  points?: number
  timestamp?: string
  severity?: string
}

function formatObserved(value: unknown): string {
  if (value === null || value === undefined) return '—'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

function fromContributions(contributions: RuleContribution[]): TimelineItem[] {
  return contributions
    .filter((c) => c.triggered)
    .map((c) => ({
      id: c.rule_code,
      kind: 'interpretation' as const,
      title: c.description,
      detail: `Rule ${c.rule_code} added ${c.points} points`,
      source: c.source_system,
      observedValue: formatObserved(c.observed_value),
      points: c.points,
      timestamp: undefined,
    }))
    .sort((a, b) => (b.points ?? 0) - (a.points ?? 0))
}

function fromEvidenceReferences(refs: EvidenceReference[]): TimelineItem[] {
  return refs.map((ref, index) => ({
    id: `${ref.source_system}-${index}`,
    kind: 'observed' as const,
    title: `${ref.source_type}: ${ref.field}`,
    detail: 'Observed fact from source system',
    source: ref.source_system,
    observedValue: formatObserved(ref.observed_value),
    timestamp: ref.timestamp ?? undefined,
  }))
}

function fromBureauTriggers(triggers: BureauTrigger[]): TimelineItem[] {
  return triggers.map((t) => ({
    id: t.bureau_trigger_id,
    kind: 'observed' as const,
    title: `${t.trigger_type} (${t.product_type})`,
    detail: t.institution_category,
    source: t.source,
    observedValue: t.amount_band,
    timestamp: t.trigger_date,
    severity: t.severity,
  }))
}

export interface EvidenceTimelineProps {
  primaryTrigger?: string | null
  contributions?: RuleContribution[]
  evidenceReferences?: EvidenceReference[]
  bureauTriggers?: BureauTrigger[]
}

export function EvidenceTimeline({
  primaryTrigger,
  contributions = [],
  evidenceReferences = [],
  bureauTriggers = [],
}: EvidenceTimelineProps) {
  const items: TimelineItem[] = [
    ...fromBureauTriggers(bureauTriggers),
    ...fromEvidenceReferences(evidenceReferences),
    ...fromContributions(contributions),
  ]

  if (primaryTrigger) {
    items.unshift({
      id: 'primary-trigger',
      kind: 'interpretation',
      title: 'Primary trigger',
      detail: primaryTrigger,
      source: 'Scoring engine',
    })
  }

  if (items.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Evidence timeline</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-slate-500">No evidence available. Run analysis to populate signals.</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Evidence timeline</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {items.map((item) => (
          <div
            key={item.id}
            className="rounded-lg border border-slate-200 p-4"
          >
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant={item.kind === 'observed' ? 'info' : 'warning'}>
                {item.kind === 'observed' ? 'Observed fact' : 'Scoring interpretation'}
              </Badge>
              {item.severity ? <Badge variant="danger">{item.severity}</Badge> : null}
              {item.points != null ? (
                <span className="text-xs text-slate-500">+{item.points} pts</span>
              ) : null}
            </div>
            <p className="mt-2 font-medium text-slate-900">{item.title}</p>
            <p className="text-sm text-slate-600">{item.detail}</p>
            {item.source ? <p className="mt-1 text-xs text-slate-500">Source: {item.source}</p> : null}
            {item.observedValue ? (
              <p className="mt-1 text-xs text-slate-500">Observed: {item.observedValue}</p>
            ) : null}
            {item.timestamp ? (
              <p className="mt-1 text-xs text-slate-400">{formatDateTime(item.timestamp)}</p>
            ) : null}
          </div>
        ))}
      </CardContent>
    </Card>
  )
}
