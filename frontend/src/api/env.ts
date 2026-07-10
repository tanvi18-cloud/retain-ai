interface AppEnv {
  apiBaseUrl: string
  appName: string
  appVersion: string
  useMockData: boolean
}

function readEnv(key: string): string | undefined {
  return import.meta.env[key] as string | undefined
}

function requireEnv(key: string): string {
  const value = readEnv(key)
  if (!value || value.trim() === '') {
    throw new Error(`Missing required environment variable: ${key}`)
  }
  return value.trim()
}

function parseBoolean(value: string): boolean {
  return value.toLowerCase() === 'true'
}

let cachedEnv: AppEnv | null = null

export function getEnv(): AppEnv {
  if (cachedEnv) return cachedEnv

  cachedEnv = {
    apiBaseUrl: requireEnv('VITE_API_BASE_URL'),
    appName: requireEnv('VITE_APP_NAME'),
    appVersion: requireEnv('VITE_APP_VERSION'),
    useMockData: parseBoolean(requireEnv('VITE_USE_MOCK_DATA')),
  }

  return cachedEnv
}

export const RM_USER = {
  id: 'RM-01',
  name: 'RM User',
} as const
