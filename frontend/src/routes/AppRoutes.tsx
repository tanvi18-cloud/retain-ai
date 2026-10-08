import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'

import { AppShell } from '../components/layout/AppShell'
import { RouteSkeleton } from '../components/layout/RouteSkeleton'
import { useDemoMode } from '../hooks/useDemoMode'
import { CustomersPage } from '../pages/CustomersPage'
import { DemoDashboardPage } from '../pages/DemoDashboardPage'
import { NotFoundPage } from '../pages/NotFoundPage'
import { PortfolioPage } from '../pages/PortfolioPage'

const CustomerDetailsPage = lazy(() =>
  import('../pages/CustomerDetailsPage').then((m) => ({ default: m.CustomerDetailsPage })),
)
const AlertsPage = lazy(() =>
  import('../pages/AlertsPage').then((m) => ({ default: m.AlertsPage })),
)
const ChatPage = lazy(() =>
  import('../pages/ChatPage').then((m) => ({ default: m.ChatPage })),
)
const SimulatorPage = lazy(() =>
  import('../pages/SimulatorPage').then((m) => ({ default: m.SimulatorPage })),
)
const SystemStatusPage = lazy(() =>
  import('../pages/SystemStatusPage').then((m) => ({ default: m.SystemStatusPage })),
)

function LazyRoute({ children }: { children: React.ReactNode }) {
  return <Suspense fallback={<RouteSkeleton />}>{children}</Suspense>
}

export function AppRoutes() {
  const { demoMode } = useDemoMode()

  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={demoMode ? <DemoDashboardPage /> : <PortfolioPage />} />
        <Route path="portfolio" element={<PortfolioPage />} />
        <Route path="customers" element={<CustomersPage />} />
        <Route
          path="customers/:customerId"
          element={
            <LazyRoute>
              <CustomerDetailsPage />
            </LazyRoute>
          }
        />
        <Route
          path="alerts"
          element={
            <LazyRoute>
              <AlertsPage />
            </LazyRoute>
          }
        />
        <Route
          path="chat"
          element={
            <LazyRoute>
              <ChatPage />
            </LazyRoute>
          }
        />
        <Route path="copilot" element={<Navigate to="/chat" replace />} />
        <Route
          path="simulator"
          element={
            <LazyRoute>
              <SimulatorPage />
            </LazyRoute>
          }
        />
        <Route
          path="system"
          element={
            <LazyRoute>
              <SystemStatusPage />
            </LazyRoute>
          }
        />
        <Route path="404" element={<NotFoundPage />} />
        <Route path="*" element={<Navigate to="/404" replace />} />
      </Route>
    </Routes>
  )
}
