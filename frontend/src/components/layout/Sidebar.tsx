import { Link, useLocation } from 'react-router-dom'
import {
  Activity,
  Bell,
  Bot,
  LayoutDashboard,
  Users,
  Zap,
} from 'lucide-react'

import { getEnv } from '../../api/env'
import { cn } from '../../utils/cn'

import type { LucideIcon } from 'lucide-react'

type NavItem = {
  to: string
  label: string
  icon: LucideIcon
  feature?: 'simulator' | 'system'
}

export const NAV_ITEMS: NavItem[] = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/customers', label: 'Customers', icon: Users },
  { to: '/alerts', label: 'Alerts', icon: Bell },
  { to: '/chat', label: 'RM Copilot', icon: Bot },
  { to: '/simulator', label: 'Event Simulator', icon: Zap, feature: 'simulator' },
  { to: '/system', label: 'System Status', icon: Activity, feature: 'system' },
]

export interface SidebarProps {
  onNavigate?: () => void
}

export function Sidebar({ onNavigate }: SidebarProps) {
  const location = useLocation()
  const env = getEnv()

  const visibleItems = NAV_ITEMS.filter((item) => {
    if (item.feature === 'simulator') return env.enableSimulator
    if (item.feature === 'system') return env.enableSystemPage
    return true
  })

  return (
    <nav aria-label="Main navigation" className="flex h-full flex-col px-3 py-4">
      <div className="mb-6 px-3">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">{env.appName}</p>
        <p className="text-sm text-slate-600">RM Dashboard</p>
      </div>
      <ul className="space-y-1">
        {visibleItems.map((item) => {
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
                  'relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400',
                  active
                    ? 'bg-slate-100 text-slate-900'
                    : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900',
                )}
                aria-current={active ? 'page' : undefined}
              >
                {active ? (
                  <span
                    aria-hidden="true"
                    className="absolute inset-y-1.5 left-0 w-0.5 rounded-r-full bg-emerald-500"
                  />
                ) : null}
                <Icon
                  className={cn(
                    'h-4 w-4 shrink-0',
                    active ? 'text-emerald-600' : 'text-slate-500',
                  )}
                  aria-hidden="true"
                />
                <span className="flex-1">{item.label}</span>
              </Link>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}
