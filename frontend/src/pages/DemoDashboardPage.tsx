import { useEffect, useMemo, useState } from 'react'
import {
  Activity,
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  Bot,
  Building2,
  CheckCircle2,
  CreditCard,
  Minus,
  Phone,
  Radar,
  Shield,
  ShieldAlert,
  Sparkles,
  TrendingUp,
  Users,
  Wallet,
  X,
  Zap,
} from 'lucide-react'
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  RadialBar,
  RadialBarChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip as RechartsTooltip,
  XAxis,
  YAxis,
  ZAxis,
} from 'recharts'

import { getEnv, getRmUser } from '../api/env'
import {
  agents,
  benchmarkKpis,
  channelPerformance,
  cohortRetention,
  customerDossiers,
  headlineKpis,
  liveAlerts,
  matrixPoints,
  modelDrift14d,
  modelMetrics,
  priorityCustomers,
  retentionTrend,
  saveFunnel,
  segmentPerformance,
  type BenchmarkKpi,
  type CrossSellOffer,
  type CustomerDossier,
  type HeadlineKpi,
} from '../data/demoDashboardData'
import { useDocumentTitle } from '../hooks/useDocumentTitle'
import type { RecommendationDecision } from '../types/api'
import { cn } from '../utils/cn'

const DECISION_COLORS: Record<RecommendationDecision, string> = {
  RETAIN: '#e11d48',
  REVIEW: '#f59e0b',
  MONITOR: '#10b981',
  NO_ACTION: '#94a3b8',
}

const DECISION_LABELS: Record<RecommendationDecision, string> = {
  RETAIN: 'Retain',
  REVIEW: 'RM review',
  MONITOR: 'Monitor',
  NO_ACTION: 'No action',
}

const SEGMENT_LABELS: Record<string, string> = {
  PRIVATE: 'Private',
  PRIORITY: 'Priority',
  MASS_AFFLUENT: 'Mass affluent',
  STANDARD: 'Standard',
}

const SEGMENT_ACCENTS: Record<string, string> = {
  PRIVATE: 'from-slate-900 to-slate-700',
  PRIORITY: 'from-emerald-700 to-emerald-500',
  MASS_AFFLUENT: 'from-emerald-500 to-teal-400',
  STANDARD: 'from-slate-500 to-slate-400',
}

// ────────────────────────────────────────────────────────────────────────────
// Page
// ────────────────────────────────────────────────────────────────────────────

export function DemoDashboardPage() {
  const env = getEnv()
  const rm = getRmUser()
  useDocumentTitle(`${env.appName} — Executive Dashboard`)

  const [selectedCustomerId, setSelectedCustomerId] = useState<string | null>(null)
  const selectedDossier = selectedCustomerId
    ? (customerDossiers[selectedCustomerId] ?? null)
    : null

  const totalFunnelStart = saveFunnel[0]?.count ?? 1
  const totalFunnelEnd = saveFunnel[saveFunnel.length - 1]?.count ?? 0
  const overallSavePct = Math.round((totalFunnelEnd / totalFunnelStart) * 100)

  return (
    <div className="space-y-6">
      <Hero rmName={rm.name} />

      <BenchmarkKpiRow kpis={benchmarkKpis} />

      <div className="grid gap-6 xl:grid-cols-[2fr_1fr]">
        <RetentionTrendCard />
        <AgentActivityCard />
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <SaveFunnelCard overallSavePct={overallSavePct} />
        <ChannelPerformanceCard />
        <ModelPerformanceCard />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.6fr_1fr]">
        <RiskValueMatrixCard />
        <PriorityRailCard onSelectCustomer={setSelectedCustomerId} />
      </div>

      <CohortRetentionCard />

      <div className="grid gap-6 xl:grid-cols-[1.4fr_1fr]">
        <SegmentPerformanceCard />
        <GuardrailsCard />
      </div>

      <ComplianceStrip />

      {selectedDossier ? (
        <CustomerDossierModal
          dossier={selectedDossier}
          onClose={() => setSelectedCustomerId(null)}
        />
      ) : null}
    </div>
  )
}

// ────────────────────────────────────────────────────────────────────────────
// Hero
// ────────────────────────────────────────────────────────────────────────────

function Hero({ rmName }: { rmName: string }) {
  const now = new Date()
  const dateLabel = now.toLocaleDateString('en-IN', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
  })
  const timeLabel = now.toLocaleTimeString('en-IN', {
    hour: '2-digit',
    minute: '2-digit',
  })

  return (
    <section className="relative isolate overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      {/* very subtle emerald accent in the top-right corner (no blue) */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -right-24 -top-24 h-64 w-64 rounded-full bg-emerald-100/70 blur-3xl"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-emerald-400/60 to-transparent"
      />

      <div className="relative grid gap-6 p-6 lg:grid-cols-[1.3fr_1fr] lg:p-8">
        {/* Left: brand + welcome + headline */}
        <div className="flex flex-col gap-5">
          <div className="flex items-center gap-3">
            <div className="relative flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-600 to-teal-500 shadow-sm">
              <Sparkles className="h-5 w-5 text-white" aria-hidden="true" />
            </div>
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                RetainAI · Agentic Retention Copilot
              </p>
              <p className="text-sm font-medium text-slate-900">
                {dateLabel} · {timeLabel} IST
              </p>
            </div>
          </div>

          <div className="space-y-2">
            <h1 className="text-balance text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">
              Good morning, {rmName}.
            </h1>
            <p className="max-w-xl text-sm text-slate-600">
              <span className="font-semibold text-slate-900">8 priority customers</span> need
              attention today · <span className="font-semibold text-emerald-700">₹46.8 Cr</span>{' '}
              retained year-to-date through agent-assisted interventions.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2 pt-1">
            <SoftPill tone="emerald" icon={<LiveDot />}>
              All systems operational
            </SoftPill>
            <SoftPill tone="slate">4 agents · Qwen3-8B</SoftPill>
            <SoftPill tone="slate">Guardrails · policy v4.2</SoftPill>
            <SoftPill tone="slate">Audit trail · 100%</SoftPill>
          </div>
        </div>

        {/* Right: 2×2 KPI tiles with sparklines */}
        <div className="grid grid-cols-2 gap-3">
          {headlineKpis.map((k, i) => (
            <HeroKpiTile key={k.label} kpi={k} highlighted={i === 3} />
          ))}
        </div>
      </div>
    </section>
  )
}

function LiveDot() {
  return (
    <span className="relative flex h-1.5 w-1.5">
      <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-500 opacity-70" />
      <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-emerald-500" />
    </span>
  )
}

function SoftPill({
  children,
  tone,
  icon,
}: {
  children: React.ReactNode
  tone: 'emerald' | 'slate'
  icon?: React.ReactNode
}) {
  const classes = {
    emerald: 'border-emerald-200 bg-emerald-50 text-emerald-700',
    slate: 'border-slate-200 bg-slate-50 text-slate-600',
  } as const
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-medium',
        classes[tone],
      )}
    >
      {icon}
      {children}
    </span>
  )
}

function LivePill() {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-emerald-700">
      <LiveDot />
      Live
    </span>
  )
}

function HeroKpiTile({ kpi, highlighted }: { kpi: HeadlineKpi; highlighted: boolean }) {
  const first = kpi.trend[0] ?? 0
  const last = kpi.trend[kpi.trend.length - 1] ?? 0
  const deltaPct = first === 0 ? 0 : ((last - first) / first) * 100
  const chartData = kpi.trend.map((v, i) => ({ i, v }))

  return (
    <div
      className={cn(
        'relative overflow-hidden rounded-xl border p-4 transition',
        highlighted
          ? 'border-emerald-200 bg-emerald-50/60'
          : 'border-slate-200 bg-white hover:border-emerald-200',
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
          {kpi.label}
        </p>
        <span className="inline-flex items-center gap-0.5 rounded-full border border-emerald-200 bg-emerald-50 px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wider text-emerald-700">
          <ArrowUpRight className="h-2.5 w-2.5" aria-hidden="true" />
          {deltaPct >= 10 ? `+${deltaPct.toFixed(0)}%` : `+${deltaPct.toFixed(1)}%`}
        </span>
      </div>
      <p
        className={cn(
          'mt-1 text-xl font-semibold tracking-tight sm:text-2xl',
          highlighted ? 'text-emerald-700' : 'text-slate-900',
        )}
      >
        {kpi.value}
      </p>
      <p className="line-clamp-1 text-[11px] text-slate-500">{kpi.caption}</p>
      <div className="mt-1.5 h-7 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 2, right: 0, bottom: 0, left: 0 }}>
            <defs>
              <linearGradient id={`spark-${kpi.label.replace(/\W/g, '')}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#10b981" stopOpacity={0.45} />
                <stop offset="100%" stopColor="#10b981" stopOpacity={0} />
              </linearGradient>
            </defs>
            <Area
              type="monotone"
              dataKey="v"
              stroke="#059669"
              strokeWidth={1.5}
              fill={`url(#spark-${kpi.label.replace(/\W/g, '')})`}
              dot={false}
              isAnimationActive={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

// ────────────────────────────────────────────────────────────────────────────
// Benchmark KPI row
// ────────────────────────────────────────────────────────────────────────────

function BenchmarkKpiRow({ kpis }: { kpis: BenchmarkKpi[] }) {
  return (
    <section aria-labelledby="benchmark-heading">
      <div className="mb-4 flex items-end justify-between gap-3">
        <div>
          <h2 id="benchmark-heading" className="text-lg font-semibold text-slate-900">
            Industry benchmark scorecard
          </h2>
          <p className="text-sm text-slate-500">
            RetainAI vs. retail-banking industry averages (Bain · McKinsey · J.D. Power · Qualtrics)
          </p>
        </div>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
        {kpis.map((k) => (
          <BenchmarkCard key={k.label} kpi={k} />
        ))}
      </div>
    </section>
  )
}

function BenchmarkCard({ kpi }: { kpi: BenchmarkKpi }) {
  const intentClass =
    kpi.deltaIntent === 'good'
      ? 'text-emerald-600'
      : kpi.deltaIntent === 'bad'
        ? 'text-rose-600'
        : 'text-slate-500'

  const Icon =
    kpi.deltaDirection === 'up'
      ? ArrowUpRight
      : kpi.deltaDirection === 'down'
        ? ArrowDownRight
        : Minus

  return (
    <article className="group relative overflow-hidden rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:border-emerald-200 hover:shadow-md">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-x-0 -top-px h-px bg-gradient-to-r from-transparent via-emerald-400/60 to-transparent opacity-0 transition group-hover:opacity-100"
      />
      <p className="text-[11px] font-medium uppercase tracking-wider text-slate-500">
        {kpi.label}
      </p>
      <p className="mt-2 text-3xl font-semibold tracking-tight text-slate-900">{kpi.value}</p>
      <div className={cn('mt-1 inline-flex items-center gap-1 text-xs font-medium', intentClass)}>
        <Icon className="h-3.5 w-3.5" aria-hidden="true" />
        {kpi.deltaLabel}
      </div>
      <p className="mt-3 text-xs text-slate-500">{kpi.description}</p>
      <p className="mt-2 text-[11px] font-medium text-slate-400">{kpi.industryBenchmark}</p>
    </article>
  )
}

// ────────────────────────────────────────────────────────────────────────────
// Retention trend
// ────────────────────────────────────────────────────────────────────────────

function RetentionTrendCard() {
  const totalSaved = retentionTrend.reduce((s, p) => s + p.saved, 0)
  const totalRevenueSaved = retentionTrend
    .reduce((s, p) => s + p.revenueSavedCr, 0)
    .toFixed(1)

  return (
    <article className="relative overflow-hidden rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <header className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-slate-900">
            Retention performance · last 12 months
          </h3>
          <p className="mt-1 text-sm text-slate-500">
            At-risk customers detected vs. successfully retained after RM intervention.
          </p>
        </div>
        <div className="flex gap-6 text-right">
          <div>
            <p className="text-[11px] uppercase tracking-wider text-slate-500">Saved</p>
            <p className="text-xl font-semibold text-slate-900">{totalSaved.toLocaleString('en-IN')}</p>
          </div>
          <div>
            <p className="text-[11px] uppercase tracking-wider text-slate-500">Revenue</p>
            <p className="text-xl font-semibold text-emerald-600">₹{totalRevenueSaved} Cr</p>
          </div>
        </div>
      </header>

      <div className="h-96 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={retentionTrend} margin={{ top: 10, right: 20, bottom: 0, left: -10 }}>
            <defs>
              <linearGradient id="atRiskGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#f43f5e" stopOpacity={0.45} />
                <stop offset="100%" stopColor="#f43f5e" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="savedGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#10b981" stopOpacity={0.5} />
                <stop offset="100%" stopColor="#10b981" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="month" tick={{ fontSize: 11 }} stroke="#94a3b8" />
            <YAxis
              yAxisId="left"
              tick={{ fontSize: 11 }}
              stroke="#94a3b8"
              domain={[100, 'dataMax + 20']}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              tick={{ fontSize: 11 }}
              stroke="#94a3b8"
              domain={[0, 'dataMax + 1']}
              tickFormatter={(v) => `₹${v}`}
            />
            <RechartsTooltip
              contentStyle={{
                borderRadius: 12,
                border: '1px solid #e2e8f0',
                boxShadow: '0 10px 30px -10px rgba(15,23,42,0.2)',
                fontSize: 12,
              }}
            />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Area
              yAxisId="left"
              type="monotone"
              dataKey="atRisk"
              name="At-risk detected"
              stroke="#f43f5e"
              fill="url(#atRiskGrad)"
              strokeWidth={2}
            />
            <Area
              yAxisId="left"
              type="monotone"
              dataKey="saved"
              name="Successfully retained"
              stroke="#10b981"
              fill="url(#savedGrad)"
              strokeWidth={2}
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="revenueSavedCr"
              name="Revenue saved (₹ Cr)"
              stroke="#0f172a"
              strokeWidth={2}
              dot={{ r: 3, fill: '#0f172a' }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </article>
  )
}

// ────────────────────────────────────────────────────────────────────────────
// Agent activity
// ────────────────────────────────────────────────────────────────────────────

function AgentActivityCard() {
  return (
    <article className="relative rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <header className="mb-4 flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <Bot className="h-4 w-4 text-emerald-600" aria-hidden="true" />
          <div>
            <h3 className="text-base font-semibold text-slate-900">Agentic AI operations</h3>
            <p className="mt-0.5 text-xs text-slate-500">
              Four CrewAI agents · Pydantic-validated · deterministic guardrails
            </p>
          </div>
        </div>
        <LivePill />
      </header>

      <div className="space-y-2.5">
        {agents.map((agent) => (
          <div
            key={agent.id}
            className="group rounded-xl border border-slate-200 bg-white p-3 transition hover:border-emerald-200 hover:bg-slate-50/60"
          >
            <div className="flex items-start gap-3">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-emerald-600 to-teal-500 text-white shadow-sm">
                <Bot className="h-4 w-4" aria-hidden="true" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <p className="truncate text-sm font-semibold text-slate-900">{agent.name}</p>
                  <span className="inline-flex items-center gap-1 rounded-full border border-emerald-200 bg-emerald-50 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-emerald-700">
                    <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-500" />
                    {agent.status}
                  </span>
                </div>
                <p className="truncate text-xs text-slate-500">{agent.role}</p>
                <p className="mt-1.5 line-clamp-1 text-xs text-slate-600">
                  <span className="text-emerald-600">↳</span> {agent.lastDecision}
                </p>
              </div>
            </div>
            <div className="mt-3 grid grid-cols-3 gap-2 border-t border-slate-100 pt-2.5 text-center">
              <AgentStat label="Tasks today" value={agent.tasksToday.toString()} />
              <AgentStat label="Success" value={`${agent.successRate.toFixed(1)}%`} />
              <AgentStat label="Latency" value={`${agent.avgLatencySec.toFixed(1)}s`} />
            </div>
          </div>
        ))}
      </div>
    </article>
  )
}

function AgentStat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[10px] uppercase tracking-wider text-slate-500">{label}</p>
      <p className="text-sm font-semibold text-slate-900">{value}</p>
    </div>
  )
}

// ────────────────────────────────────────────────────────────────────────────
// Save funnel
// ────────────────────────────────────────────────────────────────────────────

function SaveFunnelCard({ overallSavePct }: { overallSavePct: number }) {
  const max = saveFunnel[0]?.count ?? 1
  return (
    <article className="relative overflow-hidden rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <header className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-slate-900">Retention save funnel · Q4</h3>
          <p className="mt-1 text-sm text-slate-500">
            From signal detection to confirmed retention — human-in-the-loop at every stage.
          </p>
        </div>
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-right">
          <p className="text-[11px] uppercase tracking-wider text-emerald-700">Overall save</p>
          <p className="text-2xl font-semibold text-emerald-700">{overallSavePct}%</p>
        </div>
      </header>

      <ol className="space-y-2.5">
        {saveFunnel.map((s, i) => {
          const widthPct = (s.count / max) * 100
          const stepPct = i === 0 ? 100 : Math.round((s.count / (saveFunnel[i - 1]?.count ?? 1)) * 100)
          return (
            <li key={s.stage} className="relative">
              <div className="flex items-baseline justify-between text-sm">
                <div className="flex items-center gap-2">
                  <span className="flex h-5 w-5 items-center justify-center rounded-full bg-slate-900 text-[10px] font-semibold text-white">
                    {i + 1}
                  </span>
                  <span className="font-medium text-slate-900">{s.stage}</span>
                  <span className="text-xs text-slate-500">· {s.description}</span>
                </div>
                <div className="flex items-center gap-3 text-xs">
                  {i > 0 ? (
                    <span className="text-slate-500">step {stepPct}%</span>
                  ) : null}
                  <span className="font-semibold tabular-nums text-slate-900">
                    {s.count.toLocaleString('en-IN')}
                  </span>
                </div>
              </div>
              <div className="mt-1.5 h-2.5 w-full overflow-hidden rounded-full bg-slate-100">
                <div
                  className="relative h-full rounded-full bg-gradient-to-r from-emerald-600 via-emerald-500 to-teal-400"
                  style={{ width: `${widthPct}%` }}
                >
                  <span
                    aria-hidden="true"
                    className="absolute inset-0 rounded-full bg-[linear-gradient(90deg,transparent,rgba(255,255,255,0.35),transparent)] bg-[length:200%_100%] animate-shimmer"
                  />
                </div>
              </div>
            </li>
          )
        })}
      </ol>
    </article>
  )
}

// ────────────────────────────────────────────────────────────────────────────
// Channel performance
// ────────────────────────────────────────────────────────────────────────────

function ChannelPerformanceCard() {
  const totals = channelPerformance.reduce(
    (acc, c) => ({
      contacted: acc.contacted + c.contacted,
      retained: acc.retained + c.retained,
    }),
    { contacted: 0, retained: 0 },
  )
  const blended = ((totals.retained / totals.contacted) * 100).toFixed(1)

  return (
    <article className="relative overflow-hidden rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <header className="mb-2">
        <h3 className="text-base font-semibold text-slate-900">Channel performance</h3>
        <p className="mt-1 text-sm text-slate-500">
          Save rate by outreach channel · blended{' '}
          <span className="font-semibold text-emerald-700">{blended}%</span>
        </p>
      </header>

      <div className="h-52 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={channelPerformance}
            layout="vertical"
            margin={{ top: 10, right: 24, bottom: 0, left: -8 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
            <XAxis
              type="number"
              domain={[0, 100]}
              tick={{ fontSize: 11 }}
              stroke="#94a3b8"
              tickFormatter={(v) => `${v}%`}
            />
            <YAxis
              type="category"
              dataKey="channel"
              tick={{ fontSize: 11 }}
              stroke="#94a3b8"
              width={56}
            />
            <RechartsTooltip
              contentStyle={{ borderRadius: 12, border: '1px solid #e2e8f0', fontSize: 12 }}
              formatter={(v, _n, item) => {
                const row = item?.payload as (typeof channelPerformance)[number] | undefined
                return [`${v}% save · ${row?.retained ?? '—'} / ${row?.contacted ?? '—'}`, 'Rate']
              }}
            />
            <Bar dataKey="saveRatePct" radius={[0, 6, 6, 0]} barSize={18}>
              {channelPerformance.map((c) => (
                <Cell
                  key={c.channel}
                  fill={
                    c.saveRatePct >= 80
                      ? '#047857'
                      : c.saveRatePct >= 65
                        ? '#10b981'
                        : c.saveRatePct >= 55
                          ? '#34d399'
                          : '#f59e0b'
                  }
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <dl className="mt-2 grid grid-cols-2 gap-3 border-t border-slate-100 pt-3 text-xs">
        <div>
          <dt className="text-slate-500">Fastest response</dt>
          <dd className="font-semibold text-slate-900">In-app · 0.6 h</dd>
        </div>
        <div>
          <dt className="text-slate-500">Highest save rate</dt>
          <dd className="font-semibold text-emerald-700">Phone · 82%</dd>
        </div>
      </dl>
    </article>
  )
}

// ────────────────────────────────────────────────────────────────────────────
// Model performance
// ────────────────────────────────────────────────────────────────────────────

function ModelPerformanceCard() {
  const firstAuc = modelDrift14d[0]?.auc ?? 0
  const lastAuc = modelDrift14d[modelDrift14d.length - 1]?.auc ?? 0
  const driftDelta = lastAuc - firstAuc
  const minAuc = Math.min(...modelDrift14d.map((d) => d.auc))
  const maxAuc = Math.max(...modelDrift14d.map((d) => d.auc))

  return (
    <article className="relative overflow-hidden rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <header className="mb-2">
        <div className="flex items-center gap-2">
          <Radar className="h-4 w-4 text-emerald-600" aria-hidden="true" />
          <h3 className="text-base font-semibold text-slate-900">Model performance</h3>
        </div>
        <p className="mt-1 text-sm text-slate-500">
          Churn-risk classifier · daily holdout · industry AUC 0.75–0.85
        </p>
      </header>

      <div className="h-44 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart
            innerRadius="30%"
            outerRadius="100%"
            data={modelMetrics}
            startAngle={90}
            endAngle={-270}
          >
            <RadialBar dataKey="value" background cornerRadius={8} />
            <RechartsTooltip
              contentStyle={{
                borderRadius: 12,
                border: '1px solid #e2e8f0',
                fontSize: 12,
              }}
              formatter={(v) => [`${v}`, 'Score']}
            />
            <Legend
              iconSize={8}
              wrapperStyle={{ fontSize: 11 }}
              layout="horizontal"
              verticalAlign="bottom"
            />
          </RadialBarChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-2 rounded-xl border border-slate-100 bg-slate-50/60 p-3">
        <div className="mb-1 flex items-baseline justify-between">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
            AUC drift · last 14 days
          </p>
          <p className="text-xs">
            <span className="font-semibold text-slate-900">{lastAuc.toFixed(1)}</span>
            <span className="ml-1 text-emerald-700">
              {driftDelta >= 0 ? '+' : ''}
              {driftDelta.toFixed(1)} pts
            </span>
          </p>
        </div>
        <div className="h-10 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={modelDrift14d} margin={{ top: 2, right: 0, bottom: 0, left: 0 }}>
              <YAxis hide domain={[minAuc - 0.5, maxAuc + 0.5]} />
              <Line
                type="monotone"
                dataKey="auc"
                stroke="#047857"
                strokeWidth={1.5}
                dot={false}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <dl className="mt-3 grid grid-cols-2 gap-3 border-t border-slate-100 pt-3 text-xs">
        <div>
          <dt className="text-slate-500">Status</dt>
          <dd className="font-semibold text-emerald-700">Stable · within band</dd>
        </div>
        <div>
          <dt className="text-slate-500">Explainability</dt>
          <dd className="font-semibold text-slate-900">SHAP · top-5 features</dd>
        </div>
      </dl>
    </article>
  )
}

// ────────────────────────────────────────────────────────────────────────────
// Risk × value matrix
// ────────────────────────────────────────────────────────────────────────────

function RiskValueMatrixCard() {
  const quadrantSummary = useMemo(() => {
    const hvHr = matrixPoints.filter((p) => p.value_score >= 50 && p.churn_score >= 50).length
    const hvLr = matrixPoints.filter((p) => p.value_score >= 50 && p.churn_score < 50).length
    const lvHr = matrixPoints.filter((p) => p.value_score < 50 && p.churn_score >= 50).length
    const lvLr = matrixPoints.filter((p) => p.value_score < 50 && p.churn_score < 50).length
    return { hvHr, hvLr, lvHr, lvLr }
  }, [])

  const insights = useMemo(() => {
    const totalRar = matrixPoints.reduce((s, p) => s + p.revenue_at_risk, 0)
    const avgChurn =
      matrixPoints.reduce((s, p) => s + p.churn_score, 0) / matrixPoints.length
    const avgValue =
      matrixPoints.reduce((s, p) => s + p.value_score, 0) / matrixPoints.length
    const sorted = [...matrixPoints].sort((a, b) => b.revenue_at_risk - a.revenue_at_risk)
    const top10 = sorted.slice(0, 10).reduce((s, p) => s + p.revenue_at_risk, 0)
    const concentration = totalRar > 0 ? (top10 / totalRar) * 100 : 0
    return {
      totalRarLakh: totalRar / 100_000,
      avgChurn,
      avgValue,
      concentration,
    }
  }, [])

  return (
    <article className="relative flex h-full flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <header className="mb-4">
        <div className="flex items-center gap-2">
          <Users className="h-4 w-4 text-emerald-600" aria-hidden="true" />
          <h3 className="text-base font-semibold text-slate-900">Risk × value portfolio map</h3>
        </div>
        <p className="mt-1 text-sm text-slate-500">
          Each point = one customer. Colour = retention decision · size = revenue at risk.
        </p>
      </header>

      <div className="grid flex-1 min-h-0 gap-4 lg:grid-cols-[1fr_200px]">
        <div className="min-h-[320px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 10, right: 10, bottom: 20, left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis
                type="number"
                dataKey="value_score"
                name="Customer value"
                domain={[0, 100]}
                tick={{ fontSize: 11 }}
                stroke="#94a3b8"
                label={{
                  value: 'Customer value score',
                  position: 'insideBottom',
                  offset: -5,
                  style: { fontSize: 11, fill: '#64748b' },
                }}
              />
              <YAxis
                type="number"
                dataKey="churn_score"
                name="Churn risk"
                domain={[0, 100]}
                tick={{ fontSize: 11 }}
                stroke="#94a3b8"
                label={{
                  value: 'Churn risk score',
                  angle: -90,
                  position: 'insideLeft',
                  style: { fontSize: 11, fill: '#64748b' },
                }}
              />
              <ZAxis type="number" dataKey="revenue_at_risk" range={[60, 500]} />
              <RechartsTooltip
                cursor={{ strokeDasharray: '3 3' }}
                content={({ active, payload }) => {
                  if (!active || !payload?.[0]) return null
                  const p = payload[0].payload as (typeof matrixPoints)[number]
                  return (
                    <div className="rounded-lg border border-slate-200 bg-white p-3 text-xs shadow-lg">
                      <p className="font-semibold text-slate-900">{p.full_name}</p>
                      <p className="text-slate-500">{p.customer_id}</p>
                      <p className="mt-1">
                        Churn <b>{p.churn_score}</b> · Value <b>{p.value_score}</b>
                      </p>
                      <p>Decision: {DECISION_LABELS[p.decision]}</p>
                      <p>Revenue at risk: ₹{(p.revenue_at_risk / 100000).toFixed(1)} L</p>
                    </div>
                  )
                }}
              />
              {(Object.keys(DECISION_COLORS) as RecommendationDecision[]).map((d) => (
                <Scatter
                  key={d}
                  name={DECISION_LABELS[d]}
                  data={matrixPoints.filter((p) => p.decision === d)}
                  fill={DECISION_COLORS[d]}
                >
                  {matrixPoints
                    .filter((p) => p.decision === d)
                    .map((entry) => (
                      <Cell key={entry.customer_id} fill={DECISION_COLORS[d]} />
                    ))}
                </Scatter>
              ))}
            </ScatterChart>
          </ResponsiveContainer>
        </div>

        <div className="space-y-3 text-sm">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Quadrant mix
          </p>
          <QuadrantRow label="High value · high risk" value={quadrantSummary.hvHr} tone="rose" />
          <QuadrantRow label="High value · low risk" value={quadrantSummary.hvLr} tone="emerald" />
          <QuadrantRow label="Low value · high risk" value={quadrantSummary.lvHr} tone="amber" />
          <QuadrantRow label="Low value · low risk" value={quadrantSummary.lvLr} tone="slate" />

          <div className="border-t border-slate-100 pt-3">
            <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
              Decision mix
            </p>
            <ul className="space-y-2">
              {(Object.keys(DECISION_COLORS) as RecommendationDecision[]).map((d) => {
                const count = matrixPoints.filter((p) => p.decision === d).length
                const pct = (count / matrixPoints.length) * 100
                return (
                  <li key={d} className="space-y-0.5 text-xs">
                    <div className="flex items-center justify-between gap-2 text-slate-600">
                      <span className="flex items-center gap-2">
                        <span
                          aria-hidden="true"
                          className="inline-block h-2 w-2 rounded-full"
                          style={{ backgroundColor: DECISION_COLORS[d] }}
                        />
                        {DECISION_LABELS[d]}
                      </span>
                      <span className="tabular-nums text-slate-900">
                        {count} · {pct.toFixed(0)}%
                      </span>
                    </div>
                    <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
                      <div
                        className="h-full rounded-full"
                        style={{
                          width: `${pct}%`,
                          backgroundColor: DECISION_COLORS[d],
                        }}
                      />
                    </div>
                  </li>
                )
              })}
            </ul>
          </div>
        </div>
      </div>

      <footer className="mt-4 grid grid-cols-2 gap-3 border-t border-slate-100 pt-3 sm:grid-cols-4">
        <InsightChip
          label="Portfolio at risk"
          value={`₹${insights.totalRarLakh.toFixed(0)} L`}
          hint="Across all scored customers"
        />
        <InsightChip
          label="Avg churn score"
          value={insights.avgChurn.toFixed(0)}
          hint="Portfolio mean"
        />
        <InsightChip
          label="Avg value score"
          value={insights.avgValue.toFixed(0)}
          hint="Portfolio mean"
        />
        <InsightChip
          label="Top-10 concentration"
          value={`${insights.concentration.toFixed(0)}%`}
          hint="Of total revenue at risk"
          tone="emerald"
        />
      </footer>
    </article>
  )
}

function InsightChip({
  label,
  value,
  hint,
  tone,
}: {
  label: string
  value: string
  hint: string
  tone?: 'emerald'
}) {
  return (
    <div className="rounded-lg border border-slate-100 bg-slate-50/60 px-3 py-2">
      <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">{label}</p>
      <p
        className={cn(
          'mt-0.5 text-base font-semibold tabular-nums text-slate-900',
          tone === 'emerald' && 'text-emerald-700',
        )}
      >
        {value}
      </p>
      <p className="text-[10px] text-slate-500">{hint}</p>
    </div>
  )
}

function QuadrantRow({
  label,
  value,
  tone,
}: {
  label: string
  value: number
  tone: 'rose' | 'emerald' | 'amber' | 'slate'
}) {
  const dot = {
    rose: 'bg-rose-500',
    emerald: 'bg-emerald-500',
    amber: 'bg-amber-500',
    slate: 'bg-slate-400',
  }[tone]
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <span className={cn('h-2 w-2 rounded-full', dot)} aria-hidden="true" />
        <span className="text-slate-600">{label}</span>
      </div>
      <span className="font-semibold tabular-nums text-slate-900">{value}</span>
    </div>
  )
}

// ────────────────────────────────────────────────────────────────────────────
// Priority rail (top customers + live alerts)
// ────────────────────────────────────────────────────────────────────────────

function PriorityRailCard({ onSelectCustomer }: { onSelectCustomer: (id: string) => void }) {
  return (
    <article className="relative overflow-hidden rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <header className="mb-3 flex items-center justify-between">
        <div>
          <h3 className="text-base font-semibold text-slate-900">Priority queue</h3>
          <p className="text-sm text-slate-500">Top 8 customers · click to review · RM action pending</p>
        </div>
        <LivePill />
      </header>

      <ul className="space-y-2.5">
        {priorityCustomers.map((c) => (
          <li key={c.id}>
            <button
              type="button"
              onClick={() => onSelectCustomer(c.id)}
              className={cn(
                'group relative w-full rounded-xl border border-slate-200 bg-white p-3 text-left transition',
                'hover:border-emerald-300 hover:bg-emerald-50/40 hover:shadow-sm',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400',
              )}
              aria-label={`Open dossier for ${c.name}`}
            >
              <div className="flex items-start gap-3">
                <div
                  className={cn(
                    'flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br text-xs font-semibold text-white shadow-sm',
                    SEGMENT_ACCENTS[c.segment],
                  )}
                >
                  {initials(c.name)}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between gap-2">
                    <p className="truncate text-sm font-semibold text-slate-900">{c.name}</p>
                    <span className="shrink-0 text-xs font-semibold text-slate-900">
                      P{c.priority}
                    </span>
                  </div>
                  <p className="truncate text-xs text-slate-500">
                    {c.id} · {SEGMENT_LABELS[c.segment]} · ₹{c.revenueAtRiskLakh.toFixed(1)} L at risk
                  </p>
                  <p className="mt-1 truncate text-xs text-slate-600">
                    <span className="text-rose-600">●</span> {c.trigger}
                  </p>
                  <p className="mt-0.5 truncate text-xs text-emerald-700">↳ {c.offer}</p>
                </div>
              </div>
            </button>
          </li>
        ))}
      </ul>

      <div className="mt-4 border-t border-slate-100 pt-3">
        <div className="mb-2 flex items-center justify-between">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Live alert stream
          </p>
          <span className="text-[11px] text-slate-400">last 60 min</span>
        </div>
        <ul className="space-y-1.5 text-xs">
          {liveAlerts.map((a) => (
            <li key={a.id} className="flex items-start gap-2">
              <span
                className={cn(
                  'mt-1 h-1.5 w-1.5 shrink-0 rounded-full',
                  a.severity === 'CRITICAL' && 'bg-rose-500',
                  a.severity === 'HIGH' && 'bg-amber-500',
                  a.severity === 'MEDIUM' && 'bg-slate-400',
                )}
                aria-hidden="true"
              />
              <div className="min-w-0 flex-1">
                <p className="truncate text-slate-700">
                  <span className="font-semibold text-slate-900">{a.customerId}</span> · {a.text}
                </p>
              </div>
              <span className="shrink-0 tabular-nums text-slate-400">{a.minutesAgo}m</span>
            </li>
          ))}
        </ul>
      </div>
    </article>
  )
}

function initials(name: string): string {
  return name
    .split(' ')
    .map((p) => p[0])
    .slice(0, 2)
    .join('')
    .toUpperCase()
}

// ────────────────────────────────────────────────────────────────────────────
// Cohort retention heatmap
// ────────────────────────────────────────────────────────────────────────────

function CohortRetentionCard() {
  const months = ['M0', 'M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M7']

  // All known retention values across all cohorts/months (ignoring the implicit 100 at M0).
  const observed = cohortRetention.flatMap((r) =>
    r.retention.slice(1).filter((v): v is number => v !== null),
  )
  const avgM1 = cohortRetention
    .map((r) => r.retention[1])
    .filter((v): v is number => v !== null)
  const avgM6 = cohortRetention
    .map((r) => r.retention[6])
    .filter((v): v is number => v !== null)
  const avg = (xs: number[]) => (xs.length ? xs.reduce((s, x) => s + x, 0) / xs.length : 0)

  return (
    <article className="relative overflow-hidden rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <header className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-slate-900">
            Cohort retention · last 8 months
          </h3>
          <p className="mt-1 text-sm text-slate-500">
            % of each monthly cohort still active N months after joining.
          </p>
        </div>
        <div className="flex gap-6 text-right">
          <div>
            <p className="text-[11px] uppercase tracking-wider text-slate-500">Avg M1</p>
            <p className="text-lg font-semibold text-slate-900">{avg(avgM1).toFixed(1)}%</p>
          </div>
          <div>
            <p className="text-[11px] uppercase tracking-wider text-slate-500">Avg M6</p>
            <p className="text-lg font-semibold text-emerald-700">{avg(avgM6).toFixed(1)}%</p>
          </div>
          <div>
            <p className="text-[11px] uppercase tracking-wider text-slate-500">Observations</p>
            <p className="text-lg font-semibold text-slate-900">{observed.length}</p>
          </div>
        </div>
      </header>

      <div className="overflow-x-auto">
        <table className="min-w-full border-separate border-spacing-y-1 text-xs">
          <thead>
            <tr className="text-left text-[11px] uppercase tracking-wider text-slate-500">
              <th className="pr-3 font-medium">Cohort</th>
              <th className="pr-3 font-medium">Size</th>
              {months.map((m) => (
                <th key={m} className="px-1 text-center font-medium">
                  {m}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {cohortRetention.map((row) => (
              <tr key={row.cohort}>
                <td className="pr-3 font-medium text-slate-900">{row.cohort}</td>
                <td className="pr-3 tabular-nums text-slate-600">
                  {row.customers.toLocaleString('en-IN')}
                </td>
                {row.retention.map((v, i) => (
                  <td key={i} className="px-0.5">
                    <HeatCell value={v} isM0={i === 0} />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-3 text-xs text-slate-500">
        <span>Shaded by retention % — darker = more retained.</span>
        <div className="flex items-center gap-2">
          <span>Low</span>
          <span className="flex overflow-hidden rounded">
            {['bg-emerald-100', 'bg-emerald-200', 'bg-emerald-300', 'bg-emerald-400', 'bg-emerald-500', 'bg-emerald-600', 'bg-emerald-700'].map(
              (c) => (
                <span key={c} className={cn('h-2.5 w-5', c)} />
              ),
            )}
          </span>
          <span>High</span>
        </div>
      </div>
    </article>
  )
}

function HeatCell({ value, isM0 }: { value: number | null; isM0: boolean }) {
  if (value === null) {
    return (
      <div
        className="flex h-9 w-full items-center justify-center rounded-md border border-dashed border-slate-200 text-slate-300"
        aria-label="Cohort too young"
      >
        —
      </div>
    )
  }
  // Map retention % → emerald shade. The visible band is roughly 85–100.
  const clamped = Math.max(0, Math.min(100, value))
  // Treat M0 (always 100) with the darkest shade; otherwise interpolate from 85→100.
  const t = isM0 ? 1 : Math.max(0, Math.min(1, (clamped - 85) / 15))
  const bands = [
    'bg-emerald-100 text-emerald-900',
    'bg-emerald-200 text-emerald-900',
    'bg-emerald-300 text-emerald-900',
    'bg-emerald-400 text-emerald-900',
    'bg-emerald-500 text-white',
    'bg-emerald-600 text-white',
    'bg-emerald-700 text-white',
  ]
  const idx = Math.min(bands.length - 1, Math.round(t * (bands.length - 1)))
  return (
    <div
      className={cn(
        'flex h-9 min-w-11 items-center justify-center rounded-md text-[11px] font-semibold tabular-nums',
        bands[idx],
      )}
      title={`${value.toFixed(1)}% retained`}
    >
      {value.toFixed(0)}
    </div>
  )
}

// ────────────────────────────────────────────────────────────────────────────
// Segment performance table
// ────────────────────────────────────────────────────────────────────────────

function SegmentPerformanceCard() {
  const totalCustomers = segmentPerformance.reduce((s, r) => s + r.customers, 0)
  const totalRevenueAtRisk = segmentPerformance.reduce((s, r) => s + r.revenueAtRiskCr, 0)
  const weightedRetention =
    segmentPerformance.reduce((s, r) => s + r.retentionPct * r.customers, 0) / totalCustomers

  return (
    <article className="relative overflow-hidden rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <header className="mb-3 flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-emerald-600" aria-hidden="true" />
            <h3 className="text-base font-semibold text-slate-900">Segment retention health</h3>
          </div>
          <p className="mt-1 text-sm text-slate-500">
            Weighted retention{' '}
            <span className="font-semibold text-emerald-600">{weightedRetention.toFixed(1)}%</span>{' '}
            · ₹{totalRevenueAtRisk.toFixed(1)} Cr total at risk
          </p>
        </div>
      </header>

      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b border-slate-100 text-left text-[11px] uppercase tracking-wider text-slate-500">
              <th className="py-2 pr-4 font-medium">Segment</th>
              <th className="py-2 pr-4 font-medium">Customers</th>
              <th className="py-2 pr-4 font-medium">Retention</th>
              <th className="py-2 pr-4 font-medium">Revenue at risk</th>
              <th className="py-2 pr-4 font-medium">Products / customer</th>
            </tr>
          </thead>
          <tbody>
            {segmentPerformance.map((row) => {
              const barPct = Math.max(0, Math.min(100, row.retentionPct))
              return (
                <tr key={row.segment} className="border-b border-slate-50 last:border-0">
                  <td className="py-3 pr-4">
                    <div className="flex items-center gap-2">
                      <span
                        className={cn(
                          'h-2.5 w-2.5 rounded-full bg-gradient-to-br',
                          SEGMENT_ACCENTS[row.segment],
                        )}
                        aria-hidden="true"
                      />
                      <span className="font-medium text-slate-900">
                        {SEGMENT_LABELS[row.segment]}
                      </span>
                    </div>
                  </td>
                  <td className="py-3 pr-4 tabular-nums text-slate-700">
                    {row.customers.toLocaleString('en-IN')}
                  </td>
                  <td className="py-3 pr-4">
                    <div className="flex items-center gap-2">
                      <div className="h-1.5 w-24 overflow-hidden rounded-full bg-slate-100">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-teal-500"
                          style={{ width: `${barPct}%` }}
                        />
                      </div>
                      <span className="tabular-nums font-semibold text-slate-900">
                        {row.retentionPct.toFixed(1)}%
                      </span>
                    </div>
                  </td>
                  <td className="py-3 pr-4 tabular-nums text-slate-700">
                    ₹{row.revenueAtRiskCr.toFixed(1)} Cr
                  </td>
                  <td className="py-3 pr-4 tabular-nums text-slate-700">
                    {row.productsPerCustomer.toFixed(1)}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </article>
  )
}

// ────────────────────────────────────────────────────────────────────────────
// Guardrails card
// ────────────────────────────────────────────────────────────────────────────

function GuardrailsCard() {
  const items = [
    {
      icon: Shield,
      title: 'Deterministic scoring',
      body: 'Churn, value and priority computed by rules — never by the LLM.',
    },
    {
      icon: CheckCircle2,
      title: 'Approved offers only',
      body: 'LLM can only reference offers returned by the eligibility service.',
    },
    {
      icon: Activity,
      title: 'Human in the loop',
      body: 'Every recommendation requires explicit RM approval before customer contact.',
    },
    {
      icon: Zap,
      title: 'Structured AI output',
      body: 'All agent responses validated against Pydantic schemas before persistence.',
    },
  ]

  return (
    <article className="relative overflow-hidden rounded-2xl border border-slate-200 bg-gradient-to-br from-emerald-50/60 via-white to-slate-50 p-5 shadow-sm">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -right-16 -top-16 h-40 w-40 rounded-full bg-emerald-200/40 blur-2xl"
      />
      <header className="relative mb-3">
        <h3 className="text-base font-semibold text-slate-900">Guardrails & governance</h3>
        <p className="mt-1 text-sm text-slate-500">
          Why RetainAI can run in a regulated banking stack.
        </p>
      </header>

      <ul className="relative space-y-3">
        {items.map((it) => (
          <li key={it.title} className="flex items-start gap-3">
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-emerald-600 to-teal-500 text-white shadow-sm">
              <it.icon className="h-4 w-4" aria-hidden="true" />
            </span>
            <div>
              <p className="text-sm font-semibold text-slate-900">{it.title}</p>
              <p className="text-xs text-slate-600">{it.body}</p>
            </div>
          </li>
        ))}
      </ul>
    </article>
  )
}

// ────────────────────────────────────────────────────────────────────────────
// Compliance strip
// ────────────────────────────────────────────────────────────────────────────

function ComplianceStrip() {
  const items = [
    'Synthetic data only',
    'Audit trail · 100% of agent decisions',
    'Policy v4.2 · RBI-aligned',
    'Pydantic-validated outputs',
    'Mock LLM mode supported',
  ]
  return (
    <section className="rounded-2xl border border-slate-200 bg-slate-50 px-5 py-4">
      <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-slate-600">
        <span className="font-semibold text-slate-900">Trust posture</span>
        {items.map((it) => (
          <span key={it} className="inline-flex items-center gap-1.5">
            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" aria-hidden="true" />
            {it}
          </span>
        ))}
      </div>
    </section>
  )
}

// ────────────────────────────────────────────────────────────────────────────
// Customer dossier modal (opens when a priority customer is clicked)
// ────────────────────────────────────────────────────────────────────────────

const VERDICT_STYLES: Record<
  CustomerDossier['verdict']['label'],
  { badge: string; banner: string; accent: string; icon: typeof CheckCircle2; label: string }
> = {
  RETAIN: {
    badge: 'bg-emerald-100 text-emerald-800 border-emerald-200',
    banner: 'from-emerald-600 to-teal-500',
    accent: 'text-emerald-700',
    icon: CheckCircle2,
    label: 'RETAIN · act now',
  },
  REVIEW: {
    badge: 'bg-amber-100 text-amber-800 border-amber-200',
    banner: 'from-amber-500 to-orange-500',
    accent: 'text-amber-700',
    icon: ShieldAlert,
    label: 'REVIEW · policy constraints',
  },
  DO_NOT_RETAIN: {
    badge: 'bg-rose-100 text-rose-800 border-rose-200',
    banner: 'from-rose-600 to-rose-500',
    accent: 'text-rose-700',
    icon: AlertTriangle,
    label: 'DO NOT RETAIN',
  },
}

const FLAG_DOT: Record<RedFlagSeverity, string> = {
  HIGH: 'bg-rose-500',
  MEDIUM: 'bg-amber-500',
  LOW: 'bg-slate-400',
}

const FLAG_BADGE: Record<RedFlagSeverity, string> = {
  HIGH: 'bg-rose-50 text-rose-700 border-rose-200',
  MEDIUM: 'bg-amber-50 text-amber-800 border-amber-200',
  LOW: 'bg-slate-50 text-slate-600 border-slate-200',
}

type RedFlagSeverity = 'HIGH' | 'MEDIUM' | 'LOW'

interface AgentStep {
  id: string
  name: string
  role: string
  taskLabel: (dossier: CustomerDossier) => string
  accent: string
}

const AGENT_PIPELINE: AgentStep[] = [
  {
    id: 'retention-analyst',
    name: 'Retention Analyst',
    role: 'Interprets churn signals',
    taskLabel: (d) =>
      `Scoring churn, value & priority for ${d.id} using deterministic rules…`,
    accent: 'from-emerald-600 to-teal-500',
  },
  {
    id: 'offer-strategist',
    name: 'Offer Strategist',
    role: 'Matches eligible offers',
    taskLabel: () => 'Matching approved-catalog offers against eligibility & segment…',
    accent: 'from-teal-500 to-cyan-500',
  },
  {
    id: 'risk-advisor',
    name: 'Risk Advisor',
    role: 'Validates policy guardrails',
    taskLabel: (d) =>
      `Checking policy v4.2 constraints (DPD ${d.credit.maxDpd12m}d · util ${d.credit.utilizationPct}%)…`,
    accent: 'from-amber-500 to-orange-500',
  },
  {
    id: 'rm-communicator',
    name: 'RM Communicator',
    role: 'Drafts customer narrative',
    taskLabel: () => 'Composing RM-ready outreach narrative + verdict rationale…',
    accent: 'from-emerald-500 to-emerald-400',
  },
]

/** Milliseconds spent in each pipeline step. */
const STEP_DURATION_MS = 650

function CustomerDossierModal({
  dossier,
  onClose,
}: {
  dossier: CustomerDossier
  onClose: () => void
}) {
  // 0..AGENT_PIPELINE.length = still running (current step index)
  // AGENT_PIPELINE.length = all steps done → render dossier.
  const [agentStep, setAgentStep] = useState(0)
  const isRunning = agentStep < AGENT_PIPELINE.length

  // Advance the agent crew while the modal is open.
  useEffect(() => {
    if (!isRunning) return
    const t = window.setTimeout(() => setAgentStep((s) => s + 1), STEP_DURATION_MS)
    return () => window.clearTimeout(t)
  }, [agentStep, isRunning])

  // Esc to close + body scroll lock while open.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKey)
    const prevOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = prevOverflow
    }
  }, [onClose])

  const verdictStyle = VERDICT_STYLES[dossier.verdict.label]
  const VerdictIcon = verdictStyle.icon
  const scoreTone =
    dossier.credit.scoreBand === 'EXCELLENT'
      ? 'text-emerald-700'
      : dossier.credit.scoreBand === 'GOOD'
        ? 'text-emerald-600'
        : dossier.credit.scoreBand === 'FAIR'
          ? 'text-amber-600'
          : 'text-rose-600'

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="dossier-title"
      className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-slate-950/50 p-4 backdrop-blur-sm sm:p-8"
      onClick={onClose}
    >
      <div
        className="relative my-4 w-full max-w-5xl overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Running progress strip (top edge) */}
        {isRunning ? (
          <div
            aria-hidden="true"
            className="absolute inset-x-0 top-0 h-0.5 overflow-hidden"
          >
            <div
              className="h-full bg-gradient-to-r from-emerald-500 to-teal-400 transition-all duration-500 ease-out"
              style={{ width: `${(agentStep / AGENT_PIPELINE.length) * 100}%` }}
            />
          </div>
        ) : null}

        {/* Header strip */}
        <div className="relative flex items-start justify-between gap-4 border-b border-slate-100 px-6 py-5">
          <div className="flex items-start gap-4">
            <div
              className={cn(
                'flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br text-sm font-semibold text-white shadow-sm',
                SEGMENT_ACCENTS[dossier.segment],
              )}
            >
              {initials(dossier.name)}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2
                  id="dossier-title"
                  className="text-xl font-semibold tracking-tight text-slate-900"
                >
                  {dossier.name}
                </h2>
                {isRunning ? (
                  <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-emerald-700">
                    <span className="relative flex h-1.5 w-1.5">
                      <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-500 opacity-70" />
                      <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-emerald-500" />
                    </span>
                    Agents working…
                  </span>
                ) : (
                  <span
                    className={cn(
                      'inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider',
                      verdictStyle.badge,
                    )}
                  >
                    <VerdictIcon className="mr-1 h-3 w-3" aria-hidden="true" />
                    {verdictStyle.label}
                  </span>
                )}
              </div>
              <p className="mt-0.5 text-sm text-slate-500">
                {dossier.id} · {SEGMENT_LABELS[dossier.segment]} · {dossier.relationshipYears}-yr
                relationship · Preferred: {dossier.preferredChannel}
              </p>
              <div className="mt-2 flex flex-wrap items-center gap-2 text-xs">
                <ChipStat label="Priority" value={`P${dossier.priority}`} tone="slate" />
                <ChipStat
                  label="Revenue at risk"
                  value={`₹${dossier.revenueAtRiskLakh.toFixed(1)} L`}
                  tone="rose"
                />
                <ChipStat label="Churn score" value={dossier.churnScore.toString()} tone="slate" />
                <ChipStat label="Value score" value={dossier.valueScore.toString()} tone="slate" />
              </div>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close dossier"
            className="rounded-lg p-1.5 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
          >
            <X className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>

        {isRunning ? (
          <AgentProcessingView dossier={dossier} currentStep={agentStep} />
        ) : (
          <DossierBody dossier={dossier} verdictStyle={verdictStyle} scoreTone={scoreTone} />
        )}
      </div>
    </div>
  )
}

function AgentProcessingView({
  dossier,
  currentStep,
}: {
  dossier: CustomerDossier
  currentStep: number
}) {
  return (
    <div className="relative px-6 pb-6 pt-5">
      {/* subtle emerald glow bg */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -top-10 right-10 h-40 w-40 rounded-full bg-emerald-100/60 blur-3xl"
      />
      <div className="relative mb-5 flex items-center gap-2 text-sm">
        <Bot className="h-4 w-4 text-emerald-600" aria-hidden="true" />
        <p className="font-semibold text-slate-900">Running agent crew</p>
        <span className="text-xs text-slate-500">
          · deterministic rules + Qwen3-8B reasoning
        </span>
      </div>

      <ol className="relative space-y-3">
        {AGENT_PIPELINE.map((agent, i) => {
          const state: 'done' | 'running' | 'queued' =
            i < currentStep ? 'done' : i === currentStep ? 'running' : 'queued'
          return (
            <li
              key={agent.id}
              className={cn(
                'relative overflow-hidden rounded-xl border p-3.5 transition-all',
                state === 'done' && 'border-emerald-200 bg-emerald-50/50',
                state === 'running' && 'border-emerald-300 bg-white shadow-sm ring-1 ring-emerald-200',
                state === 'queued' && 'border-slate-100 bg-white opacity-60',
              )}
            >
              <div className="flex items-start gap-3">
                <div
                  className={cn(
                    'relative flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br text-white shadow-sm',
                    agent.accent,
                  )}
                >
                  <Bot className="h-4 w-4" aria-hidden="true" />
                  {state === 'running' ? (
                    <span className="absolute inset-0 rounded-lg ring-2 ring-emerald-400/70 animate-pulse" />
                  ) : null}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm font-semibold text-slate-900">{agent.name}</p>
                    <StepBadge state={state} />
                  </div>
                  <p className="truncate text-xs text-slate-500">{agent.role}</p>
                  <p className="mt-1 line-clamp-1 text-xs text-slate-700">
                    {state === 'queued' ? 'Queued…' : agent.taskLabel(dossier)}
                  </p>
                  {state === 'running' ? (
                    <div className="mt-2 h-1 w-full overflow-hidden rounded-full bg-emerald-100">
                      <div className="relative h-full w-1/3 rounded-full bg-gradient-to-r from-emerald-500 to-teal-400">
                        <span className="absolute inset-0 rounded-full bg-[linear-gradient(90deg,transparent,rgba(255,255,255,0.5),transparent)] bg-[length:200%_100%] animate-shimmer" />
                      </div>
                    </div>
                  ) : null}
                </div>
              </div>
            </li>
          )
        })}
      </ol>

      <p className="mt-4 text-center text-xs text-slate-500">
        All outputs are Pydantic-validated · the LLM never touches eligibility or scores.
      </p>
    </div>
  )
}

function StepBadge({ state }: { state: 'done' | 'running' | 'queued' }) {
  if (state === 'done') {
    return (
      <span className="inline-flex items-center gap-1 rounded-full border border-emerald-200 bg-emerald-50 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-emerald-700">
        <CheckCircle2 className="h-3 w-3" aria-hidden="true" />
        Done
      </span>
    )
  }
  if (state === 'running') {
    return (
      <span className="inline-flex items-center gap-1 rounded-full border border-emerald-300 bg-emerald-100 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-emerald-800">
        <span className="relative flex h-1.5 w-1.5">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-500 opacity-70" />
          <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-emerald-500" />
        </span>
        Running
      </span>
    )
  }
  return (
    <span className="inline-flex items-center rounded-full border border-slate-200 bg-slate-50 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
      Queued
    </span>
  )
}

function DossierBody({
  dossier,
  verdictStyle,
  scoreTone,
}: {
  dossier: CustomerDossier
  verdictStyle: (typeof VERDICT_STYLES)[CustomerDossier['verdict']['label']]
  scoreTone: string
}) {
  const VerdictIcon = verdictStyle.icon
  return (
    <>
      {/* Verdict banner */}
        <div className="px-6 pt-5">
          <div
            className={cn(
              'relative overflow-hidden rounded-xl bg-gradient-to-r p-4 text-white shadow-sm',
              verdictStyle.banner,
            )}
          >
            <div className="flex items-start gap-3">
              <VerdictIcon className="mt-0.5 h-5 w-5 shrink-0" aria-hidden="true" />
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-wider text-white/80">
                  Agent verdict · deterministic rules + CrewAI reasoning
                </p>
                <p className="mt-0.5 text-base font-semibold leading-snug">
                  {dossier.verdict.headline}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Body */}
        <div className="grid gap-5 px-6 py-5 lg:grid-cols-[1.1fr_1fr]">
          {/* Left: red flags + reasoning */}
          <div className="space-y-5">
            <section>
              <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-slate-900">
                <AlertTriangle className="h-4 w-4 text-rose-500" aria-hidden="true" />
                Red flags · {dossier.redFlags.length}
              </h3>
              <ul className="space-y-2">
                {dossier.redFlags.map((f) => (
                  <li
                    key={f.label}
                    className="flex items-start gap-3 rounded-lg border border-slate-100 bg-slate-50/60 p-3"
                  >
                    <span
                      className={cn('mt-1.5 h-2 w-2 shrink-0 rounded-full', FLAG_DOT[f.severity])}
                      aria-hidden="true"
                    />
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-semibold text-slate-900">{f.label}</p>
                        <span
                          className={cn(
                            'inline-flex items-center rounded-full border px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wider',
                            FLAG_BADGE[f.severity],
                          )}
                        >
                          {f.severity}
                        </span>
                      </div>
                      <p className="mt-0.5 text-xs text-slate-600">{f.detail}</p>
                    </div>
                  </li>
                ))}
              </ul>
            </section>

            <section>
              <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-slate-900">
                <Sparkles className="h-4 w-4 text-emerald-600" aria-hidden="true" />
                Why this verdict
              </h3>
              <ul className="space-y-1.5 text-sm text-slate-700">
                {dossier.verdict.reasons.map((r, i) => (
                  <li key={i} className="flex gap-2">
                    <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-slate-400" />
                    <span>{r}</span>
                  </li>
                ))}
              </ul>
            </section>
          </div>

          {/* Right: credit + banking snapshots */}
          <div className="space-y-5">
            <section>
              <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-slate-900">
                <CreditCard className="h-4 w-4 text-slate-500" aria-hidden="true" />
                Credit snapshot
              </h3>
              <div className="grid grid-cols-3 gap-2">
                <SnapshotCell
                  label="CIBIL"
                  value={dossier.credit.creditScore.toString()}
                  hint={dossier.credit.scoreBand}
                  valueClass={scoreTone}
                />
                <SnapshotCell
                  label="Max DPD 12m"
                  value={`${dossier.credit.maxDpd12m}d`}
                  hint={dossier.credit.maxDpd12m === 0 ? 'Clean' : 'Watch'}
                  valueClass={dossier.credit.maxDpd12m === 0 ? 'text-emerald-700' : 'text-rose-600'}
                />
                <SnapshotCell
                  label="Utilisation"
                  value={`${dossier.credit.utilizationPct}%`}
                  hint={dossier.credit.utilizationPct < 30 ? 'Healthy' : dossier.credit.utilizationPct < 70 ? 'Moderate' : 'Stressed'}
                  valueClass={
                    dossier.credit.utilizationPct < 30
                      ? 'text-emerald-700'
                      : dossier.credit.utilizationPct < 70
                        ? 'text-amber-600'
                        : 'text-rose-600'
                  }
                />
                <SnapshotCell
                  label="Active loans"
                  value={dossier.credit.activeLoans.toString()}
                  hint="On book"
                />
                <SnapshotCell
                  label="Enquiries"
                  value={dossier.credit.recentInquiries.toString()}
                  hint="Last 90 days"
                  valueClass={
                    dossier.credit.recentInquiries === 0
                      ? 'text-emerald-700'
                      : dossier.credit.recentInquiries <= 2
                        ? 'text-slate-900'
                        : 'text-rose-600'
                  }
                />
                <SnapshotCell
                  label="Default"
                  value={dossier.credit.defaultFlag ? 'YES' : 'No'}
                  hint="Flag"
                  valueClass={dossier.credit.defaultFlag ? 'text-rose-600' : 'text-emerald-700'}
                />
              </div>
            </section>

            <section>
              <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-slate-900">
                <Wallet className="h-4 w-4 text-slate-500" aria-hidden="true" />
                Banking snapshot
              </h3>
              <div className="grid grid-cols-3 gap-2">
                <SnapshotCell
                  label="Balance"
                  value={`₹${dossier.banking.currentBalanceLakh.toFixed(1)} L`}
                  hint="Current"
                />
                <SnapshotCell
                  label="90-d avg"
                  value={`₹${dossier.banking.avgBalance90dLakh.toFixed(1)} L`}
                  hint="Average"
                />
                <SnapshotCell
                  label="Δ 30d"
                  value={`${dossier.banking.balanceChange30dPct > 0 ? '+' : ''}${dossier.banking.balanceChange30dPct.toFixed(1)}%`}
                  hint="Balance change"
                  valueClass={
                    dossier.banking.balanceChange30dPct >= 0 ? 'text-emerald-700' : 'text-rose-600'
                  }
                />
                <SnapshotCell
                  label="Salary"
                  value={dossier.banking.salaryReceivedThisMonth ? 'Credited' : 'Missed'}
                  hint={dossier.banking.salaryAccount ? 'Salary A/C' : 'Non-salary'}
                  valueClass={
                    dossier.banking.salaryReceivedThisMonth ? 'text-emerald-700' : 'text-rose-600'
                  }
                />
                <SnapshotCell
                  label="Card spend Δ"
                  value={`${dossier.banking.cardSpendChangePct > 0 ? '+' : ''}${dossier.banking.cardSpendChangePct}%`}
                  hint="QoQ"
                  valueClass={
                    dossier.banking.cardSpendChangePct >= 0 ? 'text-emerald-700' : 'text-rose-600'
                  }
                />
                <SnapshotCell
                  label="Competitor"
                  value={dossier.banking.competitorTransferDetected ? 'Detected' : 'None'}
                  hint="Outbound flow"
                  valueClass={
                    dossier.banking.competitorTransferDetected
                      ? 'text-rose-600'
                      : 'text-emerald-700'
                  }
                />
              </div>
            </section>
          </div>
        </div>

        {/* Offers / policy blocks */}
        <div className="border-t border-slate-100 bg-slate-50/40 px-6 py-5">
          {dossier.policyBlocks && dossier.policyBlocks.length > 0 ? (
            <section className="mb-5">
              <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-slate-900">
                <ShieldAlert className="h-4 w-4 text-rose-500" aria-hidden="true" />
                Policy blocks
              </h3>
              <ul className="space-y-2">
                {dossier.policyBlocks.map((p) => (
                  <li
                    key={p.title}
                    className="rounded-lg border border-rose-200 bg-rose-50/60 p-3 text-sm"
                  >
                    <p className="font-semibold text-rose-900">{p.title}</p>
                    <p className="mt-0.5 text-xs text-rose-800/80">{p.detail}</p>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          {dossier.offers && dossier.offers.length > 0 ? (
            <section>
              <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-slate-900">
                <Building2 className="h-4 w-4 text-emerald-600" aria-hidden="true" />
                {dossier.verdict.label === 'REVIEW' ? 'Recommended support' : 'Approved cross-sell / up-sell offers'}
                <span className="text-xs font-normal text-slate-500">
                  · approved catalog only
                </span>
              </h3>
              <div className="grid gap-3 md:grid-cols-2">
                {dossier.offers.map((o) => (
                  <OfferCard key={o.offerId} offer={o} />
                ))}
              </div>
            </section>
          ) : null}
        </div>

        {/* Footer actions */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 bg-white px-6 py-4">
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <Phone className="h-3.5 w-3.5" aria-hidden="true" />
            RM to approve before customer contact.
          </div>
          <div className="flex flex-wrap gap-2">
            <ActionButton tone="ghost" label="Defer 7 days" />
            <ActionButton tone="danger" label="Reject" />
            <ActionButton tone="primary" label="Approve & contact" />
          </div>
        </div>
    </>
  )
}

function ChipStat({
  label,
  value,
  tone,
}: {
  label: string
  value: string
  tone: 'slate' | 'rose'
}) {
  const toneCls =
    tone === 'rose'
      ? 'border-rose-200 bg-rose-50 text-rose-700'
      : 'border-slate-200 bg-slate-50 text-slate-700'
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium',
        toneCls,
      )}
    >
      <span className="opacity-70">{label}</span>
      <span className="font-semibold">{value}</span>
    </span>
  )
}

function SnapshotCell({
  label,
  value,
  hint,
  valueClass,
}: {
  label: string
  value: string
  hint: string
  valueClass?: string
}) {
  return (
    <div className="rounded-lg border border-slate-100 bg-white p-2.5">
      <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
        {label}
      </p>
      <p
        className={cn(
          'mt-0.5 text-sm font-semibold tabular-nums text-slate-900',
          valueClass,
        )}
      >
        {value}
      </p>
      <p className="text-[10px] text-slate-500">{hint}</p>
    </div>
  )
}

function OfferCard({ offer }: { offer: CrossSellOffer }) {
  return (
    <article className="rounded-xl border border-emerald-200 bg-white p-3 shadow-sm">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-emerald-700">
            {offer.offerId}
          </p>
          <p className="mt-0.5 text-sm font-semibold text-slate-900">{offer.offerName}</p>
          <p className="text-[11px] text-slate-500">{offer.product}</p>
        </div>
        <div className="text-right">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
            P(accept)
          </p>
          <p className="text-base font-semibold text-emerald-700">{offer.acceptanceProb}%</p>
        </div>
      </div>
      <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
        <div
          className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-teal-400"
          style={{ width: `${offer.acceptanceProb}%` }}
        />
      </div>
      <p className="mt-2 text-xs text-slate-600">
        <span className="font-semibold text-slate-900">{offer.uplift}</span> — {offer.rationale}
      </p>
    </article>
  )
}

function ActionButton({
  label,
  tone,
}: {
  label: string
  tone: 'primary' | 'danger' | 'ghost'
}) {
  const classes = {
    primary:
      'bg-emerald-600 text-white hover:bg-emerald-700 focus-visible:ring-emerald-400 shadow-sm',
    danger:
      'bg-white text-rose-700 border border-rose-200 hover:bg-rose-50 focus-visible:ring-rose-400',
    ghost:
      'bg-white text-slate-700 border border-slate-200 hover:bg-slate-50 focus-visible:ring-slate-400',
  } as const
  return (
    <button
      type="button"
      className={cn(
        'inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
        classes[tone],
      )}
    >
      {label}
    </button>
  )
}
