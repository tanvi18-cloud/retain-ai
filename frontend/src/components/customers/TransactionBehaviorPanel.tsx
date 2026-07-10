import type { TransactionFeature } from '../../types/customer'
import { formatINR } from '../../utils/currency'
import { Badge } from '../ui/Badge'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card'
import { Tooltip } from '../ui/Tooltip'

function Trend({ value, suffix = '%' }: { value: number; suffix?: string }) {
  const positive = value > 0
  const negative = value < 0
  return (
    <span
      className={
        positive ? 'text-emerald-700' : negative ? 'text-red-700' : 'text-slate-600'
      }
    >
      {positive ? '↑' : negative ? '↓' : '→'} {Math.abs(value).toFixed(1)}
      {suffix}
    </span>
  )
}

export function TransactionBehaviorPanel({ features }: { features: TransactionFeature | null }) {
  if (!features) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Transaction behavior</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-slate-500">Transaction features not available.</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Transaction behavior</CardTitle>
      </CardHeader>
      <CardContent>
        <dl className="grid gap-4 sm:grid-cols-2">
          <div>
            <dt className="text-xs text-slate-500">Salary received this month</dt>
            <dd className="font-medium">
              {features.salary_received_current_month ? 'Yes' : 'No'}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-slate-500">Balance change (30d)</dt>
            <dd>
              <Trend value={features.balance_change_pct_30d} />
            </dd>
          </div>
          <div>
            <dt className="text-xs text-slate-500">Monthly inflow</dt>
            <dd className="font-medium">{formatINR(features.monthly_inflow)}</dd>
          </div>
          <div>
            <dt className="text-xs text-slate-500">Monthly outflow</dt>
            <dd className="font-medium">{formatINR(features.monthly_outflow)}</dd>
          </div>
          <div>
            <dt className="text-xs text-slate-500">External transfers (30d)</dt>
            <dd className="font-medium">{formatINR(features.external_transfer_amount_30d)}</dd>
          </div>
          <div>
            <dt className="text-xs text-slate-500">Card spend change (30d)</dt>
            <dd>
              <Trend value={features.card_spend_change_pct_30d} />
            </dd>
          </div>
          <div>
            <dt className="text-xs text-slate-500">Forex spending (30d)</dt>
            <dd className="font-medium">{formatINR(features.forex_spend_30d)}</dd>
          </div>
          <div>
            <dt className="text-xs text-slate-500">Competitor transfer</dt>
            <dd>
              {features.competitor_transfer_detected ? (
                <Badge variant="danger">Detected</Badge>
              ) : (
                <Badge variant="success">Not detected</Badge>
              )}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-slate-500">Product inactivity</dt>
            <dd>
              <Tooltip content="Days since meaningful product usage was observed.">
                <span className="font-medium">{features.product_inactivity_days} days</span>
              </Tooltip>
            </dd>
          </div>
        </dl>
        <p className="mt-4 text-xs text-slate-500">
          Signals reflect observed transaction patterns. They do not imply causation beyond backend
          evidence.
        </p>
      </CardContent>
    </Card>
  )
}
