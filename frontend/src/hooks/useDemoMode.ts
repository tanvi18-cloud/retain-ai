import { useCallback, useEffect, useSyncExternalStore } from 'react'

import { getEnv } from '../api/env'

const STORAGE_KEY = 'retainai:demo-mode'
const EVENT_NAME = 'retainai:demo-mode-change'

type Override = 'on' | 'off' | null

function readOverride(): Override {
  if (typeof window === 'undefined') return null
  try {
    const value = window.localStorage.getItem(STORAGE_KEY)
    if (value === 'on' || value === 'off') return value
  } catch {
    // ignore storage errors (private mode, etc.)
  }
  return null
}

function writeOverride(next: Override): void {
  if (typeof window === 'undefined') return
  try {
    if (next === null) {
      window.localStorage.removeItem(STORAGE_KEY)
    } else {
      window.localStorage.setItem(STORAGE_KEY, next)
    }
    window.dispatchEvent(new Event(EVENT_NAME))
  } catch {
    // ignore
  }
}

function readUrlOverride(): Override {
  if (typeof window === 'undefined') return null
  const params = new URLSearchParams(window.location.search)
  const raw = params.get('demo')
  if (raw === null) return null
  if (raw === '1' || raw === 'true' || raw === 'on') return 'on'
  if (raw === '0' || raw === 'false' || raw === 'off') return 'off'
  return null
}

function subscribe(callback: () => void): () => void {
  const handler = () => callback()
  window.addEventListener(EVENT_NAME, handler)
  window.addEventListener('storage', handler)
  return () => {
    window.removeEventListener(EVENT_NAME, handler)
    window.removeEventListener('storage', handler)
  }
}

function getSnapshot(): boolean {
  const envDefault = getEnv().demoMode
  const override = readOverride()
  if (override === 'on') return true
  if (override === 'off') return false
  return envDefault
}

function getServerSnapshot(): boolean {
  return getEnv().demoMode
}

export interface UseDemoModeResult {
  demoMode: boolean
  envDefault: boolean
  setDemoMode: (next: boolean) => void
  toggleDemoMode: () => void
  resetToEnv: () => void
}

/**
 * Reactive demo-mode hook.
 *
 * Resolution order (highest priority first):
 *   1. `?demo=1` / `?demo=0` URL query — applied once on mount, persisted to localStorage.
 *   2. `localStorage['retainai:demo-mode']` — set by the UI toggle.
 *   3. `VITE_DEMO_MODE` env variable (default `true`).
 */
export function useDemoMode(): UseDemoModeResult {
  const demoMode = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot)
  const envDefault = getEnv().demoMode

  // One-time: honour ?demo=1/0 by writing it into localStorage so it survives navigation.
  useEffect(() => {
    const urlOverride = readUrlOverride()
    if (urlOverride) writeOverride(urlOverride)
  }, [])

  const setDemoMode = useCallback(
    (next: boolean) => {
      // If the requested value matches the env default, clear the override so it reverts cleanly.
      if (next === envDefault) {
        writeOverride(null)
      } else {
        writeOverride(next ? 'on' : 'off')
      }
    },
    [envDefault],
  )

  const toggleDemoMode = useCallback(() => {
    setDemoMode(!getSnapshot())
  }, [setDemoMode])

  const resetToEnv = useCallback(() => writeOverride(null), [])

  return { demoMode, envDefault, setDemoMode, toggleDemoMode, resetToEnv }
}
