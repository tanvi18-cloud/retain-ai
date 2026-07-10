import { useState } from 'react'
import { Outlet } from 'react-router-dom'

import { AlertsWebSocketProvider } from '../../hooks/useAlertsWebSocket'
import { Drawer } from '../ui/Drawer'
import { MobileNavigation } from './MobileNavigation'
import { Sidebar } from './Sidebar'
import { TopNavigation } from './TopNavigation'

export function AppShell() {
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <AlertsWebSocketProvider>
      <div className="min-h-svh bg-slate-50 text-slate-900">
        <div className="flex min-h-svh">
          <aside className="hidden w-64 shrink-0 border-r border-slate-200 bg-white lg:block">
            <Sidebar />
          </aside>

          <Drawer open={mobileOpen} onClose={() => setMobileOpen(false)} title="Navigation">
            <Sidebar onNavigate={() => setMobileOpen(false)} />
          </Drawer>

          <div className="flex min-w-0 flex-1 flex-col">
            <TopNavigation onMenuClick={() => setMobileOpen(true)} />
            <main className="flex-1 px-4 py-6 pb-20 lg:px-6 lg:pb-6">
              <Outlet />
            </main>
            <MobileNavigation />
          </div>
        </div>
      </div>
    </AlertsWebSocketProvider>
  )
}
