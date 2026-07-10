import { useQuery } from '@tanstack/react-query'
import { Link, useLocation } from 'react-router-dom'
import { Bell, Menu } from 'lucide-react'

import { getEnv, getRmUser } from '../../api/env'
import { fetchPortfolioSummary } from '../../api/portfolio'
import { ConnectionStatus } from '../system/ConnectionStatus'
import { cn } from '../../utils/cn'
import { queryKeys } from '../../utils/queryKeys'
import { Badge } from '../ui/Badge'

const PAGE_TITLES: Record<string, string> = {
  '/': 'Customer Retention Command Center',
  '/customers': 'Customer Directory',
  '/alerts': 'Retention Alerts',
  '/chat': 'RM Copilot',
  '/simulator': 'Event Simulator',
  '/system': 'System Status',
}

function usePageTitle(pathname: string): string {
  if (pathname.startsWith('/customers/')) return 'Customer 360'
  return PAGE_TITLES[pathname] ?? 'RetainAI'
}

export interface TopNavigationProps {
  onMenuClick: () => void
}

export function TopNavigation({ onMenuClick }: TopNavigationProps) {
  const location = useLocation()
  const env = getEnv()
  const rm = getRmUser()
  const pageTitle = usePageTitle(location.pathname)

  const portfolioQuery = useQuery({
    queryKey: queryKeys.portfolio.summary,
    queryFn: fetchPortfolioSummary,
    staleTime: 30_000,
    refetchInterval: 60_000,
  })

  const unacknowledgedCount = portfolioQuery.data?.unacknowledged_alerts ?? 0

  return (
    <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/95 backdrop-blur">
      <div className="flex h-16 items-center gap-4 px-4 lg:px-6">
        <button
          type="button"
          className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 lg:hidden focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
          aria-label="Open navigation menu"
          onClick={onMenuClick}
        >
          <Menu className="h-5 w-5" />
        </button>

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-sm font-semibold text-slate-900">{env.appName}</p>
            <span className="hidden text-slate-300 sm:inline" aria-hidden="true">
              |
            </span>
            <p className="hidden text-sm text-slate-500 sm:block">Customer Retention Copilot</p>
            <Badge variant="warning">Synthetic data</Badge>
            <ConnectionStatus compact className="hidden md:flex" />
          </div>
          <h1 className="truncate text-lg font-semibold text-slate-900">{pageTitle}</h1>
        </div>

        <div className="flex shrink-0 items-center gap-3">
          <Link
            to="/alerts"
            className={cn(
              'relative inline-flex min-h-10 min-w-10 items-center justify-center rounded-lg',
              'text-slate-600 hover:bg-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400',
            )}
            aria-label={
              unacknowledgedCount > 0
                ? `${unacknowledgedCount} unacknowledged alerts`
                : 'View alerts'
            }
          >
            <Bell className="h-5 w-5" aria-hidden="true" />
            {unacknowledgedCount > 0 ? (
              <span className="absolute -right-0.5 -top-0.5 inline-flex min-w-5 items-center justify-center rounded-full bg-red-600 px-1.5 py-0.5 text-[10px] font-semibold text-white">
                {unacknowledgedCount > 99 ? '99+' : unacknowledgedCount}
              </span>
            ) : null}
          </Link>

          <div className="hidden text-right sm:block">
            <p className="text-sm font-medium text-slate-900">{rm.name}</p>
            <p className="text-xs text-slate-500">{rm.id}</p>
          </div>
        </div>
      </div>

      <div className="border-t border-slate-100 px-4 py-2 md:hidden">
        <ConnectionStatus compact />
      </div>
    </header>
  )
}
