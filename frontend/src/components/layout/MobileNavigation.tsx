import { Link, useLocation } from 'react-router-dom'
import { Bell, Bot, LayoutDashboard, Users } from 'lucide-react'

import { cn } from '../../utils/cn'

const MOBILE_ITEMS = [
  { to: '/', label: 'Portfolio', icon: LayoutDashboard },
  { to: '/customers', label: 'Customers', icon: Users },
  { to: '/alerts', label: 'Alerts', icon: Bell },
  { to: '/chat', label: 'Copilot', icon: Bot },
] as const

export function MobileNavigation() {
  const location = useLocation()

  return (
    <nav
      aria-label="Mobile quick navigation"
      className="fixed inset-x-0 bottom-0 z-40 border-t border-slate-200 bg-white/95 backdrop-blur lg:hidden"
    >
      <ul className="grid grid-cols-4">
        {MOBILE_ITEMS.map((item) => {
          const Icon = item.icon
          const active =
            item.to === '/'
              ? location.pathname === '/'
              : location.pathname.startsWith(item.to)

          return (
            <li key={item.to}>
              <Link
                to={item.to}
                className={cn(
                  'flex min-h-14 flex-col items-center justify-center gap-1 px-2 py-2 text-xs font-medium',
                  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-slate-400',
                  active ? 'text-slate-900' : 'text-slate-500',
                )}
                aria-current={active ? 'page' : undefined}
              >
                <Icon className="h-5 w-5" aria-hidden="true" />
                <span>{item.label}</span>
              </Link>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}
