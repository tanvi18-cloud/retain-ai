/**
 * Synthetic demo-dashboard data for RetainAI.
 *
 * All numbers are illustrative and based on publicly reported retail-banking
 * retention benchmarks (Bain, McKinsey, Qualtrics, CFI, J.D. Power). Nothing
 * here is sourced from real customers.
 *
 * Industry benchmarks used:
 *   - Annual retail-banking churn       : 11–15% (we beat with 7.8%)
 *   - Save rate on at-risk customers    : 40–55% average
 *   - Retention offer acceptance rate   : 25–35% average
 *   - Products per customer (PpC)       : 2.5–3.0 average
 *   - Retail-banking NPS                : ~34 average (industry median)
 *   - Churn model AUC                   : 0.75–0.85 production range
 */

import type { RecommendationDecision } from '../types/api'

// ─────────────────────────────────────────────────────────────────────────────
// Headline KPIs (hero + benchmark row)
// ─────────────────────────────────────────────────────────────────────────────

export interface HeadlineKpi {
  label: string
  value: string
  caption: string
  /** 12-month trend sparkline. */
  trend: number[]
  trendTone: 'positive' | 'neutral'
}

export const headlineKpis: HeadlineKpi[] = [
  {
    label: 'Portfolio AUM',
    value: '₹1,284 Cr',
    caption: 'Assets under RM management',
    trend: [1098, 1121, 1146, 1172, 1189, 1204, 1218, 1231, 1246, 1259, 1272, 1284],
    trendTone: 'positive',
  },
  {
    label: 'Customers covered',
    value: '12,480',
    caption: 'Across 4 segments · 6 regions',
    trend: [11_820, 11_880, 11_942, 12_006, 12_088, 12_154, 12_212, 12_271, 12_326, 12_388, 12_441, 12_480],
    trendTone: 'positive',
  },
  {
    label: 'Net retention rate',
    value: '94.2%',
    caption: 'Trailing 12 months · YoY +3.1 pts',
    trend: [91.1, 91.4, 91.8, 92.1, 92.4, 92.6, 92.9, 93.2, 93.5, 93.8, 94.0, 94.2],
    trendTone: 'positive',
  },
  {
    label: 'Revenue saved YTD',
    value: '₹46.8 Cr',
    caption: 'Attributed to agent-assisted saves',
    trend: [2.6, 5.7, 9.1, 12.7, 16.7, 21.0, 25.6, 30.0, 34.9, 40.1, 45.2, 46.8],
    trendTone: 'positive',
  },
]

export interface BenchmarkKpi {
  label: string
  value: string
  deltaLabel: string
  deltaDirection: 'up' | 'down' | 'flat'
  /** `good` means the delta direction is favourable for the business. */
  deltaIntent: 'good' | 'bad' | 'neutral'
  industryBenchmark: string
  description: string
}

export const benchmarkKpis: BenchmarkKpi[] = [
  {
    label: 'Annualised churn rate',
    value: '7.8%',
    deltaLabel: '−4.9 pts vs. industry',
    deltaDirection: 'down',
    deltaIntent: 'good',
    industryBenchmark: 'Industry 12.7% (Bain, 2024)',
    description: 'Rolling 12-month customer attrition across the managed book.',
  },
  {
    label: 'Save rate',
    value: '73.4%',
    deltaLabel: '+25.4 pts vs. industry',
    deltaDirection: 'up',
    deltaIntent: 'good',
    industryBenchmark: 'Industry 48% (J.D. Power)',
    description: 'At-risk customers retained after RM intervention.',
  },
  {
    label: 'Offer acceptance',
    value: '61.2%',
    deltaLabel: '+26.2 pts vs. industry',
    deltaDirection: 'up',
    deltaIntent: 'good',
    industryBenchmark: 'Industry 35% (McKinsey)',
    description: 'Approved retention offers accepted by customers.',
  },
  {
    label: 'Avg Customer Lifetime Value',
    value: '₹8.42 L',
    deltaLabel: '+18% vs. baseline',
    deltaDirection: 'up',
    deltaIntent: 'good',
    industryBenchmark: 'Baseline ₹7.14 L',
    description: 'Discounted lifetime revenue per retained customer.',
  },
  {
    label: 'Relationship NPS',
    value: '58',
    deltaLabel: '+24 vs. industry',
    deltaDirection: 'up',
    deltaIntent: 'good',
    industryBenchmark: 'Industry 34 (Qualtrics)',
    description: 'Transactional NPS after an RM-led retention conversation.',
  },
  {
    label: 'Avg response time',
    value: '2.4 h',
    deltaLabel: '−78% vs. SLA',
    deltaDirection: 'down',
    deltaIntent: 'good',
    industryBenchmark: 'SLA 11 h',
    description: 'Time from churn signal to first RM outreach.',
  },
]

// ─────────────────────────────────────────────────────────────────────────────
// Four-agent CrewAI activity
// ─────────────────────────────────────────────────────────────────────────────

export interface AgentStatus {
  id: string
  name: string
  role: string
  tasksToday: number
  successRate: number
  avgLatencySec: number
  model: string
  status: 'ACTIVE' | 'IDLE'
  lastDecision: string
  accent: string // tailwind gradient classes
}

export const agents: AgentStatus[] = [
  {
    id: 'retention-analyst',
    name: 'Retention Analyst',
    role: 'Interprets churn signals',
    tasksToday: 184,
    successRate: 98.4,
    avgLatencySec: 2.1,
    model: 'Qwen3-8B · guardrailed',
    status: 'ACTIVE',
    lastDecision: 'Flagged C-00412: 42% salary-inflow drop + external home-loan inquiry.',
    accent: 'from-indigo-500 via-violet-500 to-fuchsia-500',
  },
  {
    id: 'offer-strategist',
    name: 'Offer Strategist',
    role: 'Picks eligible approved offers',
    tasksToday: 142,
    successRate: 100.0,
    avgLatencySec: 1.4,
    model: 'Deterministic + Qwen3-8B',
    status: 'ACTIVE',
    lastDecision: 'Matched OFFER-HL-SWITCH-21 for C-00412 (eligibility verified).',
    accent: 'from-cyan-500 via-sky-500 to-indigo-500',
  },
  {
    id: 'risk-advisor',
    name: 'Risk Advisor',
    role: 'Surfaces policy warnings',
    tasksToday: 97,
    successRate: 99.1,
    avgLatencySec: 1.8,
    model: 'Rules engine · policy v4.2',
    status: 'ACTIVE',
    lastDecision: 'Blocked new lending for C-00761 (60 DPD) — repayment support only.',
    accent: 'from-amber-500 via-orange-500 to-rose-500',
  },
  {
    id: 'rm-communicator',
    name: 'RM Communicator',
    role: 'Drafts customer narrative',
    tasksToday: 128,
    successRate: 97.6,
    avgLatencySec: 3.2,
    model: 'Qwen3-8B · tone-tuned',
    status: 'ACTIVE',
    lastDecision: 'Drafted retention script for C-00412 — awaiting RM approval.',
    accent: 'from-emerald-500 via-teal-500 to-cyan-500',
  },
]

// ─────────────────────────────────────────────────────────────────────────────
// Retention performance — last 12 months
// ─────────────────────────────────────────────────────────────────────────────

export interface RetentionPoint {
  month: string
  atRisk: number
  saved: number
  revenueSavedCr: number
}

export const retentionTrend: RetentionPoint[] = [
  { month: 'Nov', atRisk: 182, saved: 118, revenueSavedCr: 2.6 },
  { month: 'Dec', atRisk: 196, saved: 134, revenueSavedCr: 3.1 },
  { month: 'Jan', atRisk: 211, saved: 148, revenueSavedCr: 3.4 },
  { month: 'Feb', atRisk: 204, saved: 151, revenueSavedCr: 3.6 },
  { month: 'Mar', atRisk: 221, saved: 168, revenueSavedCr: 4.0 },
  { month: 'Apr', atRisk: 234, saved: 179, revenueSavedCr: 4.3 },
  { month: 'May', atRisk: 242, saved: 191, revenueSavedCr: 4.6 },
  { month: 'Jun', atRisk: 228, saved: 182, revenueSavedCr: 4.4 },
  { month: 'Jul', atRisk: 251, saved: 203, revenueSavedCr: 4.9 },
  { month: 'Aug', atRisk: 263, saved: 214, revenueSavedCr: 5.2 },
  { month: 'Sep', atRisk: 258, saved: 212, revenueSavedCr: 5.1 },
  { month: 'Oct', atRisk: 247, saved: 211, revenueSavedCr: 5.6 },
]

// ─────────────────────────────────────────────────────────────────────────────
// Model performance (RadialBarChart)
// ─────────────────────────────────────────────────────────────────────────────

export interface ModelMetric {
  name: string
  value: number
  fill: string
}

export const modelMetrics: ModelMetric[] = [
  { name: 'AUC-ROC', value: 89, fill: '#047857' },
  { name: 'Precision', value: 84, fill: '#10b981' },
  { name: 'Recall', value: 81, fill: '#14b8a6' },
  { name: 'F1 score', value: 82, fill: '#f59e0b' },
]

// ─────────────────────────────────────────────────────────────────────────────
// Save funnel
// ─────────────────────────────────────────────────────────────────────────────

export interface FunnelStage {
  stage: string
  count: number
  description: string
}

export const saveFunnel: FunnelStage[] = [
  { stage: 'Signals detected', count: 1842, description: 'Bureau, CRM & transaction triggers' },
  { stage: 'Agent-analysed', count: 1687, description: 'Churn + value scored by rules engine' },
  { stage: 'Eligible offer matched', count: 1142, description: 'Approved catalog only' },
  { stage: 'RM approved', count: 964, description: 'Human-in-the-loop sign-off' },
  { stage: 'Customer contacted', count: 891, description: 'Email / phone / SMS outreach' },
  { stage: 'Retained', count: 654, description: 'Positive customer response captured' },
]

// ─────────────────────────────────────────────────────────────────────────────
// Risk × value matrix (scatter)
// ─────────────────────────────────────────────────────────────────────────────

export interface MatrixPoint {
  customer_id: string
  full_name: string
  churn_score: number
  value_score: number
  revenue_at_risk: number // INR
  decision: RecommendationDecision
}

// ~56 realistic-looking points spread across the four quadrants so the chart feels dense.
export const matrixPoints: MatrixPoint[] = [
  { customer_id: 'C-00412', full_name: 'Aarav Mehta', churn_score: 88, value_score: 91, revenue_at_risk: 4_200_000, decision: 'RETAIN' },
  { customer_id: 'C-00761', full_name: 'Priya Shah', churn_score: 82, value_score: 72, revenue_at_risk: 2_800_000, decision: 'RETAIN' },
  { customer_id: 'C-01204', full_name: 'Rohan Verma', churn_score: 79, value_score: 86, revenue_at_risk: 3_600_000, decision: 'RETAIN' },
  { customer_id: 'C-00318', full_name: 'Ananya Nair', churn_score: 76, value_score: 69, revenue_at_risk: 2_100_000, decision: 'RETAIN' },
  { customer_id: 'C-00927', full_name: 'Vikram Rao', churn_score: 72, value_score: 83, revenue_at_risk: 3_100_000, decision: 'RETAIN' },
  { customer_id: 'C-01566', full_name: 'Isha Kapoor', churn_score: 70, value_score: 61, revenue_at_risk: 1_900_000, decision: 'RETAIN' },
  { customer_id: 'C-01887', full_name: 'Siddharth Jain', churn_score: 68, value_score: 55, revenue_at_risk: 1_400_000, decision: 'RETAIN' },
  { customer_id: 'C-02041', full_name: 'Meera Iyer', churn_score: 66, value_score: 78, revenue_at_risk: 2_600_000, decision: 'RETAIN' },

  { customer_id: 'C-00533', full_name: 'Kabir Singh', churn_score: 58, value_score: 72, revenue_at_risk: 1_600_000, decision: 'REVIEW' },
  { customer_id: 'C-00698', full_name: 'Riya Deshmukh', churn_score: 54, value_score: 65, revenue_at_risk: 1_200_000, decision: 'REVIEW' },
  { customer_id: 'C-00812', full_name: 'Aditya Pillai', churn_score: 51, value_score: 58, revenue_at_risk: 980_000, decision: 'REVIEW' },
  { customer_id: 'C-01123', full_name: 'Sneha Reddy', churn_score: 49, value_score: 71, revenue_at_risk: 1_050_000, decision: 'REVIEW' },
  { customer_id: 'C-01345', full_name: 'Arjun Khanna', churn_score: 47, value_score: 61, revenue_at_risk: 860_000, decision: 'REVIEW' },
  { customer_id: 'C-01611', full_name: 'Divya Bose', churn_score: 44, value_score: 55, revenue_at_risk: 720_000, decision: 'REVIEW' },
  { customer_id: 'C-01788', full_name: 'Nikhil Menon', churn_score: 42, value_score: 68, revenue_at_risk: 940_000, decision: 'REVIEW' },
  { customer_id: 'C-01902', full_name: 'Pooja Agarwal', churn_score: 40, value_score: 52, revenue_at_risk: 610_000, decision: 'REVIEW' },

  { customer_id: 'C-02187', full_name: 'Harsh Vora', churn_score: 36, value_score: 48, revenue_at_risk: 420_000, decision: 'MONITOR' },
  { customer_id: 'C-02233', full_name: 'Kavya Mishra', churn_score: 34, value_score: 44, revenue_at_risk: 360_000, decision: 'MONITOR' },
  { customer_id: 'C-02301', full_name: 'Rahul Chopra', churn_score: 32, value_score: 51, revenue_at_risk: 390_000, decision: 'MONITOR' },
  { customer_id: 'C-02389', full_name: 'Tanvi Saxena', churn_score: 30, value_score: 38, revenue_at_risk: 290_000, decision: 'MONITOR' },
  { customer_id: 'C-02412', full_name: 'Yash Bhatt', churn_score: 28, value_score: 46, revenue_at_risk: 310_000, decision: 'MONITOR' },
  { customer_id: 'C-02501', full_name: 'Neha Gill', churn_score: 26, value_score: 34, revenue_at_risk: 230_000, decision: 'MONITOR' },
  { customer_id: 'C-02566', full_name: 'Dev Patel', churn_score: 24, value_score: 42, revenue_at_risk: 260_000, decision: 'MONITOR' },
  { customer_id: 'C-02611', full_name: 'Simran Kaur', churn_score: 22, value_score: 29, revenue_at_risk: 180_000, decision: 'MONITOR' },

  { customer_id: 'C-02701', full_name: 'Aryan Dubey', churn_score: 18, value_score: 71, revenue_at_risk: 140_000, decision: 'NO_ACTION' },
  { customer_id: 'C-02766', full_name: 'Zara Khan', churn_score: 16, value_score: 83, revenue_at_risk: 120_000, decision: 'NO_ACTION' },
  { customer_id: 'C-02801', full_name: 'Reyansh Gupta', churn_score: 15, value_score: 62, revenue_at_risk: 90_000, decision: 'NO_ACTION' },
  { customer_id: 'C-02854', full_name: 'Ishaan Yadav', churn_score: 14, value_score: 55, revenue_at_risk: 80_000, decision: 'NO_ACTION' },
  { customer_id: 'C-02898', full_name: 'Aarohi Sinha', churn_score: 12, value_score: 48, revenue_at_risk: 70_000, decision: 'NO_ACTION' },
  { customer_id: 'C-02941', full_name: 'Mihir Joshi', churn_score: 10, value_score: 72, revenue_at_risk: 60_000, decision: 'NO_ACTION' },
  { customer_id: 'C-02988', full_name: 'Saanvi Rao', churn_score: 9, value_score: 36, revenue_at_risk: 50_000, decision: 'NO_ACTION' },
  { customer_id: 'C-03011', full_name: 'Krish Trivedi', churn_score: 7, value_score: 58, revenue_at_risk: 40_000, decision: 'NO_ACTION' },

  // additional density
  { customer_id: 'C-03101', full_name: 'Lavanya Pai', churn_score: 85, value_score: 94, revenue_at_risk: 4_800_000, decision: 'RETAIN' },
  { customer_id: 'C-03122', full_name: 'Dhruv Malhotra', churn_score: 65, value_score: 88, revenue_at_risk: 3_300_000, decision: 'RETAIN' },
  { customer_id: 'C-03145', full_name: 'Avni Shetty', churn_score: 55, value_score: 69, revenue_at_risk: 1_300_000, decision: 'REVIEW' },
  { customer_id: 'C-03166', full_name: 'Pranav Das', churn_score: 48, value_score: 54, revenue_at_risk: 820_000, decision: 'REVIEW' },
  { customer_id: 'C-03188', full_name: 'Myra Kulkarni', churn_score: 38, value_score: 41, revenue_at_risk: 340_000, decision: 'MONITOR' },
  { customer_id: 'C-03201', full_name: 'Vihaan Chawla', churn_score: 20, value_score: 65, revenue_at_risk: 110_000, decision: 'NO_ACTION' },
  { customer_id: 'C-03234', full_name: 'Anika Bhat', churn_score: 73, value_score: 77, revenue_at_risk: 2_700_000, decision: 'RETAIN' },
  { customer_id: 'C-03266', full_name: 'Shaurya Lal', churn_score: 61, value_score: 63, revenue_at_risk: 1_500_000, decision: 'RETAIN' },
  { customer_id: 'C-03288', full_name: 'Diya Suri', churn_score: 46, value_score: 76, revenue_at_risk: 1_000_000, decision: 'REVIEW' },
  { customer_id: 'C-03301', full_name: 'Yuvraj Khurana', churn_score: 33, value_score: 55, revenue_at_risk: 410_000, decision: 'MONITOR' },
  { customer_id: 'C-03322', full_name: 'Ira Mahajan', churn_score: 25, value_score: 81, revenue_at_risk: 170_000, decision: 'NO_ACTION' },
  { customer_id: 'C-03345', full_name: 'Advait Rai', churn_score: 59, value_score: 70, revenue_at_risk: 1_700_000, decision: 'RETAIN' },
  { customer_id: 'C-03366', full_name: 'Mahira Sood', churn_score: 43, value_score: 59, revenue_at_risk: 780_000, decision: 'REVIEW' },
  { customer_id: 'C-03388', full_name: 'Reyaan Oberoi', churn_score: 29, value_score: 44, revenue_at_risk: 280_000, decision: 'MONITOR' },
  { customer_id: 'C-03401', full_name: 'Kiara Bhalla', churn_score: 11, value_score: 68, revenue_at_risk: 95_000, decision: 'NO_ACTION' },
  { customer_id: 'C-03422', full_name: 'Veer Chowdhary', churn_score: 77, value_score: 65, revenue_at_risk: 2_400_000, decision: 'RETAIN' },
  { customer_id: 'C-03444', full_name: 'Nitara Sen', churn_score: 50, value_score: 48, revenue_at_risk: 700_000, decision: 'REVIEW' },
  { customer_id: 'C-03466', full_name: 'Aarush Vyas', churn_score: 37, value_score: 60, revenue_at_risk: 500_000, decision: 'MONITOR' },
  { customer_id: 'C-03488', full_name: 'Siya Mathur', churn_score: 19, value_score: 54, revenue_at_risk: 130_000, decision: 'NO_ACTION' },
  { customer_id: 'C-03511', full_name: 'Arnav Grover', churn_score: 69, value_score: 58, revenue_at_risk: 1_800_000, decision: 'RETAIN' },
  { customer_id: 'C-03533', full_name: 'Pari Dhawan', churn_score: 41, value_score: 73, revenue_at_risk: 900_000, decision: 'REVIEW' },
  { customer_id: 'C-03555', full_name: 'Rudra Thakur', churn_score: 31, value_score: 39, revenue_at_risk: 320_000, decision: 'MONITOR' },
  { customer_id: 'C-03577', full_name: 'Anvi Chauhan', churn_score: 13, value_score: 42, revenue_at_risk: 75_000, decision: 'NO_ACTION' },
]

// ─────────────────────────────────────────────────────────────────────────────
// Top priority customers (table-ish list for the right rail)
// ─────────────────────────────────────────────────────────────────────────────

export interface PriorityCustomer {
  id: string
  name: string
  segment: 'PRIVATE' | 'PRIORITY' | 'MASS_AFFLUENT' | 'STANDARD'
  priority: number
  revenueAtRiskLakh: number
  trigger: string
  offer: string
  decision: RecommendationDecision
}

export const priorityCustomers: PriorityCustomer[] = [
  { id: 'C-00412', name: 'Aarav Mehta', segment: 'PRIVATE', priority: 94, revenueAtRiskLakh: 42.0, trigger: 'External home-loan inquiry', offer: 'OFFER-HL-SWITCH-21', decision: 'RETAIN' },
  { id: 'C-03101', name: 'Lavanya Pai', segment: 'PRIVATE', priority: 92, revenueAtRiskLakh: 48.0, trigger: 'Salary inflow stopped', offer: 'OFFER-RELATIONSHIP-02', decision: 'RETAIN' },
  { id: 'C-01204', name: 'Rohan Verma', segment: 'PRIORITY', priority: 88, revenueAtRiskLakh: 36.0, trigger: 'Forex spend spike + travel card', offer: 'OFFER-TRAVEL-15', decision: 'RETAIN' },
  { id: 'C-00761', name: 'Priya Shah', segment: 'PRIORITY', priority: 85, revenueAtRiskLakh: 28.0, trigger: 'FD maturing in 14 days', offer: 'OFFER-FD-RENEW-07', decision: 'RETAIN' },
  { id: 'C-00927', name: 'Vikram Rao', segment: 'PRIORITY', priority: 82, revenueAtRiskLakh: 31.0, trigger: 'Credit utilisation 94%', offer: 'OFFER-CARD-LIMIT-04', decision: 'RETAIN' },
  { id: 'C-03234', name: 'Anika Bhat', segment: 'PRIORITY', priority: 80, revenueAtRiskLakh: 27.0, trigger: 'Competitor transfer ₹8.4 L', offer: 'OFFER-SAVE-PLUS-11', decision: 'RETAIN' },
  { id: 'C-00318', name: 'Ananya Nair', segment: 'MASS_AFFLUENT', priority: 78, revenueAtRiskLakh: 21.0, trigger: 'External home-loan inquiry', offer: 'OFFER-HL-SWITCH-21', decision: 'RETAIN' },
  { id: 'C-01566', name: 'Isha Kapoor', segment: 'MASS_AFFLUENT', priority: 75, revenueAtRiskLakh: 19.0, trigger: 'Card spend −62% QoQ', offer: 'OFFER-CARD-REWARDS-09', decision: 'RETAIN' },
]

// ─────────────────────────────────────────────────────────────────────────────
// Live alert ticker
// ─────────────────────────────────────────────────────────────────────────────

export interface LiveAlert {
  id: string
  customerId: string
  text: string
  minutesAgo: number
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM'
}

export const liveAlerts: LiveAlert[] = [
  { id: 'A-9821', customerId: 'C-00412', text: 'External home-loan inquiry — ₹1.2 Cr', minutesAgo: 2, severity: 'CRITICAL' },
  { id: 'A-9820', customerId: 'C-03101', text: 'Salary credit paused for 2 cycles', minutesAgo: 7, severity: 'CRITICAL' },
  { id: 'A-9819', customerId: 'C-00761', text: 'Fixed deposit maturing in 14 days', minutesAgo: 14, severity: 'HIGH' },
  { id: 'A-9818', customerId: 'C-01204', text: 'Forex spend ₹3.1 L in 30 days', minutesAgo: 22, severity: 'HIGH' },
  { id: 'A-9817', customerId: 'C-00927', text: 'Credit utilisation crossed 90%', minutesAgo: 31, severity: 'HIGH' },
  { id: 'A-9816', customerId: 'C-03234', text: 'Outbound transfer to competitor bank', minutesAgo: 46, severity: 'MEDIUM' },
]

// ─────────────────────────────────────────────────────────────────────────────
// Segment-level retention
// ─────────────────────────────────────────────────────────────────────────────

export interface SegmentRow {
  segment: 'PRIVATE' | 'PRIORITY' | 'MASS_AFFLUENT' | 'STANDARD'
  customers: number
  retentionPct: number
  revenueAtRiskCr: number
  productsPerCustomer: number
}

export const segmentPerformance: SegmentRow[] = [
  { segment: 'PRIVATE', customers: 184, retentionPct: 97.8, revenueAtRiskCr: 6.4, productsPerCustomer: 4.6 },
  { segment: 'PRIORITY', customers: 1240, retentionPct: 95.2, revenueAtRiskCr: 11.8, productsPerCustomer: 3.8 },
  { segment: 'MASS_AFFLUENT', customers: 3860, retentionPct: 93.1, revenueAtRiskCr: 14.2, productsPerCustomer: 2.9 },
  { segment: 'STANDARD', customers: 7196, retentionPct: 91.4, revenueAtRiskCr: 14.4, productsPerCustomer: 2.1 },
]

// ─────────────────────────────────────────────────────────────────────────────
// Channel performance (comms channel save-rate benchmark)
// ─────────────────────────────────────────────────────────────────────────────

export interface ChannelRow {
  channel: 'Phone' | 'Email' | 'In-app' | 'SMS'
  contacted: number
  retained: number
  saveRatePct: number
  avgResponseHours: number
}

export const channelPerformance: ChannelRow[] = [
  { channel: 'Phone', contacted: 412, retained: 338, saveRatePct: 82.0, avgResponseHours: 1.4 },
  { channel: 'In-app', contacted: 268, retained: 198, saveRatePct: 73.9, avgResponseHours: 0.6 },
  { channel: 'Email', contacted: 621, retained: 403, saveRatePct: 64.9, avgResponseHours: 4.8 },
  { channel: 'SMS', contacted: 184, retained: 103, saveRatePct: 56.0, avgResponseHours: 2.1 },
]

// ─────────────────────────────────────────────────────────────────────────────
// Model drift (14-day AUC trend for the churn model)
// ─────────────────────────────────────────────────────────────────────────────

export const modelDrift14d: { day: number; auc: number }[] = [
  { day: 1, auc: 88.1 },
  { day: 2, auc: 88.4 },
  { day: 3, auc: 88.6 },
  { day: 4, auc: 88.2 },
  { day: 5, auc: 88.5 },
  { day: 6, auc: 88.8 },
  { day: 7, auc: 89.0 },
  { day: 8, auc: 88.9 },
  { day: 9, auc: 89.1 },
  { day: 10, auc: 89.3 },
  { day: 11, auc: 89.0 },
  { day: 12, auc: 89.2 },
  { day: 13, auc: 88.9 },
  { day: 14, auc: 89.0 },
]

// ─────────────────────────────────────────────────────────────────────────────
// Cohort retention — 8 monthly cohorts × 8 months since join (lower-left is "future")
// ─────────────────────────────────────────────────────────────────────────────

export interface CohortRow {
  cohort: string
  customers: number
  /** Retention % by month index (0 = joining month). `null` = cohort too young. */
  retention: (number | null)[]
}

// ─────────────────────────────────────────────────────────────────────────────
// Customer dossier (what the modal shows when a priority customer is clicked)
// ─────────────────────────────────────────────────────────────────────────────

export type DossierVerdict = 'RETAIN' | 'REVIEW' | 'DO_NOT_RETAIN'

export interface RedFlag {
  severity: 'HIGH' | 'MEDIUM' | 'LOW'
  label: string
  detail: string
}

export interface CrossSellOffer {
  offerId: string
  offerName: string
  product: string
  uplift: string
  acceptanceProb: number
  rationale: string
}

export interface PolicyBlock {
  title: string
  detail: string
}

export interface CustomerDossier {
  id: string
  name: string
  segment: 'PRIVATE' | 'PRIORITY' | 'MASS_AFFLUENT' | 'STANDARD'
  priority: number
  relationshipYears: number
  preferredChannel: 'Phone' | 'Email' | 'SMS' | 'In-app'
  revenueAtRiskLakh: number
  churnScore: number
  valueScore: number
  verdict: {
    label: DossierVerdict
    headline: string
    reasons: string[]
  }
  redFlags: RedFlag[]
  credit: {
    creditScore: number
    scoreBand: 'EXCELLENT' | 'GOOD' | 'FAIR' | 'POOR'
    maxDpd12m: number
    utilizationPct: number
    activeLoans: number
    recentInquiries: number
    defaultFlag: boolean
  }
  banking: {
    currentBalanceLakh: number
    avgBalance90dLakh: number
    salaryAccount: boolean
    salaryReceivedThisMonth: boolean
    monthlyInflowLakh: number
    monthlyOutflowLakh: number
    balanceChange30dPct: number
    cardSpendChangePct: number
    forexSpend30dLakh: number
    competitorTransferDetected: boolean
    productInactivityDays: number
  }
  offers?: CrossSellOffer[]
  policyBlocks?: PolicyBlock[]
}

export const customerDossiers: Record<string, CustomerDossier> = {
  'C-00412': {
    id: 'C-00412',
    name: 'Aarav Mehta',
    segment: 'PRIVATE',
    priority: 94,
    relationshipYears: 11,
    preferredChannel: 'Phone',
    revenueAtRiskLakh: 42.0,
    churnScore: 88,
    valueScore: 91,
    verdict: {
      label: 'RETAIN',
      headline: 'High-value customer actively shopping a home loan externally. Retain with switch offer.',
      reasons: [
        'External home-loan inquiry detected via bureau trigger (₹1.2 Cr, HFC-category 2).',
        'Credit profile excellent (CIBIL 812, 0 DPD, utilisation 18%).',
        'Private-segment customer · ₹42 L lifetime revenue · 11-year relationship.',
        'Fully eligible for the OFFER-HL-SWITCH-21 approved offer catalog.',
      ],
    },
    redFlags: [
      { severity: 'HIGH', label: 'External home-loan inquiry', detail: 'Bureau pulled 4 days ago · ₹1.2 Cr tenure 20 yr' },
      { severity: 'MEDIUM', label: 'Falling card spend', detail: 'Card spend down 38% QoQ — attention drift signal' },
    ],
    credit: {
      creditScore: 812,
      scoreBand: 'EXCELLENT',
      maxDpd12m: 0,
      utilizationPct: 18,
      activeLoans: 1,
      recentInquiries: 2,
      defaultFlag: false,
    },
    banking: {
      currentBalanceLakh: 62.4,
      avgBalance90dLakh: 71.8,
      salaryAccount: true,
      salaryReceivedThisMonth: true,
      monthlyInflowLakh: 8.4,
      monthlyOutflowLakh: 7.1,
      balanceChange30dPct: -13.1,
      cardSpendChangePct: -38,
      forexSpend30dLakh: 1.2,
      competitorTransferDetected: false,
      productInactivityDays: 0,
    },
    offers: [
      {
        offerId: 'OFFER-HL-SWITCH-21',
        offerName: 'Home loan switch @ 8.35% + processing fee waiver',
        product: 'Home loan',
        uplift: '+₹5.2 L lifetime value',
        acceptanceProb: 71,
        rationale: '72 bps below the external quote he received. Zero DPD, 11-yr relationship — approved tier A.',
      },
      {
        offerId: 'OFFER-WEALTH-07',
        offerName: 'Private-wealth portfolio review',
        product: 'Wealth management',
        uplift: '+₹2.8 L fee uplift',
        acceptanceProb: 48,
        rationale: 'Private-segment with ₹62 L idle balance — complementary conversation to the HL offer.',
      },
    ],
  },

  'C-03101': {
    id: 'C-03101',
    name: 'Lavanya Pai',
    segment: 'PRIVATE',
    priority: 92,
    relationshipYears: 8,
    preferredChannel: 'Phone',
    revenueAtRiskLakh: 48.0,
    churnScore: 85,
    valueScore: 94,
    verdict: {
      label: 'RETAIN',
      headline: 'Salary inflow stopped 2 cycles — likely job change. Retain through relationship offer + investigation.',
      reasons: [
        'No salary credit for 62 days (last credit ₹4.8 L / cycle).',
        'Average 90-day balance dropped 41% in last 30 days.',
        'Credit profile strong (CIBIL 798, 0 DPD, 1 active loan).',
        'High strategic value — ₹48 L exposure, 8-yr relationship.',
      ],
    },
    redFlags: [
      { severity: 'HIGH', label: 'Salary credit paused', detail: 'No inflow for 2 cycles — potential job change or employer switch' },
      { severity: 'HIGH', label: 'Balance decay', detail: '90-day avg balance down 41% · ₹18.4 L moved out in last 30 days' },
      { severity: 'MEDIUM', label: 'Login frequency down', detail: 'App logins down 68% QoQ' },
    ],
    credit: {
      creditScore: 798,
      scoreBand: 'EXCELLENT',
      maxDpd12m: 0,
      utilizationPct: 22,
      activeLoans: 1,
      recentInquiries: 1,
      defaultFlag: false,
    },
    banking: {
      currentBalanceLakh: 11.6,
      avgBalance90dLakh: 19.8,
      salaryAccount: true,
      salaryReceivedThisMonth: false,
      monthlyInflowLakh: 0.4,
      monthlyOutflowLakh: 2.9,
      balanceChange30dPct: -41.3,
      cardSpendChangePct: -12,
      forexSpend30dLakh: 0.2,
      competitorTransferDetected: true,
      productInactivityDays: 18,
    },
    offers: [
      {
        offerId: 'OFFER-RELATIONSHIP-02',
        offerName: 'Relationship upgrade — fee-free Private banking refresh',
        product: 'Relationship / wealth',
        uplift: '+₹3.4 L retained value',
        acceptanceProb: 58,
        rationale: 'Private-segment retention play — reinforces benefits before employer-driven churn finalises.',
      },
      {
        offerId: 'OFFER-SAVE-PLUS-11',
        offerName: 'Save+ sweep account @ 6.1% effective yield',
        product: 'Savings',
        uplift: '+₹0.9 L deposit uplift',
        acceptanceProb: 44,
        rationale: 'Idle ₹11.6 L balance deserves a yield story — pairs with retention outreach.',
      },
    ],
  },

  'C-01204': {
    id: 'C-01204',
    name: 'Rohan Verma',
    segment: 'PRIORITY',
    priority: 88,
    relationshipYears: 6,
    preferredChannel: 'Email',
    revenueAtRiskLakh: 36.0,
    churnScore: 79,
    valueScore: 86,
    verdict: {
      label: 'RETAIN',
      headline: 'High forex spend + travel card inactivity. Retain with upgraded travel card.',
      reasons: [
        'Forex spend ₹3.1 L in last 30 days (across 2 countries).',
        'Current travel card inactive 48 days.',
        'Credit profile good (CIBIL 764, 0 DPD).',
        'OFFER-TRAVEL-15 approved — zero forex markup + lounge access.',
      ],
    },
    redFlags: [
      { severity: 'HIGH', label: 'External forex spend spike', detail: '₹3.1 L spent via non-bank wallet in last 30 days' },
      { severity: 'MEDIUM', label: 'Travel card dormant', detail: 'No swipe for 48 days — competitor card likely active' },
    ],
    credit: {
      creditScore: 764,
      scoreBand: 'GOOD',
      maxDpd12m: 0,
      utilizationPct: 34,
      activeLoans: 2,
      recentInquiries: 1,
      defaultFlag: false,
    },
    banking: {
      currentBalanceLakh: 18.2,
      avgBalance90dLakh: 17.4,
      salaryAccount: true,
      salaryReceivedThisMonth: true,
      monthlyInflowLakh: 3.6,
      monthlyOutflowLakh: 3.2,
      balanceChange30dPct: 4.6,
      cardSpendChangePct: 12,
      forexSpend30dLakh: 3.1,
      competitorTransferDetected: false,
      productInactivityDays: 48,
    },
    offers: [
      {
        offerId: 'OFFER-TRAVEL-15',
        offerName: 'Platinum travel card — 0% forex markup + 8 lounge visits',
        product: 'Credit card',
        uplift: '+₹1.6 L interchange + fee',
        acceptanceProb: 67,
        rationale: 'Direct substitute for the competitor card the forex pattern suggests.',
      },
    ],
  },

  'C-00761': {
    id: 'C-00761',
    name: 'Priya Shah',
    segment: 'PRIORITY',
    priority: 85,
    relationshipYears: 9,
    preferredChannel: 'Phone',
    revenueAtRiskLakh: 28.0,
    churnScore: 82,
    valueScore: 72,
    verdict: {
      label: 'RETAIN',
      headline: 'Fixed deposit of ₹22 L maturing in 14 days. Retain with renewal + step-up offer.',
      reasons: [
        'FD-847 maturing 22 Oct · principal ₹22 L.',
        'No renewal instructions on file — passive churn risk.',
        'Clean credit (CIBIL 751, 0 DPD).',
        'OFFER-FD-RENEW-07 pre-approved · +25 bps step-up.',
      ],
    },
    redFlags: [
      { severity: 'HIGH', label: 'FD maturing · no auto-renew', detail: '₹22 L matures in 14 days — competitor banks will outbid' },
      { severity: 'LOW', label: 'Reduced engagement', detail: 'Branch visits down 60% YoY — but digital usage steady' },
    ],
    credit: {
      creditScore: 751,
      scoreBand: 'GOOD',
      maxDpd12m: 0,
      utilizationPct: 11,
      activeLoans: 0,
      recentInquiries: 0,
      defaultFlag: false,
    },
    banking: {
      currentBalanceLakh: 9.8,
      avgBalance90dLakh: 9.4,
      salaryAccount: false,
      salaryReceivedThisMonth: false,
      monthlyInflowLakh: 1.1,
      monthlyOutflowLakh: 0.9,
      balanceChange30dPct: 4.2,
      cardSpendChangePct: -3,
      forexSpend30dLakh: 0,
      competitorTransferDetected: false,
      productInactivityDays: 12,
    },
    offers: [
      {
        offerId: 'OFFER-FD-RENEW-07',
        offerName: 'FD renewal @ 7.65% + 25 bps loyalty step-up',
        product: 'Fixed deposit',
        uplift: '+₹1.8 L retained interest income',
        acceptanceProb: 74,
        rationale: '9-year relationship · competitor FD rates currently at 7.4% — clear price advantage.',
      },
    ],
  },

  'C-00927': {
    id: 'C-00927',
    name: 'Vikram Rao',
    segment: 'PRIORITY',
    priority: 82,
    relationshipYears: 7,
    preferredChannel: 'Phone',
    revenueAtRiskLakh: 31.0,
    churnScore: 72,
    valueScore: 83,
    verdict: {
      label: 'REVIEW',
      headline: 'Credit stress rising. Do NOT upsell new credit — offer repayment support instead.',
      reasons: [
        'Credit utilisation at 94% across 2 cards.',
        'Max DPD of 32 days in last 12 months (card EMI).',
        'Two recent credit inquiries at other banks — likely consolidating debt.',
        'Policy v4.2 blocks new lending offers while max DPD > 30.',
      ],
    },
    redFlags: [
      { severity: 'HIGH', label: 'Credit utilisation 94%', detail: 'Both primary + supplementary cards near limit' },
      { severity: 'HIGH', label: 'Past DPD', detail: '32 DPD on card EMI (May) · remediated but visible on bureau' },
      { severity: 'MEDIUM', label: 'External debt inquiries', detail: '2 enquiries from NBFCs in last 30 days — refinance likely' },
    ],
    credit: {
      creditScore: 684,
      scoreBand: 'FAIR',
      maxDpd12m: 32,
      utilizationPct: 94,
      activeLoans: 3,
      recentInquiries: 2,
      defaultFlag: false,
    },
    banking: {
      currentBalanceLakh: 2.6,
      avgBalance90dLakh: 5.1,
      salaryAccount: true,
      salaryReceivedThisMonth: true,
      monthlyInflowLakh: 2.4,
      monthlyOutflowLakh: 2.6,
      balanceChange30dPct: -48.9,
      cardSpendChangePct: 61,
      forexSpend30dLakh: 0,
      competitorTransferDetected: false,
      productInactivityDays: 0,
    },
    policyBlocks: [
      {
        title: 'No new lending offers',
        detail: 'Policy v4.2 blocks new credit while max DPD in trailing 12 months > 30 days.',
      },
      {
        title: 'Risk Advisor flag',
        detail: 'Agent flagged — surface balance consolidation / counselling only. RM to validate.',
      },
    ],
    offers: [
      {
        offerId: 'OFFER-RESTRUCTURE-02',
        offerName: 'Debt restructure — EMI holiday + consolidated 24-mo plan',
        product: 'Loan servicing',
        uplift: 'Preserves 7-yr relationship',
        acceptanceProb: 62,
        rationale: 'Repayment support only. Keeps the customer whole without extending new credit.',
      },
    ],
  },

  'C-03234': {
    id: 'C-03234',
    name: 'Anika Bhat',
    segment: 'PRIORITY',
    priority: 80,
    relationshipYears: 5,
    preferredChannel: 'In-app',
    revenueAtRiskLakh: 27.0,
    churnScore: 73,
    valueScore: 77,
    verdict: {
      label: 'RETAIN',
      headline: 'Large outbound transfer to competitor bank. Retain with Save+ yield story.',
      reasons: [
        '₹8.4 L transferred to competitor neo-bank in last 14 days.',
        'Credit profile strong (CIBIL 772, 0 DPD).',
        'High digital engagement — in-app channel preferred.',
        'OFFER-SAVE-PLUS-11 pre-approved · competitive yield.',
      ],
    },
    redFlags: [
      { severity: 'HIGH', label: 'Competitor transfer', detail: '₹8.4 L moved out in 14 days to a neo-bank beneficiary' },
      { severity: 'MEDIUM', label: 'Yield-seeking behaviour', detail: 'Searched "best savings account 2026" twice in-app' },
    ],
    credit: {
      creditScore: 772,
      scoreBand: 'GOOD',
      maxDpd12m: 0,
      utilizationPct: 27,
      activeLoans: 1,
      recentInquiries: 0,
      defaultFlag: false,
    },
    banking: {
      currentBalanceLakh: 6.2,
      avgBalance90dLakh: 14.6,
      salaryAccount: true,
      salaryReceivedThisMonth: true,
      monthlyInflowLakh: 2.9,
      monthlyOutflowLakh: 2.4,
      balanceChange30dPct: -57.5,
      cardSpendChangePct: 4,
      forexSpend30dLakh: 0.1,
      competitorTransferDetected: true,
      productInactivityDays: 3,
    },
    offers: [
      {
        offerId: 'OFFER-SAVE-PLUS-11',
        offerName: 'Save+ sweep account @ 6.1% effective yield',
        product: 'Savings',
        uplift: '+₹1.1 L deposit uplift',
        acceptanceProb: 69,
        rationale: 'Directly answers the yield-seeking signal · matches the competitor product she just funded.',
      },
      {
        offerId: 'OFFER-WEALTH-STARTER-04',
        offerName: 'Mutual-fund starter · zero AMC first year',
        product: 'Investments',
        uplift: '+₹0.6 L AUM uplift',
        acceptanceProb: 41,
        rationale: 'High digital engagement + idle cash — natural first-time investment conversation.',
      },
    ],
  },

  'C-00318': {
    id: 'C-00318',
    name: 'Ananya Nair',
    segment: 'MASS_AFFLUENT',
    priority: 78,
    relationshipYears: 4,
    preferredChannel: 'Email',
    revenueAtRiskLakh: 21.0,
    churnScore: 76,
    valueScore: 69,
    verdict: {
      label: 'RETAIN',
      headline: 'Early-stage home-loan shopping. Retain with pre-approved sanction letter.',
      reasons: [
        'Bureau showed 1 HFC inquiry (soft pull) 8 days ago.',
        'Clean credit (CIBIL 741, 0 DPD).',
        'Steady salary inflow of ₹2.6 L/month.',
        'OFFER-HL-SWITCH-21 fully eligible.',
      ],
    },
    redFlags: [
      { severity: 'MEDIUM', label: 'External home-loan inquiry', detail: 'Soft pull from HFC — early shopping stage' },
      { severity: 'LOW', label: 'Mortgage calculator usage', detail: '3 sessions in in-app loan calculator over past week' },
    ],
    credit: {
      creditScore: 741,
      scoreBand: 'GOOD',
      maxDpd12m: 0,
      utilizationPct: 29,
      activeLoans: 0,
      recentInquiries: 1,
      defaultFlag: false,
    },
    banking: {
      currentBalanceLakh: 4.8,
      avgBalance90dLakh: 4.1,
      salaryAccount: true,
      salaryReceivedThisMonth: true,
      monthlyInflowLakh: 2.6,
      monthlyOutflowLakh: 2.1,
      balanceChange30dPct: 7.4,
      cardSpendChangePct: 9,
      forexSpend30dLakh: 0,
      competitorTransferDetected: false,
      productInactivityDays: 1,
    },
    offers: [
      {
        offerId: 'OFFER-HL-SWITCH-21',
        offerName: 'Pre-approved home-loan sanction @ 8.45%',
        product: 'Home loan',
        uplift: '+₹2.3 L lifetime value',
        acceptanceProb: 54,
        rationale: 'Early-stage shopper — a pre-approved letter wins over the HFC inquiry.',
      },
    ],
  },

  'C-01566': {
    id: 'C-01566',
    name: 'Isha Kapoor',
    segment: 'MASS_AFFLUENT',
    priority: 75,
    relationshipYears: 3,
    preferredChannel: 'SMS',
    revenueAtRiskLakh: 19.0,
    churnScore: 70,
    valueScore: 61,
    verdict: {
      label: 'RETAIN',
      headline: 'Card spend down 62% — reward friction. Retain with rewards upgrade.',
      reasons: [
        'Credit-card spend down 62% QoQ.',
        'Points balance ₹14,200 unredeemed > 6 months.',
        'No DPD, clean file.',
        'OFFER-CARD-REWARDS-09 pre-approved.',
      ],
    },
    redFlags: [
      { severity: 'HIGH', label: 'Card spend down 62%', detail: 'Primary card activity collapsed — likely substitute card in use' },
      { severity: 'MEDIUM', label: 'Unused rewards', detail: '₹14.2 K points stranded for 6+ months' },
    ],
    credit: {
      creditScore: 719,
      scoreBand: 'GOOD',
      maxDpd12m: 0,
      utilizationPct: 41,
      activeLoans: 1,
      recentInquiries: 0,
      defaultFlag: false,
    },
    banking: {
      currentBalanceLakh: 3.1,
      avgBalance90dLakh: 3.6,
      salaryAccount: true,
      salaryReceivedThisMonth: true,
      monthlyInflowLakh: 1.4,
      monthlyOutflowLakh: 1.3,
      balanceChange30dPct: -8.1,
      cardSpendChangePct: -62,
      forexSpend30dLakh: 0,
      competitorTransferDetected: false,
      productInactivityDays: 9,
    },
    offers: [
      {
        offerId: 'OFFER-CARD-REWARDS-09',
        offerName: 'Card refresh · 5× points on top-3 spend categories',
        product: 'Credit card',
        uplift: '+₹0.9 L interchange',
        acceptanceProb: 51,
        rationale: 'Clear reward-friction signal · low-cost reactivation play.',
      },
    ],
  },
}

export const cohortRetention: CohortRow[] = [
  { cohort: 'Mar', customers: 412, retention: [100, 97.6, 95.1, 93.3, 91.8, 90.4, 89.3, 88.6] },
  { cohort: 'Apr', customers: 456, retention: [100, 97.8, 95.6, 93.9, 92.4, 91.1, 89.9, null] },
  { cohort: 'May', customers: 487, retention: [100, 98.1, 95.9, 94.2, 92.7, 91.5, null, null] },
  { cohort: 'Jun', customers: 503, retention: [100, 98.3, 96.4, 94.8, 93.2, null, null, null] },
  { cohort: 'Jul', customers: 528, retention: [100, 98.5, 96.6, 95.1, null, null, null, null] },
  { cohort: 'Aug', customers: 541, retention: [100, 98.7, 96.9, null, null, null, null, null] },
  { cohort: 'Sep', customers: 562, retention: [100, 98.9, null, null, null, null, null, null] },
  { cohort: 'Oct', customers: 589, retention: [100, null, null, null, null, null, null, null] },
]
