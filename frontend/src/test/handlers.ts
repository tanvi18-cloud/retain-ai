import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'

import {
  mockCustomer360,
  mockCustomers,
  mockExecutionCompleted,
  mockExecutionFailed,
  mockExecutionQueued,
  mockHealth,
  mockPortfolioCustomers,
  mockPortfolioSummary,
  mockRecommendation,
  mockRulesOnly,
  paginate,
} from './fixtures'

const API = 'http://127.0.0.1:8001/api/v1'

let executionPolls = 0
let recommendationStatus = mockRecommendation.status

export const server = setupServer(
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
)

export function resetMockState() {
  executionPolls = 0
  recommendationStatus = 'NEW'
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
