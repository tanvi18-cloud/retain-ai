import { useMemo } from 'react'
import {
  Activity,
  ArrowDownRight,
  ArrowUpRight,
  Bot,
  CheckCircle2,
  Minus,
  Radar,
  Shield,
  Sparkles,
  TrendingUp,
  Users,
  Zap,
} from 'lucide-react'
import {
  Area,
  AreaChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
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
  headlineKpis,
  liveAlerts,
  matrixPoints,
  modelMetrics,
  priorityCustomers,
  retentionTrend,
  saveFunnel,
  segmentPerformance,
  type BenchmarkKpi,
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

      <div className="grid gap-6 xl:grid-cols-[1.3fr_1fr]">
        <SaveFunnelCard overallSavePct={overallSavePct} />
        <ModelPerformanceCard />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.6fr_1fr]">
        <RiskValueMatrixCard />
        <PriorityRailCard />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.4fr_1fr]">
        <SegmentPerformanceCard />
        <GuardrailsCard />
      </div>

      <ComplianceStrip />
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

        {/* Right: 2×2 compact KPI tiles */}
        <div className="grid grid-cols-2 gap-3">
          {headlineKpis.map((k, i) => (
            <div
              key={k.label}
              className={cn(
                'rounded-xl border border-slate-200 bg-slate-50/60 p-4',
                i === 0 && 'border-emerald-200 bg-emerald-50/60',
              )}
            >
              <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
                {k.label}
              </p>
              <p
                className={cn(
                  'mt-1.5 text-xl font-semibold tracking-tight text-slate-900 sm:text-2xl',
                  i === 0 && 'text-emerald-700',
                )}
              >
                {k.value}
              </p>
              <p className="mt-0.5 line-clamp-2 text-[11px] text-slate-500">{k.caption}</p>
            </div>
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

      <div className="h-72 w-full">
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
            <YAxis tick={{ fontSize: 11 }} stroke="#94a3b8" />
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
              type="monotone"
              dataKey="atRisk"
              name="At-risk detected"
              stroke="#f43f5e"
              fill="url(#atRiskGrad)"
              strokeWidth={2}
            />
            <Area
              type="monotone"
              dataKey="saved"
              name="Successfully retained"
              stroke="#10b981"
              fill="url(#savedGrad)"
              strokeWidth={2}
            />
            <Line
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
// Model performance
// ────────────────────────────────────────────────────────────────────────────

function ModelPerformanceCard() {
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

      <div className="h-60 w-full">
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

      <dl className="mt-3 grid grid-cols-2 gap-3 border-t border-slate-100 pt-3 text-xs">
        <div>
          <dt className="text-slate-500">Drift (7d)</dt>
          <dd className="font-semibold text-emerald-600">+0.4 pts · stable</dd>
        </div>
        <div>
          <dt className="text-slate-500">Decision explainability</dt>
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

  return (
    <article className="relative overflow-hidden rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <header className="mb-4">
        <div className="flex items-center gap-2">
          <Users className="h-4 w-4 text-emerald-600" aria-hidden="true" />
          <h3 className="text-base font-semibold text-slate-900">Risk × value portfolio map</h3>
        </div>
        <p className="mt-1 text-sm text-slate-500">
          Each point = one customer. Colour = retention decision · size = revenue at risk.
        </p>
      </header>

      <div className="grid gap-4 lg:grid-cols-[1fr_200px]">
        <div className="h-80 w-full">
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
              Legend
            </p>
            <ul className="space-y-1">
              {(Object.keys(DECISION_COLORS) as RecommendationDecision[]).map((d) => (
                <li key={d} className="flex items-center gap-2 text-xs text-slate-600">
                  <span
                    aria-hidden="true"
                    className="inline-block h-2.5 w-2.5 rounded-full"
                    style={{ backgroundColor: DECISION_COLORS[d] }}
                  />
                  {DECISION_LABELS[d]}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </article>
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

function PriorityRailCard() {
  return (
    <article className="relative overflow-hidden rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <header className="mb-3 flex items-center justify-between">
        <div>
          <h3 className="text-base font-semibold text-slate-900">Priority queue</h3>
          <p className="text-sm text-slate-500">Top 8 customers · awaiting RM action</p>
        </div>
        <LivePill />
      </header>

      <ul className="space-y-2.5">
        {priorityCustomers.map((c) => (
          <li
            key={c.id}
            className="group relative rounded-xl border border-slate-200 bg-white p-3 transition hover:border-emerald-200 hover:shadow-sm"
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
