import { get } from './client'
import type { AlertSummary, PaginatedResponse } from '../types/api'
import type { PortfolioCustomerRow, PortfolioCustomersParams, PortfolioSummary } from '../types/portfolio'

export function fetchPortfolioSummary() {
  return get<PortfolioSummary>('/portfolio/summary')
}

export function fetchPortfolioCustomers(params: PortfolioCustomersParams = {}) {
  return get<PaginatedResponse<PortfolioCustomerRow>>('/portfolio/customers', { ...params })
}

export function fetchRecentAlerts(limit = 5) {
  return get<PaginatedResponse<AlertSummary>>('/alerts', {
    page: 1,
    page_size: limit,
    sort_order: 'desc',
  })
}
