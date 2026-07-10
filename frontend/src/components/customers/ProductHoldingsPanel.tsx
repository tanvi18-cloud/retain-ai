import type { Account } from '../../types/customer'
import { formatINR } from '../../utils/currency'
import { formatDate } from '../../utils/date'
import { Badge } from '../ui/Badge'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card'

function maskAccountId(accountId: string): string {
  if (accountId.length <= 4) return `****${accountId}`
  return `****${accountId.slice(-4)}`
}

export function ProductHoldingsPanel({ accounts }: { accounts: Account[] }) {
  if (accounts.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Accounts & products</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-slate-500">No account data available.</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Accounts & products</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {accounts.map((account) => (
          <div key={account.account_id} className="rounded-lg border border-slate-200 p-4">
            <div className="flex flex-wrap items-center gap-2">
              <p className="font-medium text-slate-900">{account.account_type}</p>
              <Badge variant="neutral">{maskAccountId(account.account_id)}</Badge>
              {account.salary_account ? <Badge variant="info">Salary account</Badge> : null}
              <Badge variant={account.status === 'ACTIVE' ? 'success' : 'warning'}>
                {account.status}
              </Badge>
            </div>
            <dl className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
              <div>
                <dt className="text-slate-500">Current balance</dt>
                <dd className="font-medium">{formatINR(account.current_balance)}</dd>
              </div>
              <div>
                <dt className="text-slate-500">Avg 90-day balance</dt>
                <dd className="font-medium">{formatINR(account.average_balance_90d)}</dd>
              </div>
              {account.fixed_deposit_maturity_date ? (
                <div>
                  <dt className="text-slate-500">FD maturity</dt>
                  <dd className="font-medium">
                    {formatDate(account.fixed_deposit_maturity_date)}
                  </dd>
                </div>
              ) : null}
            </dl>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}
