import type { CustomerDetail } from '../../types/customer'
import { formatDate } from '../../utils/date'
import { segmentLabel } from '../../utils/risk'
import { Badge } from '../ui/Badge'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card'

export function CustomerSummaryCard({ customer }: { customer: CustomerDetail }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{customer.full_name}</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <div>
          <p className="text-xs text-slate-500">Customer ID</p>
          <p className="font-medium">{customer.customer_id}</p>
        </div>
        <div>
          <p className="text-xs text-slate-500">Segment</p>
          <Badge variant="neutral">{segmentLabel(customer.segment)}</Badge>
        </div>
        <div>
          <p className="text-xs text-slate-500">Customer since</p>
          <p className="font-medium">{formatDate(customer.relationship_start_date)}</p>
        </div>
        <div>
          <p className="text-xs text-slate-500">Assigned RM</p>
          <p className="font-medium">{customer.assigned_rm_name}</p>
        </div>
        <div>
          <p className="text-xs text-slate-500">Preferred channel</p>
          <p className="font-medium">{customer.preferred_channel}</p>
        </div>
        <div>
          <p className="text-xs text-slate-500">Communication consent</p>
          <Badge variant={customer.communication_consent ? 'success' : 'warning'}>
            {customer.communication_consent ? 'Consented' : 'Not consented'}
          </Badge>
        </div>
      </CardContent>
    </Card>
  )
}
