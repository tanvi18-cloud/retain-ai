import { useState } from 'react'
import { Outlet } from 'react-router-dom'

import { Drawer } from '../ui/Drawer'
import { Sidebar } from './Sidebar'
import { TopNavigation } from './TopNavigation'

export function AppShell() {
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
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
          <main className="flex-1 px-4 py-6 lg:px-6">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  )
}

export function MobileNavigation() {
  return null
}
