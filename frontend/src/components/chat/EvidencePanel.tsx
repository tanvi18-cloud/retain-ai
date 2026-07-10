import type { ChatEvidence } from '../../types/chat'
import { formatDateTime } from '../../utils/date'
import { Badge } from '../ui/Badge'
import { Drawer } from '../ui/Drawer'
import { EmptyState } from '../ui/EmptyState'

export interface EvidencePanelProps {
  open: boolean
  onClose: () => void
  evidence: ChatEvidence[]
}

function evidenceKey(item: ChatEvidence, index: number): string {
  return `${item.source_system}-${item.field}-${item.customer_id ?? 'none'}-${index}`
}

export function EvidencePanel({ open, onClose, evidence }: EvidencePanelProps) {
  return (
    <Drawer open={open} onClose={onClose} title="Evidence">
      {evidence.length === 0 ? (
        <EmptyState
          title="No evidence"
          description="This response did not include supporting evidence from source systems."
        />
      ) : (
        <ul className="space-y-3">
          {evidence.map((item, index) => (
            <li
              key={evidenceKey(item, index)}
              className="rounded-lg border border-slate-200 bg-slate-50 p-4"
            >
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="info">{item.source_system}</Badge>
                <Badge variant="neutral">{item.source_type}</Badge>
                {item.customer_id ? (
                  <Badge variant="warning">{item.customer_id}</Badge>
                ) : null}
              </div>
              <dl className="mt-3 space-y-2 text-sm">
                <div>
                  <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">Field</dt>
                  <dd className="mt-0.5 font-medium text-slate-900">{item.field}</dd>
                </div>
                <div>
                  <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">
                    Value summary
                  </dt>
                  <dd className="mt-0.5 whitespace-pre-wrap break-words text-slate-700">
                    {item.value_summary}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">
                    Timestamp
                  </dt>
                  <dd className="mt-0.5 text-slate-600">
                    <time dateTime={item.timestamp ?? undefined}>{formatDateTime(item.timestamp)}</time>
                  </dd>
                </div>
              </dl>
            </li>
          ))}
        </ul>
      )}
    </Drawer>
  )
}
