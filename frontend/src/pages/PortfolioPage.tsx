import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import {
  AlertTriangle,
  IndianRupee,
  RefreshCw,
  Target,
  TrendingUp,
  Users,
} from 'lucide-react'

import { fetchPortfolioCustomers, fetchPortfolioSummary } from '../api/portfolio'
import { ActionDistributionChart } from '../components/charts/ActionDistributionChart'
import { RevenueByProductChart } from '../components/charts/RevenueByProductChart'
import { RiskValueMatrix } from '../components/charts/RiskValueMatrix'
import { CustomerTable } from '../components/customers/CustomerTable'
import { PageHeader } from '../components/layout/PageHeader'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { EmptyState } from '../components/ui/EmptyState'
import { ErrorState } from '../components/ui/ErrorState'
import { StatCard } from '../components/ui/StatCard'
import { useDebounce } from '../hooks/useDebounce'
import { useDocumentTitle } from '../hooks/useDocumentTitle'
import type { CustomerSegment, RecommendationDecision } from '../types/api'
import type { PortfolioSortField } from '../types/portfolio'
import { formatINR } from '../utils/currency'
import { formatDateTime } from '../utils/date'
import { queryKeys } from '../utils/queryKeys'
import { BANKING_TOOLTIPS } from '../components/ui/Tooltip'

const SEGMENTS: CustomerSegment[] = ['STANDARD', 'MASS_AFFLUENT', 'PRIORITY', 'PRIVATE']
const DECISIONS: RecommendationDecision[] = ['RETAIN', 'REVIEW', 'MONITOR', 'NO_ACTION']

export function PortfolioPage() {
  useDocumentTitle('Customer Retention Command Center')
  const [searchParams, setSearchParams] = useSearchParams()

  const page = Number(searchParams.get('page') ?? '1')
  const pageSize = Number(searchParams.get('page_size') ?? '10')
  const search = searchParams.get('search') ?? ''
  const debouncedSearch = useDebounce(search, 300)
  const segment = (searchParams.get('segment') as CustomerSegment | null) ?? undefined
  const decision = (searchParams.get('decision') as RecommendationDecision | null) ?? undefined
  const minimumPriority = searchParams.get('minimum_priority')
    ? Number(searchParams.get('minimum_priority'))
    : undefined
  const sortBy = (searchParams.get('sort_by') as PortfolioSortField) || 'priority_score'
  const sortOrder = (searchParams.get('sort_order') as 'asc' | 'desc') || 'desc'

  const customerParams = useMemo(
    () => ({
      page,
      page_size: pageSize,
      search: debouncedSearch || undefined,
      segment,
      decision,
      minimum_priority: minimumPriority,
      sort_by: sortBy,
      sort_order: sortOrder,
    }),
    [page, pageSize, debouncedSearch, segment, decision, minimumPriority, sortBy, sortOrder],
  )

  const summaryQuery = useQuery({
    queryKey: queryKeys.portfolio.summary,
    queryFn: fetchPortfolioSummary,
    refetchOnWindowFocus: true,
  })

  const customersQuery = useQuery({
    queryKey: queryKeys.portfolio.customers(customerParams),
    queryFn: () => fetchPortfolioCustomers(customerParams),
    refetchOnWindowFocus: true,
  })

  const chartCustomersQuery = useQuery({
    queryKey: queryKeys.portfolio.customers({ page: 1, page_size: 100 }),
    queryFn: () => fetchPortfolioCustomers({ page: 1, page_size: 100 }),
  })

  const updateParam = (key: string, value: string | null) => {
    const next = new URLSearchParams(searchParams)
    if (value === null || value === '') next.delete(key)
    else next.set(key, value)
    if (key !== 'page') next.set('page', '1')
    setSearchParams(next)
  }

  const clearFilters = () => setSearchParams({ page: '1', page_size: String(pageSize) })

  const handleSort = (key: string) => {
    const nextOrder = sortBy === key && sortOrder === 'desc' ? 'asc' : 'desc'
    updateParam('sort_by', key)
    updateParam('sort_order', nextOrder)
  }

  const refresh = () => {
    summaryQuery.refetch()
    customersQuery.refetch()
    chartCustomersQuery.refetch()
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Customer Retention Command Center"
        description="Prioritize outreach across your synthetic retail portfolio using deterministic scores and agent-assisted recommendations."
        meta={
          <>
            <Badge variant="warning">Synthetic data</Badge>
            {summaryQuery.data ? (
              <span className="text-xs text-slate-500">
                Last refreshed {formatDateTime(summaryQuery.data.generated_at)}
              </span>
            ) : null}
          </>
        }
        actions={
          <Button variant="outline" onClick={refresh} disabled={summaryQuery.isFetching}>
            <RefreshCw className="h-4 w-4" aria-hidden="true" />
            Refresh
          </Button>
        }
      />

      {summaryQuery.isError ? (
        <ErrorState
          message="Unable to load portfolio summary."
          onRetry={() => summaryQuery.refetch()}
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
          <StatCard
            label="Total customers"
            value={summaryQuery.data?.total_customers ?? '—'}
            description="Customers in the seeded portfolio."
            icon={<Users className="h-4 w-4" />}
          />
          <StatCard
            label="Immediate intervention"
            value={summaryQuery.data?.immediate_intervention_count ?? '—'}
            description="RETAIN decisions requiring urgent RM action."
            icon={<AlertTriangle className="h-4 w-4" />}
          />
          <StatCard
            label="RM review"
            value={summaryQuery.data?.review_count ?? '—'}
            description="Customers flagged for relationship review."
            icon={<Target className="h-4 w-4" />}
          />
          <StatCard
            label="Revenue at risk"
            value={
              summaryQuery.data
                ? formatINR(summaryQuery.data.total_revenue_at_risk, true)
                : '—'
            }
            description="Estimated annual value exposed to churn."
            icon={<IndianRupee className="h-4 w-4" />}
            tooltip={BANKING_TOOLTIPS.revenueAtRisk}
          />
          <StatCard
            label="Expected net benefit"
            value={
              summaryQuery.data
                ? formatINR(summaryQuery.data.total_positive_expected_net_benefit, true)
                : '—'
            }
            description="Positive retention value from eligible offers."
            icon={<TrendingUp className="h-4 w-4" />}
          />
          <StatCard
            label="Open alerts"
            value={summaryQuery.data?.open_alerts ?? '—'}
            description="Unacknowledged retention alerts in the system."
            icon={<AlertTriangle className="h-4 w-4" />}
          />
        </div>
      )}

      {summaryQuery.data && chartCustomersQuery.data ? (
        <div className="grid gap-6 xl:grid-cols-2">
          <ActionDistributionChart summary={summaryQuery.data} />
          <RevenueByProductChart customers={chartCustomersQuery.data.items} />
        </div>
      ) : null}

      {chartCustomersQuery.data ? (
        <RiskValueMatrix customers={chartCustomersQuery.data.items} />
      ) : null}

      <section aria-labelledby="priority-customers-heading">
        <h2 id="priority-customers-heading" className="mb-4 text-lg font-semibold text-slate-900">
          Priority customers
        </h2>

        <div className="mb-4 flex flex-col gap-3 lg:flex-row lg:items-end">
          <div className="flex-1">
            <label htmlFor="portfolio-search" className="text-sm font-medium text-slate-700">
              Search
            </label>
            <input
              id="portfolio-search"
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              placeholder="Name or customer ID"
              value={search}
              onChange={(e) => updateParam('search', e.target.value)}
            />
          </div>
          <div>
            <label htmlFor="decision-filter" className="text-sm font-medium text-slate-700">
              Decision
            </label>
            <select
              id="decision-filter"
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              value={decision ?? ''}
              onChange={(e) => updateParam('decision', e.target.value || null)}
            >
              <option value="">All</option>
              {DECISIONS.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="segment-filter" className="text-sm font-medium text-slate-700">
              Segment
            </label>
            <select
              id="segment-filter"
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              value={segment ?? ''}
              onChange={(e) => updateParam('segment', e.target.value || null)}
            >
              <option value="">All</option>
              {SEGMENTS.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="priority-filter" className="text-sm font-medium text-slate-700">
              Min priority
            </label>
            <input
              id="priority-filter"
              type="number"
              min={0}
              max={100}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              value={minimumPriority ?? ''}
              onChange={(e) => updateParam('minimum_priority', e.target.value || null)}
            />
          </div>
          <Button variant="ghost" onClick={clearFilters}>
            Clear filters
          </Button>
        </div>

        {customersQuery.isError ? (
          <ErrorState
            message="Unable to load portfolio customers."
            onRetry={() => customersQuery.refetch()}
          />
        ) : (
          <>
            <CustomerTable
              rows={customersQuery.data?.items ?? []}
              loading={customersQuery.isLoading}
              sortKey={sortBy}
              sortOrder={sortOrder}
              onSort={handleSort}
              emptyState={
                <EmptyState
                  title="No customers match"
                  description="Try adjusting your search or filters."
                  action={{ label: 'Clear filters', onClick: clearFilters }}
                />
              }
            />
            {customersQuery.data && customersQuery.data.pages > 1 ? (
              <div className="mt-4 flex items-center justify-between">
                <p className="text-sm text-slate-500">
                  Page {customersQuery.data.page} of {customersQuery.data.pages} (
                  {customersQuery.data.total} customers)
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={page <= 1}
                    onClick={() => updateParam('page', String(page - 1))}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={page >= customersQuery.data.pages}
                    onClick={() => updateParam('page', String(page + 1))}
                  >
                    Next
                  </Button>
                </div>
              </div>
            ) : null}
          </>
        )}
      </section>
    </div>
  )
}
