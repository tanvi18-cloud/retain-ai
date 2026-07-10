import { MessageSquarePlus } from 'lucide-react'

import type { ConversationSummary } from '../../types/chat'
import { formatRelativeTime } from '../../utils/date'
import { cn } from '../../utils/cn'
import { Badge } from '../ui/Badge'
import { Button } from '../ui/Button'
import { EmptyState } from '../ui/EmptyState'
import { Skeleton } from '../ui/Skeleton'

export interface ConversationListProps {
  conversations: ConversationSummary[]
  selectedId: string | null
  onSelect: (conversationId: string) => void
  onNewConversation?: () => void
  loading?: boolean
}

function conversationTitle(conversation: ConversationSummary): string {
  if (conversation.title?.trim()) return conversation.title.trim()
  if (conversation.last_message_preview?.trim()) return conversation.last_message_preview.trim()
  return 'Untitled conversation'
}

export function ConversationList({
  conversations,
  selectedId,
  onSelect,
  onNewConversation,
  loading = false,
}: ConversationListProps) {
  return (
    <nav aria-label="Conversations" className="flex h-full flex-col">
      <div className="border-b border-slate-100 px-4 py-3">
        <div className="flex items-center justify-between gap-2">
          <h2 className="text-sm font-semibold text-slate-900">Conversations</h2>
          {onNewConversation ? (
            <Button type="button" variant="outline" size="sm" onClick={onNewConversation}>
              <MessageSquarePlus className="h-4 w-4" aria-hidden="true" />
              New
            </Button>
          ) : null}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        {loading ? (
          <ul className="space-y-2" aria-label="Loading conversations">
            {Array.from({ length: 5 }, (_, index) => (
              <li key={index}>
                <Skeleton className="h-16 w-full rounded-lg" />
              </li>
            ))}
          </ul>
        ) : conversations.length === 0 ? (
          <EmptyState
            title="No conversations yet"
            description="Start a new conversation to ask the RM Copilot about your portfolio."
            action={
              onNewConversation
                ? { label: 'Start conversation', onClick: onNewConversation }
                : undefined
            }
          />
        ) : (
          <ul className="space-y-1">
            {conversations.map((conversation) => {
              const isSelected = conversation.conversation_id === selectedId
              const isClosed = conversation.status === 'CLOSED'

              return (
                <li key={conversation.conversation_id}>
                  <button
                    type="button"
                    onClick={() => onSelect(conversation.conversation_id)}
                    aria-current={isSelected ? 'true' : undefined}
                    className={cn(
                      'w-full rounded-lg px-3 py-3 text-left transition-colors',
                      'hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400',
                      isSelected && 'bg-slate-100 ring-1 ring-slate-200',
                    )}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <p className="line-clamp-2 text-sm font-medium text-slate-900">
                        {conversationTitle(conversation)}
                      </p>
                      {isClosed ? <Badge variant="neutral">Closed</Badge> : null}
                    </div>
                    <div className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-slate-500">
                      <span>{conversation.message_count} messages</span>
                      {conversation.active_customer_id ? (
                        <span>· {conversation.active_customer_id}</span>
                      ) : null}
                      <span>· {formatRelativeTime(conversation.updated_at)}</span>
                    </div>
                  </button>
                </li>
              )
            })}
          </ul>
        )}
      </div>
    </nav>
  )
}
