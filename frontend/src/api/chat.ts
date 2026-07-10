import { get, post } from './client'
import type { PaginatedResponse } from '../types/api'
import type {
  ChatRequest,
  ChatResponse,
  ConversationCloseRequest,
  ConversationDetail,
  ConversationSummary,
} from '../types/chat'
import type { ChatConversationStatus } from '../types/chat'

export function sendChatMessage(body: ChatRequest) {
  return post<ChatResponse>('/chat', body)
}

export interface ConversationsListParams {
  rm_id: string
  page?: number
  page_size?: number
  status?: ChatConversationStatus
  sort_order?: 'asc' | 'desc'
}

export function listConversations(params: ConversationsListParams) {
  return get<PaginatedResponse<ConversationSummary>>('/chat/conversations', { ...params })
}

export function getConversation(conversationId: string, rmId: string) {
  return get<ConversationDetail>(`/chat/conversations/${conversationId}`, { rm_id: rmId })
}

export function closeConversation(conversationId: string, body: ConversationCloseRequest) {
  return post<ConversationDetail>(`/chat/conversations/${conversationId}/close`, body)
}
