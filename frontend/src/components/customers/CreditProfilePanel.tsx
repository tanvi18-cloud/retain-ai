import type { CreditProfile } from '../../types/customer'
import { formatPercentage } from '../../utils/date'
import { Badge } from '../ui/Badge'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card'
import { BANKING_TOOLTIPS, Tooltip } from '../ui/Tooltip'

export function CreditProfilePanel({ profile }: { profile: CreditProfile | null }) {
  if (!profile) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Credit profile</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-slate-500">Credit profile not available.</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Credit profile</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <dl className="grid gap-4 sm:grid-cols-2">
          <div>
            <dt className="text-xs text-slate-500">Credit score</dt>
            <dd className="text-lg font-semibold">{profile.credit_score}</dd>
          </div>
          <div>
            <dt className="text-xs text-slate-500">
              <Tooltip content={BANKING_TOOLTIPS.dpd}>Max DPD (12m)</Tooltip>
            </dt>
            <dd className="text-lg font-semibold">{profile.max_dpd_12m} days</dd>
          </div>
          <div>
            <dt className="text-xs text-slate-500">Utilization</dt>
            <dd className="font-medium">{formatPercentage(profile.credit_utilization_pct)}</dd>
          </div>
          <div>
            <dt className="text-xs text-slate-500">Active loans</dt>
            <dd className="font-medium">{profile.active_loans}</dd>
          </div>
          <div>
            <dt className="text-xs text-slate-500">Recent inquiries</dt>
            <dd className="font-medium">{profile.recent_credit_inquiries}</dd>
          </div>
          <div>
            <dt className="text-xs text-slate-500">Default flag</dt>
            <dd>
              <Badge variant={profile.default_flag ? 'danger' : 'success'}>
                {profile.default_flag ? 'Yes' : 'No'}
              </Badge>
            </dd>
          </div>
        </dl>
        <p className="rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-900 ring-1 ring-amber-200">
          Eligibility shown in RetainAI supports RM discussion only and is not final credit
          approval.
        </p>
      </CardContent>
    </Card>
  )
}
