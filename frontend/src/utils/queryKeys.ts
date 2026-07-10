export const queryKeys = {
  health: ['health'] as const,
  portfolio: {
    summary: ['portfolio', 'summary'] as const,
    customers: (params: Record<string, unknown>) =>
      ['portfolio', 'customers', params] as const,
  },
  customers: {
    list: (params: Record<string, unknown>) => ['customers', 'list', params] as const,
    detail: (id: string) => ['customers', 'detail', id] as const,
    customer360: (id: string) => ['customers', '360', id] as const,
  },
  recommendations: {
    list: (params: Record<string, unknown>) =>
      ['recommendations', 'list', params] as const,
    detail: (id: string) => ['recommendations', 'detail', id] as const,
  },
  analysis: {
    execution: (id: string) => ['analysis', 'execution', id] as const,
    rulesOnly: (customerId: string) => ['analysis', 'rules-only', customerId] as const,
  },
  alerts: {
    list: (params: Record<string, unknown>) => ['alerts', 'list', params] as const,
  },
}
