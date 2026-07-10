import { get } from './client'
import type { HealthResponse } from '../types/api'

export function fetchHealth() {
  return get<HealthResponse>('/health')
}
