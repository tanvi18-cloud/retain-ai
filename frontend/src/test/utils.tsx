import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, type RenderOptions } from '@testing-library/react'
import { MemoryRouter, Route, Routes, type MemoryRouterProps } from 'react-router-dom'
import { Toaster } from 'sonner'
import type { ReactElement, ReactNode } from 'react'

import { AlertsWebSocketProvider } from '../hooks/useAlertsWebSocket'

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })
}

interface ProvidersProps {
  children: ReactNode
  route?: string
  routerProps?: MemoryRouterProps
  withRoutes?: boolean
  /** When false, skip WebSocket provider (e.g. App renders AppShell which includes it). */
  enableWebSocket?: boolean
  /** When false, skip Sonner Toaster (rare — most tests need it for toast assertions). */
  enableToaster?: boolean
}

function Providers({
  children,
  route = '/',
  routerProps,
  withRoutes,
  enableWebSocket = true,
  enableToaster = true,
}: ProvidersProps) {
  const client = createTestQueryClient()
  const routed = (
    <MemoryRouter initialEntries={[route]} {...routerProps}>
      {withRoutes ? (
        <Routes>
          <Route path="/customers/:customerId" element={children} />
          <Route path="*" element={children} />
        </Routes>
      ) : (
        children
      )}
      {enableToaster ? <Toaster /> : null}
    </MemoryRouter>
  )

  return (
    <QueryClientProvider client={client}>
      {enableWebSocket ? (
        <AlertsWebSocketProvider>{routed}</AlertsWebSocketProvider>
      ) : (
        routed
      )}
    </QueryClientProvider>
  )
}

export function renderWithProviders(
  ui: ReactElement,
  options?: RenderOptions & {
    route?: string
    routerProps?: MemoryRouterProps
    withRoutes?: boolean
    enableWebSocket?: boolean
    enableToaster?: boolean
  },
) {
  const { route, routerProps, withRoutes, enableWebSocket, enableToaster, ...renderOptions } =
    options ?? {}
  return render(ui, {
    wrapper: ({ children }) => (
      <Providers
        route={route}
        routerProps={routerProps}
        withRoutes={withRoutes}
        enableWebSocket={enableWebSocket}
        enableToaster={enableToaster}
      >
        {children}
      </Providers>
    ),
    ...renderOptions,
  })
}
