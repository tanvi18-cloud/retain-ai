import type { DataFreshness } from '../../types/customer'
import type { FreshnessStatus } from '../../types/api'
import { formatDateTime } from '../../utils/date'
import { Badge } from '../ui/Badge'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card'

const SOURCE_LABELS: Record<keyof DataFreshness, string> = {
  core_banking: 'Core banking',
  credit_history: 'Credit history',
  bureau_triggers: 'Bureau triggers',
  transaction_history: 'Transaction history',
}

function freshnessVariant(status: FreshnessStatus) {
  if (status === 'FRESH') return 'success' as const
  if (status === 'STALE') return 'warning' as const
  return 'danger' as const
}

function freshnessMessage(status: FreshnessStatus): string {
  if (status === 'FRESH') return 'Data is current for RM review.'
  if (status === 'STALE') return 'Data may be outdated — verify before customer contact.'
  return 'Data is missing — analysis confidence may be reduced.'
}

export function DataFreshnessPanel({
  freshness,
  warnings = [],
}: {
  freshness: DataFreshness
  warnings?: string[]
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Data freshness</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {(Object.keys(SOURCE_LABELS) as Array<keyof DataFreshness>).map((key) => {
          const source = freshness[key]
          return (
            <div key={key} className="rounded-lg border border-slate-200 p-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="font-medium text-slate-900">{SOURCE_LABELS[key]}</p>
                <Badge variant={freshnessVariant(source.status)}>{source.status}</Badge>
              </div>
              <p className="mt-1 text-xs text-slate-500">
                Last updated: {formatDateTime(source.last_updated)}
              </p>
              <p className="mt-1 text-xs text-slate-500">{freshnessMessage(source.status)}</p>
            </div>
          )
        })}

        {warnings.length > 0 ? (
          <div className="rounded-lg bg-amber-50 px-3 py-2 ring-1 ring-amber-200">
            <p className="text-sm font-medium text-amber-900">Customer 360 warnings</p>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-xs text-amber-800">
              {warnings.map((warning) => (
                <li key={warning}>{warning}</li>
              ))}
            </ul>
          </div>
        ) : null}
      </CardContent>
    </Card>
  )
}
