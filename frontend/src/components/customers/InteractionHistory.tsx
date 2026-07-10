import type { Interaction } from '../../types/customer'
import { formatDateTime } from '../../utils/date'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card'
import { EmptyState } from '../ui/EmptyState'

export function InteractionHistory({ interactions }: { interactions: Interaction[] }) {
  const sorted = [...interactions].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
  )

  return (
    <Card>
      <CardHeader>
        <CardTitle>Interaction history</CardTitle>
      </CardHeader>
      <CardContent>
        {sorted.length === 0 ? (
          <EmptyState
            title="No interactions yet"
            description="RM actions and customer contacts will appear here."
          />
        ) : (
          <ul className="space-y-3">
            {sorted.map((item) => (
              <li key={item.interaction_id} className="rounded-lg border border-slate-200 p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="font-medium text-slate-900">{item.action_type}</p>
                  <p className="text-xs text-slate-500">{formatDateTime(item.created_at)}</p>
                </div>
                <p className="text-xs text-slate-500">RM: {item.rm_id}</p>
                {item.notes ? <p className="mt-2 text-sm text-slate-700">{item.notes}</p> : null}
                {item.offer_presented ? (
                  <p className="mt-1 text-xs text-slate-500">Offer presented to customer</p>
                ) : null}
                {item.customer_response ? (
                  <p className="mt-1 text-xs text-slate-600">
                    Customer response: {item.customer_response}
                  </p>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}
