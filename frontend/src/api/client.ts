import type { ApiErrorResponse } from '../types/api'
import { getEnv } from './env'

export type HttpMethod = 'GET' | 'POST' | 'PATCH'

export type QueryParams = Record<string, string | number | boolean | null | undefined>

export interface RequestOptions {
  method?: HttpMethod
  body?: unknown
  params?: QueryParams
  timeoutMs?: number
  signal?: AbortSignal
}

export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly details: Record<string, unknown>

  constructor(status: number, payload: ApiErrorResponse['error']) {
    super(payload.message)
    this.name = 'ApiError'
    this.status = status
    this.code = payload.code
    this.details = payload.details
  }

  get isNotFound(): boolean {
    return this.status === 404
  }

  get isValidation(): boolean {
    return this.status === 422
  }

  get isConflict(): boolean {
    return this.status === 409
  }
}

const DEFAULT_TIMEOUT_MS = 30_000

function buildUrl(path: string, params?: QueryParams): string {
  const base = getEnv().apiBaseUrl.replace(/\/$/, '')
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  const url = new URL(`${base}${normalizedPath}`)

  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null && value !== '') {
        url.searchParams.set(key, String(value))
      }
    }
  }

  return url.toString()
}

async function parseErrorResponse(response: Response): Promise<ApiError> {
  try {
    const payload = (await response.json()) as ApiErrorResponse
    if (payload?.error?.message) {
      return new ApiError(response.status, payload.error)
    }
  } catch {
    // fall through to generic error
  }

  const fallbackMessages: Record<number, string> = {
    400: 'The request could not be processed.',
    404: 'The requested resource was not found.',
    409: 'This action is not allowed in the current state.',
    422: 'The request failed validation.',
    500: 'The server encountered an error. Please try again.',
  }

  return new ApiError(response.status, {
    code: `HTTP_${response.status}`,
    message: fallbackMessages[response.status] ?? 'An unexpected error occurred.',
    details: {},
  })
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, params, timeoutMs = DEFAULT_TIMEOUT_MS, signal } = options
  const controller = new AbortController()
  const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs)

  const onAbort = () => controller.abort()
  signal?.addEventListener('abort', onAbort)

  try {
    const response = await fetch(buildUrl(path, params), {
      method,
      headers: body !== undefined ? { 'Content-Type': 'application/json' } : undefined,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    })

    if (!response.ok) {
      throw await parseErrorResponse(response)
    }

    if (response.status === 204) {
      return undefined as T
    }

    return (await response.json()) as T
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError(0, {
        code: 'TIMEOUT',
        message: 'The request timed out. Please check your connection and try again.',
        details: {},
      })
    }
    throw new ApiError(0, {
      code: 'NETWORK_ERROR',
      message: 'Unable to reach the RetainAI API. Check that the backend is running.',
      details: {},
    })
  } finally {
    window.clearTimeout(timeoutId)
    signal?.removeEventListener('abort', onAbort)
  }
}

export function get<T>(path: string, params?: QueryParams): Promise<T> {
  return apiRequest<T>(path, { method: 'GET', params })
}

export function post<T>(path: string, body?: unknown, params?: QueryParams): Promise<T> {
  return apiRequest<T>(path, { method: 'POST', body, params })
}

export function patch<T>(path: string, body?: unknown, params?: QueryParams): Promise<T> {
  return apiRequest<T>(path, { method: 'PATCH', body, params })
}
