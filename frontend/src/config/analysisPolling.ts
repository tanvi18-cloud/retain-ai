export const ANALYSIS_POLL_MAX_ATTEMPTS = 60

const PRODUCTION_POLL_INTERVAL_MS = 2000
const TEST_POLL_INTERVAL_MS = 10

export function getAnalysisPollIntervalMs(): number {
  return import.meta.env.MODE === 'test' ? TEST_POLL_INTERVAL_MS : PRODUCTION_POLL_INTERVAL_MS
}
