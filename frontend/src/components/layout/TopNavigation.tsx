import { useQuery } from '@tanstack/react-query'
import { Link, useLocation } from 'react-router-dom'
import {
  Activity,
  Bell,
  Bot,
  LayoutDashboard,
  Menu,
  Users,
  Zap,
} from 'lucide-react'

import { fetchHealth } from '../../api/health'
import { getEnv } from '../../api/env'
import { cn } from '../../utils/cn'
import { queryKeys } from '../../utils/queryKeys'
import { Badge } from '../ui/Badge'
import { Tooltip } from '../ui/Tooltip'

const NAV_ITEMS = [
  { to: '/', label: 'Portfolio', icon: LayoutDashboard, ready: true },
  { to: '/customers', label: 'Customers', icon: Users, ready: true },
  { to: '/alerts', label: 'Alerts', icon: Bell, ready: false },
  { to: '/copilot', label: 'RM Copilot', icon: Bot, ready: false },
  { to: '/simulator', label: 'Event Simulator', icon: Zap, ready: false },
  { to: '/system', label: 'System Status', icon: Activity, ready: false },
] as const

const PAGE_TITLES: Record<string, string> = {
  '/': 'Customer Retention Command Center',
  '/customers': 'Customer Directory',
  '/alerts': 'Alerts',
  '/copilot': 'RM Copilot',
  '/simulator': 'Event Simulator',
  '/system': 'System Status',
}

function usePageTitle(pathname: string): string {
  if (pathname.startsWith('/customers/')) return 'Customer 360'
  return PAGE_TITLES[pathname] ?? 'RetainAI'
}

function ApiStatusIndicator() {
  const { data, isFetching, isError } = useQuery({
    queryKey: queryKeys.health,
    queryFn: fetchHealth,
    refetchInterval: 60_000,
    retry: 1,
    staleTime: 30_000,
  })

  const state = isFetching && !data ? 'Checking' : isError || !data ? 'Unavailable' : 'Connected'
  const variant = state === 'Connected' ? 'success' : state === 'Checking' ? 'info' : 'danger'

  return (
    <Tooltip content={`API status: ${state}. Health check runs every 60 seconds.`}>
      <Badge variant={variant} className="gap-1.5">
        <span
          className={cn(
            'h-2 w-2 rounded-full',
            state === 'Connected' && 'bg-emerald-500',
            state === 'Checking' && 'bg-sky-500 animate-pulse',
            state === 'Unavailable' && 'bg-red-500',
          )}
          aria-hidden="true"
        />
        {state}
      </Badge>
    </Tooltip>
  )
}

export interface TopNavigationProps {
  onMenuClick: () => void
}

export function TopNavigation({ onMenuClick }: TopNavigationProps) {
  const location = useLocation()
  const env = getEnv()
  const pageTitle = usePageTitle(location.pathname)

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
            <ApiStatusIndicator />
          </div>
          <h1 className="truncate text-lg font-semibold text-slate-900">{pageTitle}</h1>
        </div>

        <div className="hidden text-right sm:block">
          <p className="text-sm font-medium text-slate-900">RM User</p>
          <p className="text-xs text-slate-500">RM-01</p>
        </div>
      </div>
    </header>
  )
}

export function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  const location = useLocation()

  return (
    <nav aria-label="Main navigation" className="flex h-full flex-col px-3 py-4">
      <div className="mb-6 px-3">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">RetainAI</p>
        <p className="text-sm text-slate-600">RM Dashboard</p>
      </div>
      <ul className="space-y-1">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon
          const active =
            item.to === '/'
              ? location.pathname === '/'
              : location.pathname.startsWith(item.to)

          return (
            <li key={item.to}>
              <Link
                to={item.to}
                onClick={onNavigate}
                className={cn(
                  'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400',
                  active
                    ? 'bg-slate-900 text-white'
                    : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900',
                )}
                aria-current={active ? 'page' : undefined}
              >
                <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
                <span className="flex-1">{item.label}</span>
                {!item.ready ? (
                  <span className="text-[10px] font-normal text-slate-400">Soon</span>
                ) : null}
              </Link>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}

export { NAV_ITEMS }
