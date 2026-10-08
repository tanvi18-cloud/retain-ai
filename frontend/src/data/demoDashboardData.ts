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
}

export const headlineKpis: HeadlineKpi[] = [
  { label: 'Portfolio AUM', value: '₹1,284 Cr', caption: 'Assets under RM management' },
  { label: 'Customers covered', value: '12,480', caption: 'Across 4 segments · 6 regions' },
  { label: 'Net retention rate', value: '94.2%', caption: 'Trailing 12 months · YoY +3.1 pts' },
  { label: 'Revenue saved YTD', value: '₹46.8 Cr', caption: 'Attributed to agent-assisted saves' },
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
