import type { PortfolioSummary } from '../types/portfolio'
import type { PaginatedResponse } from '../types/api'
import type { PortfolioCustomerRow } from '../types/portfolio'
import type { CustomerSummary } from '../types/customer'
import type { Customer360 } from '../types/customer'
import type { RecommendationDetail } from '../types/recommendation'
import type { HealthResponse } from '../types/api'
import type { RulesOnlyAnalysisResponse } from '../types/analysis'
import type { AnalysisExecutionDetail } from '../types/analysis'
import type { AlertDetail, AlertSummary } from '../types/alert'
import type {
  ChatResponse,
  ConversationDetail,
  ConversationSummary,
} from '../types/chat'
import type { IncomingEventDetail, IncomingEventResponse } from '../types/event'
import type {
  LLMStatus,
  NotificationSystemStatus,
  QueueSystemStatus,
} from '../types/system'

export const mockPortfolioSummary: PortfolioSummary = {
  total_customers: 10,
  immediate_intervention_count: 2,
  review_count: 3,
  monitor_count: 3,
  no_action_count: 2,
  total_revenue_at_risk: 1250000,
  total_positive_expected_net_benefit: 450000,
  open_alerts: 4,
  unacknowledged_alerts: 2,
  high_value_high_risk_count: 1,
  generated_at: '2026-07-08T10:00:00Z',
}

export const mockPortfolioCustomers: PortfolioCustomerRow[] = [
  {
    customer_id: 'C001',
    full_name: 'Asha Verma',
    segment: 'PRIORITY',
    relationship_start_date: '2018-03-15',
    churn_score: 82,
    value_score: 76,
    priority_score: 91,
    decision: 'RETAIN',
    primary_trigger: 'COMPETITOR_TRANSFER',
    recommended_action: 'Contact within 24 hours',
    top_eligible_offer_id: 'OFF-001',
    top_eligible_offer_name: 'Relationship Saver Package',
    revenue_at_risk: 320000,
    expected_net_benefit: 85000,
    recommendation_status: 'NEW',
    has_data_warning: false,
    last_analyzed_at: '2026-07-08T09:00:00Z',
  },
  {
    customer_id: 'C002',
    full_name: 'Rahul Mehta',
    segment: 'MASS_AFFLUENT',
    relationship_start_date: '2020-06-01',
    churn_score: 45,
    value_score: 55,
    priority_score: 48,
    decision: 'MONITOR',
    primary_trigger: 'BALANCE_DECLINE',
    recommended_action: 'Monitor monthly',
    top_eligible_offer_id: null,
    top_eligible_offer_name: null,
    revenue_at_risk: 120000,
    expected_net_benefit: null,
    recommendation_status: null,
    has_data_warning: false,
    last_analyzed_at: null,
  },
]

export const mockCustomers: CustomerSummary[] = [
  {
    customer_id: 'C001',
    full_name: 'Asha Verma',
    segment: 'PRIORITY',
    assigned_rm_name: 'RM User',
    estimated_annual_value: 450000,
    preferred_channel: 'PHONE',
  },
  {
    customer_id: 'C004',
    full_name: 'Deepak Nair',
    segment: 'MASS_AFFLUENT',
    assigned_rm_name: 'RM User',
    estimated_annual_value: 280000,
    preferred_channel: 'PHONE',
  },
]

export const mockCustomer360: Customer360 = {
  customer: {
    customer_id: 'C001',
    full_name: 'Asha Verma',
    segment: 'PRIORITY',
    relationship_start_date: '2018-03-15',
    assigned_rm_id: 'RM-01',
    assigned_rm_name: 'RM User',
    assigned_rm_email: 'rm01@bank.test',
    communication_consent: true,
    preferred_channel: 'PHONE',
    estimated_annual_value: 450000,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-07-08T00:00:00Z',
  },
  accounts: [
    {
      account_id: 'ACC-10001',
      customer_id: 'C001',
      account_type: 'Savings',
      current_balance: 250000,
      average_balance_90d: 220000,
      salary_account: true,
      status: 'ACTIVE',
      fixed_deposit_maturity_date: null,
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-07-08T00:00:00Z',
    },
  ],
  credit_profile: {
    credit_profile_id: 'CP-001',
    customer_id: 'C001',
    credit_score: 720,
    max_dpd_12m: 5,
    credit_utilization_pct: 42,
    active_loans: 1,
    recent_credit_inquiries: 2,
    default_flag: false,
    last_updated: '2026-07-01T00:00:00Z',
  },
  bureau_triggers: [
    {
      bureau_trigger_id: 'BT-001',
      customer_id: 'C001',
      product_type: 'HOME_LOAN',
      trigger_type: 'EXTERNAL_INQUIRY',
      institution_category: 'COMPETITOR',
      amount_band: '25L-50L',
      severity: 'HIGH',
      trigger_date: '2026-06-20',
      source: 'CREDIT_BUREAU',
      processed: true,
      created_at: '2026-06-20T00:00:00Z',
    },
  ],
  transaction_features: {
    transaction_feature_id: 'TF-001',
    customer_id: 'C001',
    salary_received_current_month: true,
    balance_change_pct_30d: -12.5,
    monthly_inflow: 180000,
    monthly_outflow: 145000,
    external_transfer_amount_30d: 75000,
    card_spend_change_pct_30d: -8,
    forex_spend_30d: 12000,
    competitor_transfer_detected: true,
    product_inactivity_days: 14,
    last_updated: '2026-07-07T00:00:00Z',
  },
  recommendations: [
    {
      recommendation_id: 'REC-001',
      customer_id: 'C001',
      churn_score: 82,
      value_score: 76,
      priority_score: 91,
      decision: 'RETAIN',
      status: 'NEW',
      recommended_offer_id: 'OFF-001',
    },
  ],
  interactions: [],
  data_freshness: {
    core_banking: { last_updated: '2026-07-08T00:00:00Z', status: 'FRESH' },
    credit_history: { last_updated: '2026-07-01T00:00:00Z', status: 'STALE' },
    bureau_triggers: { last_updated: '2026-06-20T00:00:00Z', status: 'FRESH' },
    transaction_history: { last_updated: '2026-07-07T00:00:00Z', status: 'FRESH' },
  },
  data_warnings: ['Credit history is older than 7 days'],
}

export const mockCustomer360C004: Customer360 = {
  ...mockCustomer360,
  customer: {
    ...mockCustomer360.customer,
    customer_id: 'C004',
    full_name: 'Deepak Nair',
    segment: 'MASS_AFFLUENT',
  },
  credit_profile: {
    ...mockCustomer360.credit_profile!,
    customer_id: 'C004',
    credit_score: 610,
    max_dpd_12m: 60,
    default_flag: false,
  },
  bureau_triggers: [],
  data_warnings: ['Elevated DPD — lending offers restricted'],
}

export const mockCustomer360C010: Customer360 = {
  ...mockCustomer360,
  customer: {
    ...mockCustomer360.customer,
    customer_id: 'C010',
    full_name: 'Neha Kapoor',
    segment: 'STANDARD',
  },
  credit_profile: {
    ...mockCustomer360.credit_profile!,
    customer_id: 'C010',
    credit_score: 780,
    max_dpd_12m: 0,
  },
  bureau_triggers: [],
  recommendations: [],
  data_warnings: [],
}

export const mockRecommendation: RecommendationDetail = {
  recommendation_id: 'REC-001',
  customer_id: 'C001',
  triggering_event_id: null,
  analysis_execution_id: 'EXE-001',
  churn_score: 82,
  value_score: 76,
  priority_score: 91,
  decision: 'RETAIN',
  recommended_offer_id: 'OFF-001',
  alternate_offer_id: 'OFF-002',
  revenue_at_risk: 320000,
  expected_net_benefit: 85000,
  confidence: 0.82,
  summary: 'Customer shows competitor transfer signals and declining balances.',
  investigation_summary: 'Primary signal is external home loan inquiry.',
  evidence_json: {
    evidence_references: [
      {
        source_system: 'CREDIT_BUREAU',
        source_type: 'TRIGGER',
        reference_id: 'BT-001',
        field: 'trigger_type',
        observed_value: 'EXTERNAL_INQUIRY',
        timestamp: '2026-06-20T00:00:00Z',
      },
    ],
  },
  rm_brief_json: {
    talking_points: ['Acknowledge recent balance changes', 'Discuss relationship benefits'],
  },
  policy_warnings_json: ['Offer requires RM discussion only'],
  validation_warnings_json: [],
  created_by_mode: 'MOCK',
  calculation_version: '1.0',
  policy_version: '1.0',
  eligibility_disclaimer: 'Eligibility supports RM discussion only.',
  status: 'NEW',
  created_at: '2026-07-08T09:00:00Z',
  updated_at: '2026-07-08T09:00:00Z',
  interactions: [],
}

export const mockRecommendationC010: RecommendationDetail = {
  ...mockRecommendation,
  recommendation_id: 'REC-010',
  customer_id: 'C010',
  decision: 'NO_ACTION',
  priority_score: 18,
  recommended_offer_id: null,
  alternate_offer_id: null,
  expected_net_benefit: 0,
  revenue_at_risk: 0,
  summary: 'Stable relationship with no retention action required.',
  investigation_summary: 'No material risk signals detected.',
}

export const mockRulesOnly: RulesOnlyAnalysisResponse = {
  customer_id: 'C001',
  customer_name: 'Asha Verma',
  customer_segment: 'PRIORITY',
  customer_360_warnings: [],
  churn_result: {
    score: 82,
    band: 'CRITICAL',
    contributions: [
      {
        rule_code: 'COMPETITOR_TRANSFER',
        description: 'Competitor transfer detected',
        points: 25,
        observed_value: true,
        source_system: 'TRANSACTIONS',
        source_reference: null,
        triggered: true,
      },
    ],
    calculation_version: '1.0',
    calculated_at: '2026-07-08T10:00:00Z',
  },
  value_result: {
    score: 76,
    band: 'HIGH',
    contributions: [],
    calculation_version: '1.0',
    calculated_at: '2026-07-08T10:00:00Z',
  },
  priority_result: {
    churn_score: 82,
    value_score: 76,
    churn_weight: 0.6,
    value_weight: 0.4,
    priority_score: 91,
    decision: 'RETAIN',
    explanation: 'High churn and high value',
    calculation_version: '1.0',
    calculated_at: '2026-07-08T10:00:00Z',
  },
  eligibility_result: {
    customer_id: 'C001',
    eligible_offers: [],
    rejected_offers: [],
    policy_warnings: [],
    policy_version: '1.0',
    evaluated_at: '2026-07-08T10:00:00Z',
  },
  financial_options: [],
  top_risk_signals: ['Competitor transfer'],
  primary_trigger: 'COMPETITOR_TRANSFER',
  suggested_action: 'Contact customer within 24 hours',
  generated_at: '2026-07-08T10:00:00Z',
  analysis_version: '1.0',
}

export const mockHealth: HealthResponse = {
  status: 'healthy',
  service: 'RetainAI API',
  environment: 'development',
  version: '0.1.0',
}

export function paginate<T>(items: T[], page = 1, pageSize = 20): PaginatedResponse<T> {
  const total = items.length
  const pages = Math.ceil(total / pageSize) || 0
  const start = (page - 1) * pageSize
  return {
    items: items.slice(start, start + pageSize),
    total,
    page,
    page_size: pageSize,
    pages,
  }
}

export const mockExecutionQueued: AnalysisExecutionDetail = {
  execution_id: 'EXE-NEW',
  customer_id: 'C001',
  event_id: null,
  mode: 'AGENTIC',
  status: 'QUEUED',
  current_step: null,
  recommendation_id: null,
  priority_score: null,
  started_at: null,
  completed_at: null,
  error_code: null,
  safe_error_message: null,
  validation_warnings: [],
  status_url: '/api/v1/analysis/executions/EXE-NEW',
  recommendation_url: null,
  created_at: '2026-07-08T10:00:00Z',
  updated_at: '2026-07-08T10:00:00Z',
}

export const mockExecutionCompleted: AnalysisExecutionDetail = {
  ...mockExecutionQueued,
  status: 'COMPLETED',
  recommendation_id: 'REC-001',
  completed_at: '2026-07-08T10:01:00Z',
}

export const mockExecutionFailed: AnalysisExecutionDetail = {
  ...mockExecutionQueued,
  status: 'FAILED',
  safe_error_message: 'Analysis could not be completed safely.',
}

export const mockAlerts: AlertSummary[] = [
  {
    alert_id: 'ALT-001',
    customer_id: 'C001',
    event_id: 'EVT-001',
    recommendation_id: 'REC-001',
    alert_type: 'AGENT_RECOMMENDATION',
    severity: 'HIGH',
    title: 'High churn risk — competitor transfer',
    priority_score: 91,
    acknowledged: false,
    notification_status: 'SENT',
    created_at: '2026-07-08T10:00:00Z',
  },
  {
    alert_id: 'ALT-002',
    customer_id: 'C004',
    event_id: 'EVT-002',
    recommendation_id: 'REC-002',
    alert_type: 'AGENT_RECOMMENDATION',
    severity: 'CRITICAL',
    title: 'DPD escalation — repayment support needed',
    priority_score: 88,
    acknowledged: true,
    notification_status: 'SENT',
    created_at: '2026-07-08T09:30:00Z',
  },
]

export const mockAlertDetail: AlertDetail = {
  ...mockAlerts[0],
  message: 'Customer shows elevated churn indicators requiring RM review.',
  assigned_rm_id: 'RM-01',
  assigned_rm_email: 'rm01@bank.test',
  recommended_action: 'Contact within 24 hours',
  recommended_offer_id: 'OFF-001',
  acknowledged_at: null,
  acknowledged_by: null,
}

export const mockRetentionAlertWs = {
  type: 'RETENTION_ALERT' as const,
  alert_id: 'ALT-NEW',
  event_id: 'EVT-NEW',
  recommendation_id: 'REC-001',
  customer_id: 'C001',
  alert_type: 'AGENT_RECOMMENDATION' as const,
  severity: 'HIGH' as const,
  title: 'Live retention alert',
  priority_score: 85,
  recommended_action: 'Schedule retention call',
  recommended_offer: 'Relationship Saver Package',
  expected_net_benefit: 85000,
  created_at: '2026-07-08T11:00:00Z',
}

export const mockConversationSummary: ConversationSummary = {
  conversation_id: 'CONV-001',
  title: 'Portfolio priorities',
  active_customer_id: null,
  last_message_preview: 'Who should I call today?',
  message_count: 2,
  created_at: '2026-07-08T08:00:00Z',
  updated_at: '2026-07-08T08:05:00Z',
  status: 'ACTIVE',
}

export const mockConversationDetail: ConversationDetail = {
  conversation_id: 'CONV-001',
  rm_id: 'RM-01',
  title: 'Portfolio priorities',
  active_customer_id: null,
  status: 'ACTIVE',
  created_at: '2026-07-08T08:00:00Z',
  updated_at: '2026-07-08T08:05:00Z',
  expires_at: null,
  messages: [
    {
      message_id: 'MSG-001',
      role: 'USER',
      content: 'Who should I call today?',
      customer_ids: [],
      used_tools: [],
      evidence: [],
      warnings: [],
      created_at: '2026-07-08T08:00:00Z',
    },
    {
      message_id: 'MSG-002',
      role: 'ASSISTANT',
      content: 'Start with C001 — high priority score and unacknowledged alerts.',
      customer_ids: ['C001'],
      used_tools: ['portfolio_summary'],
      evidence: [
        {
          source_system: 'RetainAI',
          source_type: 'portfolio',
          reference_id: null,
          customer_id: 'C001',
          field: 'priority_score',
          value_summary: '91',
          timestamp: '2026-07-08T08:05:00Z',
        },
      ],
      warnings: ['Synthetic data — not for production decisions.'],
      created_at: '2026-07-08T08:05:00Z',
    },
  ],
}

export const mockChatResponse: ChatResponse = {
  conversation_id: 'CONV-001',
  message_id: 'MSG-003',
  answer: 'Start with C001 — high priority score and unacknowledged alerts.',
  intent: 'PRIORITY_CUSTOMER_LIST',
  customer_ids: ['C001'],
  used_tools: ['portfolio_summary'],
  evidence: mockConversationDetail.messages[1].evidence,
  warnings: ['Synthetic data — not for production decisions.'],
  suggested_questions: ['Why is this customer high risk?', 'What offer should I discuss?'],
  generated_at: '2026-07-08T08:05:00Z',
  mode: 'MOCK',
}

export const mockChatFollowUpResponse: ChatResponse = {
  ...mockChatResponse,
  message_id: 'MSG-004',
  answer: 'For C001, OFFER-HL-FEE is eligible for discussion based on current signals.',
  intent: 'CUSTOMER_OFFER_EXPLANATION',
  suggested_questions: [],
}

export const mockEventResponse: IncomingEventResponse = {
  event_id: 'EVT-SIM-001',
  customer_id: 'C001',
  event_type: 'EXTERNAL_HOME_LOAN_INQUIRY',
  source_system: 'BUREAU_MONITOR',
  status: 'QUEUED',
  execution_id: null,
  created_at: '2026-07-08T10:00:00Z',
  queued_at: '2026-07-08T10:00:01Z',
  processing_started_at: null,
  processed_at: null,
  error_message: null,
  duplicate: false,
  analysis_summary: null,
}

export const mockEventDetailQueued: IncomingEventDetail = {
  event_id: 'EVT-SIM-001',
  customer_id: 'C001',
  event_type: 'EXTERNAL_HOME_LOAN_INQUIRY',
  source_system: 'BUREAU_MONITOR',
  payload_json: { severity: 'HIGH' },
  idempotency_key: 'sim-1',
  execution_id: null,
  analysis_result_json: null,
  status: 'QUEUED',
  error_message: null,
  retry_count: 0,
  notifications_enabled: true,
  created_at: '2026-07-08T10:00:00Z',
  queued_at: '2026-07-08T10:00:01Z',
  processing_started_at: null,
  processed_at: null,
}

export const mockEventDetailCompleted: IncomingEventDetail = {
  ...mockEventDetailQueued,
  status: 'COMPLETED',
  execution_id: 'EXE-NEW',
  processing_started_at: '2026-07-08T10:00:02Z',
  processed_at: '2026-07-08T10:00:05Z',
  analysis_result_json: { recommendation_id: 'REC-001', priority_score: 91 },
}

export const mockEventDetailFailed: IncomingEventDetail = {
  ...mockEventDetailQueued,
  status: 'FAILED',
  error_message: 'Event processing failed safely.',
  processing_started_at: '2026-07-08T10:00:02Z',
  processed_at: '2026-07-08T10:00:05Z',
}

export const mockLLMStatus: LLMStatus = {
  mode: 'MOCK',
  configured_model: 'mock-rm-copilot',
  endpoint_host: 'localhost',
  available: true,
  last_checked_at: '2026-07-08T10:00:00Z',
  error_message: null,
  crewai_version: '0.80.0',
}

export const mockLLMStatusUnavailable: LLMStatus = {
  ...mockLLMStatus,
  mode: 'QWEN',
  configured_model: 'qwen2.5-7b',
  available: false,
  error_message: 'Qwen endpoint unreachable',
}

export const mockQueueStatus: QueueSystemStatus = {
  worker_count: 2,
  queue_size: 0,
  processing_count: 0,
  completed_count_since_startup: 12,
  failed_count_since_startup: 1,
  started_at: '2026-07-08T08:00:00Z',
}

export const mockNotificationStatus: NotificationSystemStatus = {
  email_notifications_enabled: true,
  smtp_host: 'localhost',
  smtp_port: 1025,
  smtp_configured: true,
  websocket_connections: 1,
  alert_priority_threshold: 70,
}
