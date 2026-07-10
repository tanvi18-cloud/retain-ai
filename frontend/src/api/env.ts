interface AppEnv {
  apiBaseUrl: string
  wsBaseUrl: string
  appName: string
  appVersion: string
  useMockData: boolean
  rmId: string
  rmName: string
  enableSimulator: boolean
  enableSystemPage: boolean
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

function parseBoolean(value: string, defaultValue = false): boolean {
  if (!value || value.trim() === '') return defaultValue
  return value.toLowerCase() === 'true'
}

function deriveWsUrl(apiBaseUrl: string): string {
  const url = new URL(apiBaseUrl)
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
  url.pathname = '/ws/alerts'
  url.search = ''
  url.hash = ''
  return url.toString()
}

let cachedEnv: AppEnv | null = null

export function getEnv(): AppEnv {
  if (cachedEnv) return cachedEnv

  const apiBaseUrl = requireEnv('VITE_API_BASE_URL')
  const wsExplicit = readEnv('VITE_WS_BASE_URL')?.trim()
  const wsBaseUrl = wsExplicit && wsExplicit.length > 0 ? wsExplicit : deriveWsUrl(apiBaseUrl)

  cachedEnv = {
    apiBaseUrl,
    wsBaseUrl,
    appName: requireEnv('VITE_APP_NAME'),
    appVersion: requireEnv('VITE_APP_VERSION'),
    useMockData: parseBoolean(requireEnv('VITE_USE_MOCK_DATA')),
    rmId: requireEnv('VITE_RM_ID'),
    rmName: requireEnv('VITE_RM_NAME'),
    enableSimulator: parseBoolean(readEnv('VITE_ENABLE_SIMULATOR') ?? 'true', true),
    enableSystemPage: parseBoolean(readEnv('VITE_ENABLE_SYSTEM_PAGE') ?? 'true', true),
  }

  return cachedEnv
}

export function getRmUser() {
  const env = getEnv()
  return { id: env.rmId, name: env.rmName } as const
}

/** @deprecated Use getRmUser() */
export const RM_USER = {
  get id() {
    return getEnv().rmId
  },
  get name() {
    return getEnv().rmName
  },
}
