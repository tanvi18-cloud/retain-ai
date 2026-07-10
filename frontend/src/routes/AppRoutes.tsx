import { Navigate, Route, Routes } from 'react-router-dom'

import { AppShell } from '../components/layout/AppShell'
import { ComingSoonPage } from '../pages/ComingSoonPage'
import { CustomerDetailsPage } from '../pages/CustomerDetailsPage'
import { CustomersPage } from '../pages/CustomersPage'
import { NotFoundPage } from '../pages/NotFoundPage'
import { PortfolioPage } from '../pages/PortfolioPage'

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<PortfolioPage />} />
        <Route path="customers" element={<CustomersPage />} />
        <Route path="customers/:customerId" element={<CustomerDetailsPage />} />
        <Route path="alerts" element={<ComingSoonPage title="Alerts" />} />
        <Route path="copilot" element={<ComingSoonPage title="RM Copilot" />} />
        <Route path="simulator" element={<ComingSoonPage title="Event Simulator" />} />
        <Route path="system" element={<ComingSoonPage title="System Status" />} />
        <Route path="404" element={<NotFoundPage />} />
        <Route path="*" element={<Navigate to="/404" replace />} />
      </Route>
    </Routes>
  )
}
