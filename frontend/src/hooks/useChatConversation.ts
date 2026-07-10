import { useCallback, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { closeConversation, getConversation, listConversations, sendChatMessage } from '../api/chat'
import { getRmUser } from '../api/env'
import { ApiError } from '../api/client'
import type { ChatEvidence, ChatMessageResponse, ChatResponse, ConversationDetail } from '../types/chat'
import { resolveSuggestedQuestions } from '../components/chat/suggestedQuestionDefaults'
import { queryKeys } from '../utils/queryKeys'

export interface ChatUiMessage {
  id: string
  role: 'USER' | 'ASSISTANT'
  content: string
  evidence: ChatEvidence[]
  warnings: string[]
  mode?: string
  createdAt: string
}

function toUiMessages(detail: ConversationDetail): ChatUiMessage[] {
  return detail.messages.map((msg: ChatMessageResponse) => ({
    id: msg.message_id,
    role: msg.role === 'USER' ? 'USER' : 'ASSISTANT',
    content: msg.content,
    evidence: msg.evidence,
    warnings: msg.warnings,
    createdAt: msg.created_at,
  }))
}

export function useChatConversation() {
  const queryClient = useQueryClient()
  const rm = getRmUser()
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [customerContext, setCustomerContext] = useState<string | null>(null)
  const [pendingMessages, setPendingMessages] = useState<ChatUiMessage[]>([])
  const [suggestedQuestions, setSuggestedQuestions] = useState<string[]>([])
  const [lastMode, setLastMode] = useState<string | null>(null)
  const [lastWarnings, setLastWarnings] = useState<string[]>([])

  const conversationsQuery = useQuery({
    queryKey: queryKeys.chat.conversations({ rm_id: rm.id }),
    queryFn: () => listConversations({ rm_id: rm.id, page_size: 50 }),
  })

  const conversationQuery = useQuery({
    queryKey: queryKeys.chat.conversation(conversationId ?? ''),
    queryFn: () => getConversation(conversationId!, rm.id),
    enabled: Boolean(conversationId),
  })

  const sendMutation = useMutation({
    mutationFn: (message: string) =>
      sendChatMessage({
        message,
        rm_id: rm.id,
        conversation_id: conversationId,
        customer_id: customerContext,
        include_history: true,
      }),
    onMutate: (message) => {
      const optimistic: ChatUiMessage = {
        id: `pending-${Date.now()}`,
        role: 'USER',
        content: message,
        evidence: [],
        warnings: [],
        createdAt: new Date().toISOString(),
      }
      setPendingMessages((prev) => [...prev, optimistic])
    },
    onSuccess: (response: ChatResponse) => {
      setConversationId(response.conversation_id)
      setSuggestedQuestions(response.suggested_questions)
      setLastMode(response.mode)
      setLastWarnings(response.warnings)
      setPendingMessages([])
      void queryClient.invalidateQueries({ queryKey: queryKeys.chat.conversation(response.conversation_id) })
      void queryClient.invalidateQueries({ queryKey: queryKeys.chat.conversations({ rm_id: rm.id }) })
    },
    onError: () => {
      setPendingMessages([])
    },
  })

  const closeMutation = useMutation({
    mutationFn: () => closeConversation(conversationId!, { rm_id: rm.id }),
    onSuccess: () => {
      setConversationId(null)
      setPendingMessages([])
      void queryClient.invalidateQueries({ queryKey: queryKeys.chat.conversations({ rm_id: rm.id }) })
    },
  })

  const startNewConversation = useCallback(() => {
    setConversationId(null)
    setPendingMessages([])
    setSuggestedQuestions([])
    setLastWarnings([])
  }, [])

  const selectConversation = useCallback((id: string) => {
    setConversationId(id)
    setPendingMessages([])
  }, [])

  const messages: ChatUiMessage[] = [
    ...(conversationQuery.data ? toUiMessages(conversationQuery.data) : []),
    ...pendingMessages,
  ]

  const sendMessage = useCallback(
    async (message: string) => {
      const trimmed = message.trim()
      if (!trimmed || sendMutation.isPending) return
      try {
        await sendMutation.mutateAsync(trimmed)
      } catch {
        // Mutation error is surfaced via sendError.
      }
    },
    [sendMutation],
  )

  const getErrorMessage = (error: unknown): string => {
    if (error instanceof ApiError) {
      if (error.status === 409) return 'This conversation is closed. Start a new conversation.'
      if (error.status === 503) return 'Qwen is unavailable. Check system status or use mock mode.'
      return error.message
    }
    return 'Unable to send message. Please try again.'
  }

  return {
    rm,
    conversationId,
    customerContext,
    setCustomerContext,
    conversations: conversationsQuery.data?.items ?? [],
    conversationsLoading: conversationsQuery.isLoading,
    conversation: conversationQuery.data ?? null,
    conversationLoading: conversationQuery.isLoading,
    messages,
    suggestedQuestions: resolveSuggestedQuestions(customerContext, suggestedQuestions),
    lastMode,
    lastWarnings,
    isSending: sendMutation.isPending,
    sendError: sendMutation.error,
    getErrorMessage,
    sendMessage,
    startNewConversation,
    selectConversation,
    closeConversation: () => closeMutation.mutate(),
    isClosing: closeMutation.isPending,
  }
}
