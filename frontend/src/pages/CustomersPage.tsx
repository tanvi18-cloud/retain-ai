import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'

import { fetchCustomers } from '../api/customers'
import { PageHeader } from '../components/layout/PageHeader'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { EmptyState } from '../components/ui/EmptyState'
import { ErrorState } from '../components/ui/ErrorState'
import { Table, type TableColumn } from '../components/ui/Table'
import { useDebounce } from '../hooks/useDebounce'
import { useDocumentTitle } from '../hooks/useDocumentTitle'
import type { CustomerSegment } from '../types/api'
import type { CustomerSummary } from '../types/customer'
import { formatINR } from '../utils/currency'
import { segmentLabel } from '../utils/risk'
import { queryKeys } from '../utils/queryKeys'

const SEGMENTS: CustomerSegment[] = ['STANDARD', 'MASS_AFFLUENT', 'PRIORITY', 'PRIVATE']

export function CustomersPage() {
  useDocumentTitle('Customer Directory')
  const [searchParams, setSearchParams] = useSearchParams()

  const page = Number(searchParams.get('page') ?? '1')
  const pageSize = Number(searchParams.get('page_size') ?? '20')
  const search = searchParams.get('search') ?? ''
  const debouncedSearch = useDebounce(search, 300)
  const segment = (searchParams.get('segment') as CustomerSegment | null) ?? undefined
  const sortBy =
    (searchParams.get('sort_by') as
      | 'customer_id'
      | 'full_name'
      | 'relationship_start_date'
      | 'estimated_annual_value') || 'customer_id'
  const sortOrder = (searchParams.get('sort_order') as 'asc' | 'desc') || 'asc'
  const view = searchParams.get('view') === 'cards' ? 'cards' : 'table'

  const params = useMemo(
    () => ({
      page,
      page_size: pageSize,
      search: debouncedSearch || undefined,
      segment,
      sort_by: sortBy,
      sort_order: sortOrder,
    }),
    [page, pageSize, debouncedSearch, segment, sortBy, sortOrder],
  )

  const query = useQuery({
    queryKey: queryKeys.customers.list(params),
    queryFn: () => fetchCustomers(params),
  })

  const updateParam = (key: string, value: string | null) => {
    const next = new URLSearchParams(searchParams)
    if (value === null || value === '') next.delete(key)
    else next.set(key, value)
    if (key !== 'page') next.set('page', '1')
    setSearchParams(next)
  }

  const handleSort = (key: string) => {
    const nextOrder = sortBy === key && sortOrder === 'asc' ? 'desc' : 'asc'
    updateParam('sort_by', key)
    updateParam('sort_order', nextOrder)
  }

  const columns: TableColumn<CustomerSummary>[] = [
    {
      key: 'customer_id',
      header: 'Customer ID',
      sortable: true,
      render: (row) => row.customer_id,
    },
    {
      key: 'full_name',
      header: 'Name',
      sortable: true,
      render: (row) => row.full_name,
    },
    {
      key: 'segment',
      header: 'Segment',
      render: (row) => <Badge variant="neutral">{segmentLabel(row.segment)}</Badge>,
    },
    {
      key: 'assigned_rm_name',
      header: 'Assigned RM',
      render: (row) => row.assigned_rm_name,
    },
    {
      key: 'estimated_annual_value',
      header: 'Annual value',
      sortable: true,
      render: (row) => formatINR(row.estimated_annual_value),
    },
    {
      key: 'preferred_channel',
      header: 'Channel',
      render: (row) => row.preferred_channel,
    },
    {
      key: 'actions',
      header: '',
      render: (row) => (
        <Link
          to={`/customers/${row.customer_id}`}
          className="text-sm font-medium text-slate-900 underline-offset-2 hover:underline"
        >
          Customer 360
        </Link>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      <PageHeader
        title="Customer Directory"
        description="Browse the synthetic customer book. Open Customer 360 for retention analysis and RM actions."
        actions={
          <div className="flex gap-2">
            <Button
              variant={view === 'table' ? 'primary' : 'outline'}
              size="sm"
              onClick={() => updateParam('view', 'table')}
            >
              Table
            </Button>
            <Button
              variant={view === 'cards' ? 'primary' : 'outline'}
              size="sm"
              onClick={() => updateParam('view', 'cards')}
            >
              Cards
            </Button>
          </div>
        }
      />

      <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
        <div className="flex-1">
          <label htmlFor="customer-search" className="text-sm font-medium text-slate-700">
            Search
          </label>
          <input
            id="customer-search"
            className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            placeholder="Name or customer ID"
            value={search}
            onChange={(e) => updateParam('search', e.target.value)}
          />
        </div>
        <div>
          <label htmlFor="customer-segment" className="text-sm font-medium text-slate-700">
            Segment
          </label>
          <select
            id="customer-segment"
            className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            value={segment ?? ''}
            onChange={(e) => updateParam('segment', e.target.value || null)}
          >
            <option value="">All</option>
            {SEGMENTS.map((s) => (
              <option key={s} value={s}>
                {segmentLabel(s)}
              </option>
            ))}
          </select>
        </div>
      </div>

      {query.isError ? (
        <ErrorState message="Unable to load customers." onRetry={() => query.refetch()} />
      ) : view === 'table' ? (
        <Table
          columns={columns}
          data={query.data?.items ?? []}
          rowKey={(row) => row.customer_id}
          loading={query.isLoading}
          sortKey={sortBy}
          sortOrder={sortOrder}
          onSort={handleSort}
          emptyState={
            <EmptyState
              title="No customers found"
              description="Try a different search or segment filter."
            />
          }
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {(query.data?.items ?? []).map((customer) => (
            <Link
              key={customer.customer_id}
              to={`/customers/${customer.customer_id}`}
              className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm transition hover:border-slate-300"
            >
              <p className="font-semibold text-slate-900">{customer.full_name}</p>
              <p className="text-sm text-slate-500">{customer.customer_id}</p>
              <div className="mt-3 flex flex-wrap gap-2">
                <Badge variant="neutral">{segmentLabel(customer.segment)}</Badge>
                <Badge variant="info">{formatINR(customer.estimated_annual_value, true)}</Badge>
              </div>
              <p className="mt-2 text-xs text-slate-500">RM: {customer.assigned_rm_name}</p>
            </Link>
          ))}
        </div>
      )}

      {query.data && query.data.pages > 1 ? (
        <div className="flex items-center justify-between">
          <p className="text-sm text-slate-500">
            Page {query.data.page} of {query.data.pages}
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
              disabled={page >= query.data.pages}
              onClick={() => updateParam('page', String(page + 1))}
            >
              Next
            </Button>
          </div>
        </div>
      ) : null}
    </div>
  )
}
