import { useId, useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search, UserRound } from 'lucide-react'

import { fetchCustomers } from '../../api/customers'
import { useDebounce } from '../../hooks/useDebounce'
import type { CustomerSummary } from '../../types/customer'
import { queryKeys } from '../../utils/queryKeys'
import { cn } from '../../utils/cn'
import { Skeleton } from '../ui/Skeleton'

const CHAT_CUSTOMER_ID_PATTERN = /^C(?:00[1-9]|010)$/

function isChatCustomer(customerId: string): boolean {
  return CHAT_CUSTOMER_ID_PATTERN.test(customerId)
}

export interface CustomerContextSelectorProps {
  value: string | null
  onChange: (customerId: string | null) => void
  disabled?: boolean
}

export function CustomerContextSelector({
  value,
  onChange,
  disabled = false,
}: CustomerContextSelectorProps) {
  const labelId = useId()
  const listboxId = useId()
  const [search, setSearch] = useState('')
  const debouncedSearch = useDebounce(search, 300)

  const customersQuery = useQuery({
    queryKey: queryKeys.customers.list({ page_size: 20, search: debouncedSearch || undefined }),
    queryFn: () =>
      fetchCustomers({
        page_size: 20,
        search: debouncedSearch || undefined,
        sort_by: 'customer_id',
        sort_order: 'asc',
      }),
  })

  const customers = useMemo(
    () => (customersQuery.data?.items ?? []).filter((customer) => isChatCustomer(customer.customer_id)),
    [customersQuery.data?.items],
  )

  const selectedCustomer = useMemo(
    () => customers.find((customer) => customer.customer_id === value) ?? null,
    [customers, value],
  )

  const handleSelect = (customer: CustomerSummary | null) => {
    onChange(customer?.customer_id ?? null)
    setSearch('')
  }

  return (
    <div className="space-y-2">
      <label id={labelId} htmlFor={`${labelId}-search`} className="text-sm font-medium text-slate-700">
        Customer context
      </label>

      <div className="relative">
        <Search
          className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
          aria-hidden="true"
        />
        <input
          id={`${labelId}-search`}
          type="search"
          role="combobox"
          aria-labelledby={labelId}
          aria-controls={listboxId}
          aria-expanded={customers.length > 0}
          aria-autocomplete="list"
          placeholder="Search C001–C010…"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          disabled={disabled}
          className={cn(
            'w-full rounded-lg border border-slate-300 py-2 pl-9 pr-3 text-sm',
            'focus:border-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-200',
            'disabled:cursor-not-allowed disabled:bg-slate-50 disabled:text-slate-500',
          )}
        />
      </div>

      <p className="text-xs text-slate-500">
        {selectedCustomer
          ? `Selected: ${selectedCustomer.customer_id} — ${selectedCustomer.full_name}`
          : 'No customer selected — portfolio-wide context'}
      </p>

      {customersQuery.isLoading ? (
        <Skeleton className="h-24 w-full rounded-lg" />
      ) : (
        <ul
          id={listboxId}
          role="listbox"
          aria-labelledby={labelId}
          className="max-h-48 space-y-1 overflow-y-auto rounded-lg border border-slate-200 bg-white p-1"
        >
          <li role="presentation">
            <button
              type="button"
              role="option"
              aria-selected={value === null}
              disabled={disabled}
              onClick={() => handleSelect(null)}
              className={cn(
                'flex w-full items-center gap-2 rounded-md px-3 py-2 text-left text-sm',
                'hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400',
                value === null && 'bg-slate-100 font-medium',
                disabled && 'cursor-not-allowed opacity-50',
              )}
            >
              <UserRound className="h-4 w-4 text-slate-400" aria-hidden="true" />
              No customer context
            </button>
          </li>
          {customers.map((customer) => (
            <li key={customer.customer_id} role="presentation">
              <button
                type="button"
                role="option"
                aria-selected={value === customer.customer_id}
                disabled={disabled}
                onClick={() => handleSelect(customer)}
                className={cn(
                  'flex w-full flex-col rounded-md px-3 py-2 text-left text-sm',
                  'hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400',
                  value === customer.customer_id && 'bg-slate-100 font-medium',
                  disabled && 'cursor-not-allowed opacity-50',
                )}
              >
                <span className="font-medium text-slate-900">{customer.customer_id}</span>
                <span className="text-xs text-slate-500">{customer.full_name}</span>
              </button>
            </li>
          ))}
          {!customersQuery.isLoading && customers.length === 0 ? (
            <li className="px-3 py-2 text-sm text-slate-500">No matching customers found.</li>
          ) : null}
        </ul>
      )}
    </div>
  )
}
