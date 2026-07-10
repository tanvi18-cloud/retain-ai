import { useCallback, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { toast } from 'sonner'
import { ArrowLeft, Loader2 } from 'lucide-react'

import { runFullAnalysis, runRulesOnlyAnalysis } from '../api/analysis'
import { fetchCustomer360 } from '../api/customers'
import { fetchRecommendation } from '../api/recommendations'
import { ApiError } from '../api/client'
import { CreditProfilePanel } from '../components/customers/CreditProfilePanel'
import { CustomerSummaryCard } from '../components/customers/CustomerSummaryCard'
import { DataFreshnessPanel } from '../components/customers/DataFreshnessPanel'
import { EvidenceTimeline } from '../components/customers/EvidenceTimeline'
import { InteractionHistory } from '../components/customers/InteractionHistory'
import { ProductHoldingsPanel } from '../components/customers/ProductHoldingsPanel'
import { RecommendationPanel } from '../components/customers/RecommendationPanel'
import { RiskScoreGrid } from '../components/customers/RiskScoreCard'
import { RMActionPanel } from '../components/customers/RMActionPanel'
import { TransactionBehaviorPanel } from '../components/customers/TransactionBehaviorPanel'
import { Button } from '../components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { ErrorState } from '../components/ui/ErrorState'
import { Skeleton } from '../components/ui/Skeleton'
import { useAnalysisExecutionPolling } from '../hooks/useAnalysisExecutionPolling'
import { useDocumentTitle } from '../hooks/useDocumentTitle'
import type { RulesOnlyAnalysisResponse } from '../types/analysis'
import type { EvidenceReference } from '../types/recommendation'
import { decisionLabel } from '../utils/risk'
import { queryKeys } from '../utils/queryKeys'

function parseEvidenceReferences(value: unknown): EvidenceReference[] {
  if (!Array.isArray(value)) return []
  return value.filter(
    (item): item is EvidenceReference =>
      typeof item === 'object' &&
      item !== null &&
      'source_system' in item &&
      'field' in item,
  ) as EvidenceReference[]
}

export function CustomerDetailsPage() {
  const { customerId = '' } = useParams()
  const [rulesOnlyResult, setRulesOnlyResult] = useState<RulesOnlyAnalysisResponse | null>(null)
  const [executionId, setExecutionId] = useState<string | null>(null)
  const [executionStatus, setExecutionStatus] = useState<string | null>(null)

  const clearExecution = useCallback(() => {
    setExecutionId(null)
    setExecutionStatus(null)
  }, [])

  useAnalysisExecutionPolling({
    executionId,
    customerId,
    onStatusChange: setExecutionStatus,
    onComplete: () => {
      toast.success('Full analysis completed')
      clearExecution()
    },
    onFailed: (message) => {
      toast.error(message)
      clearExecution()
    },
    onPollError: (message) => {
      toast.error(message)
      clearExecution()
    },
    onTimeout: () => {
      toast.error('Analysis polling timed out. Please retry.')
      clearExecution()
    },
  })

  const customer360Query = useQuery({
    queryKey: queryKeys.customers.customer360(customerId),
    queryFn: () => fetchCustomer360(customerId),
    enabled: Boolean(customerId),
  })

  const latestRecommendationId =
    customer360Query.data?.recommendations[0]?.recommendation_id ?? null

  const recommendationQuery = useQuery({
    queryKey: queryKeys.recommendations.detail(latestRecommendationId ?? ''),
    queryFn: () => fetchRecommendation(latestRecommendationId!),
    enabled: Boolean(latestRecommendationId),
  })

  useDocumentTitle(
    customer360Query.data
      ? `${customer360Query.data.customer.full_name} · Customer 360`
      : 'Customer 360',
  )

  const rulesOnlyMutation = useMutation({
    mutationFn: () => runRulesOnlyAnalysis(customerId),
    onSuccess: (result) => {
      setRulesOnlyResult(result)
      toast.success('Rules-only analysis complete')
    },
    onError: (error) => {
      toast.error(error instanceof ApiError ? error.message : 'Analysis failed')
    },
  })

  const fullAnalysisMutation = useMutation({
    mutationFn: () => runFullAnalysis(customerId, { notifications_enabled: true }),
    onSuccess: (result) => {
      setExecutionId(result.execution_id)
      setExecutionStatus(result.status)
      toast.message('Analysis queued', { description: 'Polling for completion…' })
    },
    onError: (error) => {
      toast.error(error instanceof ApiError ? error.message : 'Unable to queue analysis')
    },
  })

  if (customer360Query.isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-60 w-full" />
      </div>
    )
  }

  if (customer360Query.isError) {
    const notFound = customer360Query.error instanceof ApiError && customer360Query.error.isNotFound
    return (
      <ErrorState
        title={notFound ? 'Customer not found' : 'Unable to load Customer 360'}
        message={
          customer360Query.error instanceof ApiError
            ? customer360Query.error.message
            : 'Please try again.'
        }
        onRetry={() => customer360Query.refetch()}
      />
    )
  }

  const data = customer360Query.data

  if (!data) {
    return (
      <ErrorState
        title="Customer not available"
        message="Customer 360 data could not be loaded."
        onRetry={() => customer360Query.refetch()}
      />
    )
  }

  const recommendation = recommendationQuery.data ?? null

  const summaryRec = data.recommendations[0]

  const churnScore = rulesOnlyResult?.churn_result.score ?? summaryRec?.churn_score ?? 0
  const valueScore = rulesOnlyResult?.value_result.score ?? summaryRec?.value_score ?? 0
  const priorityScore = rulesOnlyResult?.priority_result.priority_score ?? summaryRec?.priority_score ?? 0
  const decision =
    rulesOnlyResult?.priority_result.decision ?? summaryRec?.decision ?? 'NO_ACTION'

  const evidenceRefs = recommendation
    ? parseEvidenceReferences(recommendation.evidence_json.evidence_references)
    : []

  const topOffer =
    data.recommendations[0]?.recommended_offer_id ??
    rulesOnlyResult?.financial_options[0]?.offer_name ??
    null

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-3">
        <Link
          to="/customers"
          className="inline-flex h-8 items-center gap-2 rounded-lg px-3 text-sm font-medium text-slate-700 hover:bg-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          Back to customers
        </Link>
        <Button
          variant="outline"
          loading={rulesOnlyMutation.isPending}
          onClick={() => rulesOnlyMutation.mutate()}
        >
          Run rules-only analysis
        </Button>
        <Button
          variant="primary"
          loading={fullAnalysisMutation.isPending || Boolean(executionId)}
          onClick={() => fullAnalysisMutation.mutate()}
        >
          {executionId ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
              {executionStatus ?? 'Running'}…
            </>
          ) : (
            'Run full analysis'
          )}
        </Button>
      </div>

      <CustomerSummaryCard customer={data.customer} />

      <RiskScoreGrid
        churnScore={churnScore}
        churnBand={rulesOnlyResult?.churn_result.band}
        valueScore={valueScore}
        valueBand={rulesOnlyResult?.value_result.band}
        priorityScore={priorityScore}
        decision={decisionLabel(decision)}
        revenueAtRisk={recommendation?.revenue_at_risk ?? 0}
        expectedNetBenefit={recommendation?.expected_net_benefit ?? null}
        topOffer={topOffer}
      />

      {rulesOnlyResult ? (
        <Card>
          <CardHeader>
            <CardTitle>Rules-only analysis result</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-slate-600">
            <p>{rulesOnlyResult.suggested_action}</p>
            <p>Primary trigger: {rulesOnlyResult.primary_trigger ?? '—'}</p>
            <p>Generated: {rulesOnlyResult.generated_at}</p>
          </CardContent>
        </Card>
      ) : null}

      <div className="grid gap-6 xl:grid-cols-2">
        <EvidenceTimeline
          primaryTrigger={rulesOnlyResult?.primary_trigger ?? null}
          contributions={rulesOnlyResult?.churn_result.contributions}
          evidenceReferences={evidenceRefs}
          bureauTriggers={data.bureau_triggers}
        />
        <DataFreshnessPanel freshness={data.data_freshness} warnings={data.data_warnings} />
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <ProductHoldingsPanel accounts={data.accounts} />
        <TransactionBehaviorPanel features={data.transaction_features} />
      </div>

      <CreditProfilePanel profile={data.credit_profile} />

      <RecommendationPanel
        recommendation={recommendation}
        loading={recommendationQuery.isLoading || recommendationQuery.isFetching}
        onRunFullAnalysis={() => fullAnalysisMutation.mutate()}
      />

      {recommendation ? (
        <RMActionPanel recommendation={recommendation} customerId={customerId} />
      ) : null}

      <InteractionHistory interactions={data.interactions} />
    </div>
  )
}
