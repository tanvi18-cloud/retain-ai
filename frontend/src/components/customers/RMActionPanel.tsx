import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { ApiError } from '../../api/client'
import { RM_USER } from '../../api/env'
import {
  approveRecommendation,
  closeRecommendation,
  contactedRecommendation,
  rejectRecommendation,
  reviewRecommendation,
} from '../../api/recommendations'
import type { RecommendationDetail } from '../../types/recommendation'
import type { RecommendationStatus } from '../../types/api'
import { queryKeys } from '../../utils/queryKeys'
import { Button } from '../ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card'
import { ConfirmDialog } from '../ui/ConfirmDialog'
import { Modal } from '../ui/Modal'

const ALLOWED_TRANSITIONS: Record<RecommendationStatus, RecommendationStatus[]> = {
  NEW: ['REVIEWED', 'APPROVED', 'REJECTED'],
  REVIEWED: ['APPROVED', 'REJECTED', 'CONTACTED'],
  APPROVED: ['CONTACTED', 'CLOSED'],
  REJECTED: ['CLOSED'],
  CONTACTED: ['CLOSED'],
  CLOSED: [],
}

const ACTION_TARGETS: Record<string, RecommendationStatus> = {
  review: 'REVIEWED',
  approve: 'APPROVED',
  reject: 'REJECTED',
  contacted: 'CONTACTED',
  close: 'CLOSED',
}

function canTransition(status: RecommendationStatus, action: keyof typeof ACTION_TARGETS): boolean {
  const target = ACTION_TARGETS[action]
  return ALLOWED_TRANSITIONS[status]?.includes(target) ?? false
}

export interface RMActionPanelProps {
  recommendation: RecommendationDetail
  customerId: string
}

export function RMActionPanel({ recommendation, customerId }: RMActionPanelProps) {
  const queryClient = useQueryClient()
  const [approveOpen, setApproveOpen] = useState(false)
  const [rejectOpen, setRejectOpen] = useState(false)
  const [contactOpen, setContactOpen] = useState(false)
  const [closeOpen, setCloseOpen] = useState(false)
  const [reviewNote, setReviewNote] = useState('')
  const [rejectReason, setRejectReason] = useState('')
  const [rejectNote, setRejectNote] = useState('')
  const [closeNote, setCloseNote] = useState('')
  const [contactChannel, setContactChannel] = useState('')
  const [customerResponse, setCustomerResponse] = useState('')
  const [contactNote, setContactNote] = useState('')
  const [offerPresented, setOfferPresented] = useState(false)
  const [followUpDate, setFollowUpDate] = useState('')

  const invalidate = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: queryKeys.recommendations.detail(recommendation.recommendation_id) }),
      queryClient.invalidateQueries({ queryKey: queryKeys.customers.customer360(customerId) }),
      queryClient.invalidateQueries({ queryKey: queryKeys.recommendations.list({ customer_id: customerId }) }),
    ])
  }

  const mutation = useMutation({
    mutationFn: async (action: {
      type: 'review' | 'approve' | 'reject' | 'contacted' | 'close'
      payload?: Record<string, unknown>
    }) => {
      const base = { rm_id: RM_USER.id }
      switch (action.type) {
        case 'review':
          return reviewRecommendation(recommendation.recommendation_id, {
            ...base,
            notes: reviewNote || null,
          })
        case 'approve':
          return approveRecommendation(recommendation.recommendation_id, base)
        case 'reject':
          return rejectRecommendation(recommendation.recommendation_id, {
            ...base,
            rejection_reason: rejectReason,
            notes: rejectNote || null,
          })
        case 'contacted':
          return contactedRecommendation(recommendation.recommendation_id, {
            ...base,
            contact_channel: contactChannel || null,
            offer_presented: offerPresented,
            customer_response: customerResponse || null,
            notes: contactNote || null,
            follow_up_date: followUpDate || null,
          })
        case 'close':
          return closeRecommendation(recommendation.recommendation_id, {
            ...base,
            closing_note: closeNote,
          })
      }
    },
    onSuccess: async (result) => {
      toast.success(result.message)
      await invalidate()
      setApproveOpen(false)
      setRejectOpen(false)
      setContactOpen(false)
      setCloseOpen(false)
    },
    onError: (error) => {
      const message =
        error instanceof ApiError
          ? error.message
          : 'Unable to complete the action. Please try again.'
      toast.error(message)
    },
  })

  const status = recommendation.status

  return (
    <Card>
      <CardHeader>
        <CardTitle>RM actions</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-wrap gap-2">
        <Button
          variant="outline"
          disabled={!canTransition(status, 'review') || mutation.isPending}
          onClick={() => {
            setReviewNote('')
            mutation.mutate({ type: 'review' })
          }}
        >
          Review
        </Button>
        <Button
          variant="primary"
          disabled={!canTransition(status, 'approve') || mutation.isPending}
          onClick={() => setApproveOpen(true)}
        >
          Approve for discussion
        </Button>
        <Button
          variant="danger"
          disabled={!canTransition(status, 'reject') || mutation.isPending}
          onClick={() => setRejectOpen(true)}
        >
          Reject
        </Button>
        <Button
          variant="outline"
          disabled={!canTransition(status, 'contacted') || mutation.isPending}
          onClick={() => setContactOpen(true)}
        >
          Mark contacted
        </Button>
        <Button
          variant="secondary"
          disabled={!canTransition(status, 'close') || mutation.isPending}
          onClick={() => setCloseOpen(true)}
        >
          Close
        </Button>
      </CardContent>

      <ConfirmDialog
        open={approveOpen}
        onClose={() => setApproveOpen(false)}
        onConfirm={() => mutation.mutate({ type: 'approve' })}
        title="Approve for discussion"
        description="Approval allows the RM to discuss the recommendation. It does not represent credit or product approval."
        confirmLabel="Approve"
        loading={mutation.isPending}
      />

      <Modal
        open={rejectOpen}
        onClose={() => setRejectOpen(false)}
        title="Reject recommendation"
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setRejectOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="danger"
              disabled={!rejectReason.trim()}
              loading={mutation.isPending}
              onClick={() => mutation.mutate({ type: 'reject' })}
            >
              Reject
            </Button>
          </div>
        }
      >
        <div className="space-y-3">
          <div>
            <label htmlFor="reject-reason" className="text-sm font-medium text-slate-700">
              Rejection reason *
            </label>
            <textarea
              id="reject-reason"
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              rows={3}
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              required
            />
          </div>
          <div>
            <label htmlFor="reject-note" className="text-sm font-medium text-slate-700">
              Note (optional)
            </label>
            <textarea
              id="reject-note"
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              rows={2}
              value={rejectNote}
              onChange={(e) => setRejectNote(e.target.value)}
            />
          </div>
        </div>
      </Modal>

      <Modal
        open={contactOpen}
        onClose={() => setContactOpen(false)}
        title="Mark customer contacted"
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setContactOpen(false)}>
              Cancel
            </Button>
            <Button
              loading={mutation.isPending}
              onClick={() => mutation.mutate({ type: 'contacted' })}
            >
              Save contact
            </Button>
          </div>
        }
      >
        <div className="space-y-3">
          <div>
            <label htmlFor="contact-channel" className="text-sm font-medium text-slate-700">
              Contact channel
            </label>
            <input
              id="contact-channel"
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              value={contactChannel}
              onChange={(e) => setContactChannel(e.target.value)}
            />
          </div>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={offerPresented}
              onChange={(e) => setOfferPresented(e.target.checked)}
            />
            Offer presented
          </label>
          <div>
            <label htmlFor="customer-response" className="text-sm font-medium text-slate-700">
              Customer response
            </label>
            <input
              id="customer-response"
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              value={customerResponse}
              onChange={(e) => setCustomerResponse(e.target.value)}
            />
          </div>
          <div>
            <label htmlFor="follow-up" className="text-sm font-medium text-slate-700">
              Follow-up date
            </label>
            <input
              id="follow-up"
              type="date"
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              value={followUpDate}
              onChange={(e) => setFollowUpDate(e.target.value)}
            />
          </div>
          <div>
            <label htmlFor="contact-note" className="text-sm font-medium text-slate-700">
              Note (optional)
            </label>
            <textarea
              id="contact-note"
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              rows={2}
              value={contactNote}
              onChange={(e) => setContactNote(e.target.value)}
            />
          </div>
        </div>
      </Modal>

      <Modal
        open={closeOpen}
        onClose={() => setCloseOpen(false)}
        title="Close recommendation"
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setCloseOpen(false)}>
              Cancel
            </Button>
            <Button
              disabled={!closeNote.trim()}
              loading={mutation.isPending}
              onClick={() => mutation.mutate({ type: 'close' })}
            >
              Close
            </Button>
          </div>
        }
      >
        <div>
          <label htmlFor="close-note" className="text-sm font-medium text-slate-700">
            Closing reason *
          </label>
          <textarea
            id="close-note"
            className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            rows={3}
            value={closeNote}
            onChange={(e) => setCloseNote(e.target.value)}
            required
          />
        </div>
      </Modal>
    </Card>
  )
}
