import { ShieldCheck } from 'lucide-react'

import { cn } from './lib/utils'

function App() {
  return (
    <main
      className={cn(
        'flex min-h-svh flex-col items-center justify-center bg-slate-950 px-6 text-slate-100',
      )}
    >
      <div className="flex max-w-lg flex-col items-center gap-4 text-center">
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-500/10 ring-1 ring-emerald-500/30">
          <ShieldCheck aria-hidden="true" className="h-7 w-7 text-emerald-400" />
        </div>
        <h1 className="text-4xl font-semibold tracking-tight">RetainAI</h1>
        <p className="text-base text-slate-400">
          Customer-retention copilot for retail banking Relationship Managers.
        </p>
        <p className="text-sm text-slate-500">Scaffold ready — business features coming soon.</p>
      </div>
    </main>
  )
}

export default App
