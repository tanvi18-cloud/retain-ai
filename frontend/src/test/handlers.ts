import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'

import { alertsWebSocketHandler } from './mswWebSocket'
import {
  mockAlertDetail,
  mockAlerts,
  mockChatResponse,
  mockConversationDetail,
  mockConversationSummary,
  mockCustomer360,
  mockCustomers,
  mockEventDetailCompleted,
  mockEventDetailFailed,
  mockEventDetailQueued,
  mockEventResponse,
  mockExecutionCompleted,
  mockExecutionFailed,
  mockExecutionQueued,
  mockHealth,
  mockLLMStatus,
  mockNotificationStatus,
  mockPortfolioCustomers,
  mockPortfolioSummary,
  mockQueueStatus,
  mockRecommendation,
  mockRulesOnly,
  paginate,
} from './fixtures'

const API = 'http://127.0.0.1:8001/api/v1'

let executionPolls = 0
let recommendationStatus = mockRecommendation.status
let eventPolls = 0
let eventStatus: 'QUEUED' | 'PROCESSING' | 'COMPLETED' | 'FAILED' = 'QUEUED'
let simulateFailedNext = false
let chatConversationClosed = false

export const server = setupServer(
  alertsWebSocketHandler,
  http.get(`${API}/health`, () => HttpResponse.json(mockHealth)),

  http.get(`${API}/portfolio/summary`, () => HttpResponse.json(mockPortfolioSummary)),

  http.get(`${API}/portfolio/customers`, ({ request }) => {
    const url = new URL(request.url)
    let items = [...mockPortfolioCustomers]

    const search = url.searchParams.get('search')
    if (search) {
      items = items.filter(
        (item) =>
          item.customer_id.toLowerCase().includes(search.toLowerCase()) ||
          item.full_name.toLowerCase().includes(search.toLowerCase()),
      )
    }

    const decision = url.searchParams.get('decision')
    if (decision) items = items.filter((item) => item.decision === decision)

    const page = Number(url.searchParams.get('page') ?? '1')
    const pageSize = Number(url.searchParams.get('page_size') ?? '20')
    return HttpResponse.json(paginate(items, page, pageSize))
  }),

  http.get(`${API}/customers`, ({ request }) => {
    const url = new URL(request.url)
    const page = Number(url.searchParams.get('page') ?? '1')
    const pageSize = Number(url.searchParams.get('page_size') ?? '20')
    return HttpResponse.json(paginate(mockCustomers, page, pageSize))
  }),

  http.get(`${API}/customers/:customerId/360`, ({ params }) => {
    if (params.customerId === 'MISSING') {
      return HttpResponse.json(
        { error: { code: 'NOT_FOUND', message: 'Customer not found', details: {} } },
        { status: 404 },
      )
    }
    return HttpResponse.json(mockCustomer360)
  }),

  http.get(`${API}/recommendations/:id`, () =>
    HttpResponse.json({ ...mockRecommendation, status: recommendationStatus }),
  ),

  http.get(`${API}/recommendations`, () =>
    HttpResponse.json(paginate([mockRecommendation], 1, 20)),
  ),

  http.post(`${API}/analysis/:customerId/rules-only`, () => HttpResponse.json(mockRulesOnly)),

  http.post(`${API}/analysis/:customerId`, () =>
    HttpResponse.json({
      execution_id: 'EXE-NEW',
      customer_id: 'C001',
      status: 'QUEUED',
      queued_at: '2026-07-08T10:00:00Z',
      status_url: '/api/v1/analysis/executions/EXE-NEW',
    }),
  ),

  http.get(`${API}/analysis/executions/:id`, () => {
    executionPolls += 1
    if (executionPolls < 2) return HttpResponse.json(mockExecutionQueued)
    return HttpResponse.json(mockExecutionCompleted)
  }),

  http.post(`${API}/recommendations/:id/review`, () => {
    recommendationStatus = 'REVIEWED'
    return HttpResponse.json({
      recommendation_id: 'REC-001',
      status: 'REVIEWED',
      interaction_id: 'INT-001',
      message: 'Recommendation marked as reviewed',
    })
  }),

  http.post(`${API}/recommendations/:id/approve`, () => {
    recommendationStatus = 'APPROVED'
    return HttpResponse.json({
      recommendation_id: 'REC-001',
      status: 'APPROVED',
      interaction_id: 'INT-002',
      message: 'Recommendation approved for discussion',
    })
  }),

  http.post(`${API}/recommendations/:id/reject`, async ({ request }) => {
    const body = (await request.json()) as { rejection_reason?: string }
    if (!body.rejection_reason) {
      return HttpResponse.json(
        { error: { code: 'VALIDATION_ERROR', message: 'Rejection reason required', details: {} } },
        { status: 422 },
      )
    }
    recommendationStatus = 'REJECTED'
    return HttpResponse.json({
      recommendation_id: 'REC-001',
      status: 'REJECTED',
      interaction_id: 'INT-003',
      message: 'Recommendation rejected',
    })
  }),

  http.post(`${API}/recommendations/:id/contacted`, () => {
    recommendationStatus = 'CONTACTED'
    return HttpResponse.json({
      recommendation_id: 'REC-001',
      status: 'CONTACTED',
      interaction_id: 'INT-004',
      message: 'Contact recorded',
    })
  }),

  http.post(`${API}/recommendations/:id/close`, async ({ request }) => {
    const body = (await request.json()) as { closing_note?: string }
    if (!body.closing_note) {
      return HttpResponse.json(
        { error: { code: 'VALIDATION_ERROR', message: 'Closing note required', details: {} } },
        { status: 422 },
      )
    }
    recommendationStatus = 'CLOSED'
    return HttpResponse.json({
      recommendation_id: 'REC-001',
      status: 'CLOSED',
      interaction_id: 'INT-005',
      message: 'Recommendation closed',
    })
  }),

  http.get(`${API}/alerts`, ({ request }) => {
    const url = new URL(request.url)
    let items = [...mockAlerts]
    const acknowledged = url.searchParams.get('acknowledged')
    if (acknowledged === 'true') items = items.filter((a) => a.acknowledged)
    if (acknowledged === 'false') items = items.filter((a) => !a.acknowledged)
    const customerId = url.searchParams.get('customer_id')
    if (customerId) items = items.filter((a) => a.customer_id === customerId)
    const page = Number(url.searchParams.get('page') ?? '1')
    const pageSize = Number(url.searchParams.get('page_size') ?? '20')
    return HttpResponse.json(paginate(items, page, pageSize))
  }),

  http.get(`${API}/alerts/:alertId`, ({ params }) =>
    HttpResponse.json({ ...mockAlertDetail, alert_id: String(params.alertId) }),
  ),

  http.patch(`${API}/alerts/:alertId/acknowledge`, async ({ params, request }) => {
    const body = (await request.json()) as { rm_id?: string }
    if (!body.rm_id) {
      return HttpResponse.json(
        { error: { code: 'VALIDATION_ERROR', message: 'rm_id required', details: {} } },
        { status: 422 },
      )
    }
    return HttpResponse.json({
      ...mockAlertDetail,
      alert_id: String(params.alertId),
      acknowledged: true,
      acknowledged_at: '2026-07-08T12:00:00Z',
      acknowledged_by: body.rm_id,
    })
  }),

  http.get(`${API}/chat/conversations`, ({ request }) => {
    const url = new URL(request.url)
    const page = Number(url.searchParams.get('page') ?? '1')
    const pageSize = Number(url.searchParams.get('page_size') ?? '20')
    return HttpResponse.json(paginate([mockConversationSummary], page, pageSize))
  }),

  http.get(`${API}/chat/conversations/:conversationId`, ({ params, request }) => {
    const url = new URL(request.url)
    if (!url.searchParams.get('rm_id')) {
      return HttpResponse.json(
        { error: { code: 'VALIDATION_ERROR', message: 'rm_id required', details: {} } },
        { status: 422 },
      )
    }
    if (chatConversationClosed) {
      return HttpResponse.json({
        ...mockConversationDetail,
        conversation_id: String(params.conversationId),
        status: 'CLOSED',
      })
    }
    return HttpResponse.json({
      ...mockConversationDetail,
      conversation_id: String(params.conversationId),
    })
  }),

  http.post(`${API}/chat`, async ({ request }) => {
    if (chatConversationClosed) {
      return HttpResponse.json(
        { error: { code: 'CONVERSATION_CLOSED', message: 'Conversation is closed', details: {} } },
        { status: 409 },
      )
    }
    const body = (await request.json()) as { message?: string }
    if (!body.message?.trim()) {
      return HttpResponse.json(
        { error: { code: 'VALIDATION_ERROR', message: 'Message required', details: {} } },
        { status: 422 },
      )
    }
    return HttpResponse.json(mockChatResponse)
  }),

  http.post(`${API}/chat/conversations/:conversationId/close`, async ({ request }) => {
    const body = (await request.json()) as { rm_id?: string }
    if (!body.rm_id) {
      return HttpResponse.json(
        { error: { code: 'VALIDATION_ERROR', message: 'rm_id required', details: {} } },
        { status: 422 },
      )
    }
    chatConversationClosed = true
    return HttpResponse.json({ ...mockConversationDetail, status: 'CLOSED' })
  }),

  http.post(`${API}/events`, async () => {
    if (simulateFailedNext) {
      eventPolls = 0
      eventStatus = 'FAILED'
      simulateFailedNext = false
    } else {
      eventPolls = 0
      eventStatus = 'QUEUED'
    }
    return HttpResponse.json(mockEventResponse)
  }),

  http.get(`${API}/events/:eventId`, () => {
    eventPolls += 1
    if (eventStatus === 'FAILED') return HttpResponse.json(mockEventDetailFailed)
    if (eventStatus === 'COMPLETED' || eventPolls >= 2) {
      eventStatus = 'COMPLETED'
      return HttpResponse.json(mockEventDetailCompleted)
    }
    if (eventPolls >= 1) {
      return HttpResponse.json({ ...mockEventDetailQueued, status: 'PROCESSING', execution_id: 'EXE-NEW' })
    }
    return HttpResponse.json(mockEventDetailQueued)
  }),

  http.post(`${API}/events/:eventId/retry`, () => {
    eventPolls = 0
    eventStatus = 'QUEUED'
    return HttpResponse.json({ ...mockEventResponse, event_id: 'EVT-SIM-RETRY' })
  }),

  http.get(`${API}/system/llm-status`, () => HttpResponse.json(mockLLMStatus)),

  http.get(`${API}/system/queue-status`, () => HttpResponse.json(mockQueueStatus)),

  http.get(`${API}/system/notification-status`, () => HttpResponse.json(mockNotificationStatus)),
)

export function resetMockState() {
  executionPolls = 0
  recommendationStatus = 'NEW'
  eventPolls = 0
  eventStatus = 'QUEUED'
  simulateFailedNext = false
  chatConversationClosed = false
}

export function getExecutionPollCount(): number {
  return executionPolls
}

export function setFailedExecution() {
  server.use(
    http.get(`${API}/analysis/executions/:id`, () => HttpResponse.json(mockExecutionFailed)),
  )
}

export function setPortfolioError() {
  server.use(
    http.get(`${API}/portfolio/summary`, () =>
      HttpResponse.json(
        { error: { code: 'SERVER_ERROR', message: 'Backend unavailable', details: {} } },
        { status: 500 },
      ),
    ),
  )
}

export function setInvalidTransition() {
  server.use(
    http.post(`${API}/recommendations/:id/approve`, () =>
      HttpResponse.json(
        { error: { code: 'INVALID_TRANSITION', message: 'Invalid status transition', details: {} } },
        { status: 409 },
      ),
    ),
  )
}

export function setFailedEvent() {
  simulateFailedNext = true
}

export function setQwenUnavailable() {
  server.use(
    http.post(`${API}/chat`, () =>
      HttpResponse.json(
        { error: { code: 'LLM_UNAVAILABLE', message: 'Qwen unavailable', details: {} } },
        { status: 503 },
      ),
    ),
  )
}

export function setAlertsError() {
  server.use(
    http.get(`${API}/alerts`, () =>
      HttpResponse.json(
        { error: { code: 'SERVER_ERROR', message: 'Alerts unavailable', details: {} } },
        { status: 500 },
      ),
    ),
  )
}

export function setClosedConversation() {
  chatConversationClosed = true
}
