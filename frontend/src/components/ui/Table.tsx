import type { ReactNode } from 'react'

import { cn } from '../../utils/cn'
import { Skeleton } from './Skeleton'

export interface TableColumn<T> {
  key: string
  header: ReactNode
  sortable?: boolean
  className?: string
  render: (row: T) => ReactNode
}

export interface TableProps<T> {
  columns: TableColumn<T>[]
  data: T[]
  rowKey: (row: T) => string
  loading?: boolean
  loadingRows?: number
  emptyState?: ReactNode
  sortKey?: string
  sortOrder?: 'asc' | 'desc'
  onSort?: (key: string) => void
}

export function Table<T>({
  columns,
  data,
  rowKey,
  loading,
  loadingRows = 5,
  emptyState,
  sortKey,
  sortOrder,
  onSort,
}: TableProps<T>) {
  if (!loading && data.length === 0 && emptyState) {
    return <>{emptyState}</>
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50">
          <tr>
            {columns.map((column) => (
              <th
                key={column.key}
                scope="col"
                className={cn(
                  'px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500',
                  column.className,
                )}
              >
                {column.sortable && onSort ? (
                  <button
                    type="button"
                    className="inline-flex items-center gap-1 hover:text-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
                    onClick={() => onSort(column.key)}
                    aria-sort={
                      sortKey === column.key
                        ? sortOrder === 'asc'
                          ? 'ascending'
                          : 'descending'
                        : 'none'
                    }
                  >
                    {column.header}
                    {sortKey === column.key ? (
                      <span aria-hidden="true">{sortOrder === 'asc' ? '↑' : '↓'}</span>
                    ) : null}
                  </button>
                ) : (
                  column.header
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {loading
            ? Array.from({ length: loadingRows }).map((_, index) => (
                <tr key={`loading-${index}`}>
                  {columns.map((column) => (
                    <td key={column.key} className="px-4 py-3">
                      <Skeleton className="h-4 w-full" />
                    </td>
                  ))}
                </tr>
              ))
            : data.map((row) => (
                <tr key={rowKey(row)} className="hover:bg-slate-50">
                  {columns.map((column) => (
                    <td key={column.key} className={cn('px-4 py-3 text-slate-700', column.className)}>
                      {column.render(row)}
                    </td>
                  ))}
                </tr>
              ))}
        </tbody>
      </table>
    </div>
  )
}
