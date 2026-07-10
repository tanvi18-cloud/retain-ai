import { Link } from 'react-router-dom'

import type { PortfolioCustomerRow } from '../../types/portfolio'
import { formatINR } from '../../utils/currency'
import {
  decisionLabel,
  decisionVariant,
  recommendationStatusLabel,
  riskLabelFromScore,
  segmentLabel,
} from '../../utils/risk'
import { Badge } from '../ui/Badge'
import { Table, type TableColumn } from '../ui/Table'

export interface CustomerTableProps {
  rows: PortfolioCustomerRow[]
  loading?: boolean
  sortKey?: string
  sortOrder?: 'asc' | 'desc'
  onSort?: (key: string) => void
  emptyState?: React.ReactNode
}

export function CustomerTable({
  rows,
  loading,
  sortKey,
  sortOrder,
  onSort,
  emptyState,
}: CustomerTableProps) {
  const columns: TableColumn<PortfolioCustomerRow>[] = [
    {
      key: 'customer',
      header: 'Customer',
      render: (row) => (
        <div>
          <p className="font-medium text-slate-900">{row.full_name}</p>
          <p className="text-xs text-slate-500">{row.customer_id}</p>
        </div>
      ),
    },
    {
      key: 'segment',
      header: 'Segment',
      render: (row) => <Badge variant="neutral">{segmentLabel(row.segment)}</Badge>,
    },
    {
      key: 'primary_trigger',
      header: 'Primary signal',
      render: (row) => row.primary_trigger ?? '—',
    },
    {
      key: 'churn_score',
      header: 'Churn risk',
      sortable: true,
      render: (row) => (
        <div className="flex items-center gap-2">
          <span className="font-medium">{row.churn_score}</span>
          <Badge variant={row.churn_score >= 75 ? 'danger' : row.churn_score >= 50 ? 'warning' : 'success'}>
            {riskLabelFromScore(row.churn_score)}
          </Badge>
        </div>
      ),
    },
    {
      key: 'value_score',
      header: 'Customer value',
      sortable: true,
      render: (row) => row.value_score,
    },
    {
      key: 'priority_score',
      header: 'Priority',
      sortable: true,
      render: (row) => <span className="font-semibold">{row.priority_score}</span>,
    },
    {
      key: 'decision',
      header: 'Decision',
      render: (row) => <Badge variant={decisionVariant(row.decision)}>{decisionLabel(row.decision)}</Badge>,
    },
    {
      key: 'revenue_at_risk',
      header: 'Revenue at risk',
      sortable: true,
      render: (row) => formatINR(row.revenue_at_risk),
    },
    {
      key: 'expected_net_benefit',
      header: 'Expected net benefit',
      sortable: true,
      render: (row) =>
        row.expected_net_benefit != null ? formatINR(row.expected_net_benefit) : '—',
    },
    {
      key: 'recommendation_status',
      header: 'Status',
      render: (row) =>
        row.recommendation_status ? (
          <Badge variant="info">{recommendationStatusLabel(row.recommendation_status as import('../../types/api').RecommendationStatus)}</Badge>
        ) : (
          '—'
        ),
    },
    {
      key: 'recommended_action',
      header: 'Action',
      render: (row) => <span className="text-xs">{row.recommended_action}</span>,
    },
    {
      key: 'actions',
      header: '',
      render: (row) => (
        <Link
          to={`/customers/${row.customer_id}`}
          className="inline-flex h-8 items-center rounded-lg border border-slate-300 bg-white px-3 text-sm font-medium text-slate-800 hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
        >
          View
        </Link>
      ),
    },
  ]

  return (
    <Table
      columns={columns}
      data={rows}
      rowKey={(row) => row.customer_id}
      loading={loading}
      sortKey={sortKey}
      sortOrder={sortOrder}
      onSort={onSort}
      emptyState={emptyState}
    />
  )
}
