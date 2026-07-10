import { useMemo } from 'react'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import type { PortfolioCustomerRow } from '../../types/portfolio'
import { formatINR } from '../../utils/currency'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/Card'

const PRODUCT_BUCKETS = [
  'home loan',
  'credit card',
  'deposits',
  'travel',
  'relationship',
  'other',
] as const

type ProductBucket = (typeof PRODUCT_BUCKETS)[number]

function classifyProduct(row: PortfolioCustomerRow): ProductBucket {
  const trigger = (row.primary_trigger ?? '').toLowerCase()
  const offer = (row.top_eligible_offer_name ?? '').toLowerCase()

  if (trigger.includes('home') || trigger.includes('loan') || offer.includes('home')) {
    return 'home loan'
  }
  if (trigger.includes('card') || offer.includes('card')) return 'credit card'
  if (trigger.includes('deposit') || trigger.includes('fd') || offer.includes('deposit')) {
    return 'deposits'
  }
  if (trigger.includes('forex') || trigger.includes('travel') || offer.includes('travel')) {
    return 'travel'
  }
  if (trigger.includes('salary') || trigger.includes('relationship') || offer.includes('relationship')) {
    return 'relationship'
  }
  return 'other'
}

export interface RevenueByProductChartProps {
  customers: PortfolioCustomerRow[]
}

export function RevenueByProductChart({ customers }: RevenueByProductChartProps) {
  const data = useMemo(() => {
    const totals = Object.fromEntries(PRODUCT_BUCKETS.map((b) => [b, 0])) as Record<
      ProductBucket,
      number
    >

    for (const row of customers) {
      const bucket = classifyProduct(row)
      totals[bucket] += row.revenue_at_risk
    }

    return PRODUCT_BUCKETS.map((bucket) => ({
      bucket,
      revenue: totals[bucket],
    }))
  }, [customers])

  const totalRevenue = data.reduce((sum, item) => sum + item.revenue, 0)

  return (
    <Card>
      <CardHeader>
        <CardTitle>Revenue at risk by product (estimated)</CardTitle>
        <CardDescription>
          Grouped from primary trigger and top offer fields. Estimates only — not sourced from
          product ledger.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <p className="mb-3 text-sm text-slate-600">
          Total estimated revenue at risk: {formatINR(totalRevenue)}
        </p>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="bucket" tick={{ fontSize: 11 }} />
              <YAxis tickFormatter={(v) => formatINR(Number(v), true)} tick={{ fontSize: 11 }} />
              <Tooltip formatter={(value) => formatINR(Number(value))} />
              <Bar dataKey="revenue" fill="#0f766e" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}
