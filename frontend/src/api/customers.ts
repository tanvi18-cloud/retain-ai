import { get } from './client'
import type { PaginatedResponse } from '../types/api'
import type { CustomerDetail, CustomerSummary } from '../types/customer'
import type { Customer360 } from '../types/customer'

export interface CustomersListParams {
  page?: number
  page_size?: number
  segment?: string
  search?: string
  sort_by?: 'customer_id' | 'full_name' | 'relationship_start_date' | 'estimated_annual_value'
  sort_order?: 'asc' | 'desc'
}

export function fetchCustomers(params: CustomersListParams = {}) {
  return get<PaginatedResponse<CustomerSummary>>('/customers', { ...params })
}

export function fetchCustomer(customerId: string) {
  return get<CustomerDetail>(`/customers/${customerId}`)
}

export function fetchCustomer360(customerId: string) {
  return get<Customer360>(`/customers/${customerId}/360`)
}

export type { Customer360, CustomerDetail, CustomerSummary }
