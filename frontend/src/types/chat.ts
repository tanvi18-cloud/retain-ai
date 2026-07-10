export type LLMMode = 'MOCK' | 'QWEN'

export type ChatIntent =
  | 'CUSTOMER_RISK_EXPLANATION'
  | 'CUSTOMER_OFFER_EXPLANATION'
  | 'CUSTOMER_ELIGIBILITY_EXPLANATION'
  | 'CUSTOMER_COMPARISON'
  | 'PRIORITY_CUSTOMER_LIST'
  | 'PORTFOLIO_SUMMARY'
  | 'TRIGGER_SEARCH'
  | 'REVENUE_AT_RISK'
  | 'RM_TALKING_POINTS'
  | 'RECOMMENDATION_STATUS'
  | 'DATA_FRESHNESS'
  | 'DPD_EXPLANATION'
  | 'FOLLOW_UP_QUESTION'
  | 'GENERAL_HELP'
  | 'UNSUPPORTED'

export type ChatConversationStatus = 'ACTIVE' | 'CLOSED'

export type ChatMessageRole = 'USER' | 'ASSISTANT' | 'SYSTEM'

export interface ChatEvidence {
  source_system: string
  source_type: string
  reference_id: string | null
  customer_id: string | null
  field: string
  value_summary: string
  timestamp: string | null
}

export interface ChatRequest {
  message: string
  conversation_id?: string | null
  rm_id: string
  customer_id?: string | null
  include_history?: boolean
}

export interface ChatResponse {
  conversation_id: string
  message_id: string
  answer: string
  intent: ChatIntent
  customer_ids: string[]
  used_tools: string[]
  evidence: ChatEvidence[]
  warnings: string[]
  suggested_questions: string[]
  generated_at: string
  mode: LLMMode
}

export interface ConversationSummary {
  conversation_id: string
  title: string | null
  active_customer_id: string | null
  last_message_preview: string | null
  message_count: number
  created_at: string
  updated_at: string
  status: ChatConversationStatus
}

export interface ChatMessageResponse {
  message_id: string
  role: ChatMessageRole
  content: string
  customer_ids: string[]
  used_tools: string[]
  evidence: ChatEvidence[]
  warnings: string[]
  created_at: string
}

export interface ConversationDetail {
  conversation_id: string
  rm_id: string
  title: string | null
  active_customer_id: string | null
  status: ChatConversationStatus
  created_at: string
  updated_at: string
  expires_at: string | null
  messages: ChatMessageResponse[]
}

export interface ConversationCloseRequest {
  rm_id: string
}
