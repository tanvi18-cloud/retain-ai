import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, type RenderOptions } from '@testing-library/react'
import { MemoryRouter, Route, Routes, type MemoryRouterProps } from 'react-router-dom'
import { Toaster } from 'sonner'
import type { ReactElement, ReactNode } from 'react'

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
}

function Providers({ children, route = '/', routerProps, withRoutes }: ProvidersProps) {
  const client = createTestQueryClient()
  return (
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[route]} {...routerProps}>
        {withRoutes ? (
          <Routes>
            <Route path="/customers/:customerId" element={children} />
            <Route path="*" element={children} />
          </Routes>
        ) : (
          children
        )}
        <Toaster />
      </MemoryRouter>
    </QueryClientProvider>
  )
}

export function renderWithProviders(
  ui: ReactElement,
  options?: RenderOptions & {
    route?: string
    routerProps?: MemoryRouterProps
    withRoutes?: boolean
  },
) {
  const { route, routerProps, withRoutes, ...renderOptions } = options ?? {}
  return render(ui, {
    wrapper: ({ children }) => (
      <Providers route={route} routerProps={routerProps} withRoutes={withRoutes}>
        {children}
      </Providers>
    ),
    ...renderOptions,
  })
}
