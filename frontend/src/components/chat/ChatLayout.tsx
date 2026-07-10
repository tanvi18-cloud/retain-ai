import { useCallback, useState } from 'react'
import { Menu, XCircle } from 'lucide-react'

import { useChatConversation } from '../../hooks/useChatConversation'
import type { ChatEvidence, LLMMode } from '../../types/chat'
import { cn } from '../../utils/cn'
import { PageHeader } from '../layout/PageHeader'
import { Badge } from '../ui/Badge'
import { Button } from '../ui/Button'
import { Drawer } from '../ui/Drawer'
import { EmptyState } from '../ui/EmptyState'
import { ErrorState } from '../ui/ErrorState'
import { Skeleton } from '../ui/Skeleton'
import { ChatComposer } from './ChatComposer'
import { ChatMessage } from './ChatMessage'
import { ConversationList } from './ConversationList'
import { CustomerContextSelector } from './CustomerContextSelector'
import { EvidencePanel } from './EvidencePanel'
import { SuggestedQuestions } from './SuggestedQuestions'

export function ChatLayout() {
  const {
    conversationId,
    customerContext,
    setCustomerContext,
    conversations,
    conversationsLoading,
    conversationLoading,
    messages,
    suggestedQuestions,
    lastMode,
    lastWarnings,
    isSending,
    sendError,
    getErrorMessage,
    sendMessage,
    startNewConversation,
    selectConversation,
    closeConversation,
    isClosing,
  } = useChatConversation()

  const [mobileConversationsOpen, setMobileConversationsOpen] = useState(false)
  const [evidenceOpen, setEvidenceOpen] = useState(false)
  const [activeEvidence, setActiveEvidence] = useState<ChatEvidence[]>([])

  const handleSelectConversation = useCallback(
    (id: string) => {
      selectConversation(id)
      setMobileConversationsOpen(false)
    },
    [selectConversation],
  )

  const handleNewConversation = useCallback(() => {
    startNewConversation()
    setMobileConversationsOpen(false)
  }, [startNewConversation])

  const handleShowEvidence = useCallback((evidence: ChatEvidence[]) => {
    setActiveEvidence(evidence)
    setEvidenceOpen(true)
  }, [])

  const handleSuggestedQuestion = useCallback(
    (question: string) => {
      void sendMessage(question)
    },
    [sendMessage],
  )

  const lastAssistantMessageId = [...messages].reverse().find((msg) => msg.role === 'ASSISTANT')?.id

  const conversationList = (
    <ConversationList
      conversations={conversations}
      selectedId={conversationId}
      onSelect={handleSelectConversation}
      onNewConversation={handleNewConversation}
      loading={conversationsLoading}
    />
  )

  return (
    <div className="flex h-[calc(100svh-8rem)] min-h-[32rem] flex-col">
      <PageHeader
        title="RM Copilot"
        description="Ask questions about customer risk, retention offers, and portfolio insights."
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="lg:hidden"
              onClick={() => setMobileConversationsOpen(true)}
            >
              <Menu className="h-4 w-4" aria-hidden="true" />
              Conversations
            </Button>
            {conversationId ? (
              <Button
                type="button"
                variant="outline"
                size="sm"
                loading={isClosing}
                onClick={() => closeConversation()}
              >
                <XCircle className="h-4 w-4" aria-hidden="true" />
                Close conversation
              </Button>
            ) : null}
          </div>
        }
        meta={
          lastMode ? (
            <Badge variant={lastMode === 'QWEN' ? 'info' : 'neutral'}>Mode: {lastMode}</Badge>
          ) : null
        }
      />

      <div className="flex min-h-0 flex-1 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <aside className="hidden w-72 shrink-0 border-r border-slate-200 lg:block">{conversationList}</aside>

        <Drawer
          open={mobileConversationsOpen}
          onClose={() => setMobileConversationsOpen(false)}
          title="Conversations"
        >
          {conversationList}
        </Drawer>

        <section className="flex min-w-0 flex-1 flex-col" aria-label="Chat">
          <div className="flex-1 overflow-y-auto px-4 py-4">
            {conversationLoading && conversationId ? (
              <div className="space-y-4" aria-label="Loading messages">
                <Skeleton className="ml-auto h-16 w-2/3 rounded-xl" />
                <Skeleton className="h-24 w-3/4 rounded-xl" />
              </div>
            ) : messages.length === 0 ? (
              <EmptyState
                title="Start a conversation"
                description="Select a customer context or ask a portfolio-wide question to begin."
              />
            ) : (
              <div className="space-y-6">
                {messages.map((message) => (
                  <ChatMessage
                    key={message.id}
                    message={message}
                    mode={
                      message.role === 'ASSISTANT' && message.id === lastAssistantMessageId
                        ? (lastMode as LLMMode | null)
                        : null
                    }
                    onShowEvidence={handleShowEvidence}
                  />
                ))}
              </div>
            )}

            {sendError ? (
              <div className="mt-4">
                <ErrorState message={getErrorMessage(sendError)} />
              </div>
            ) : null}

            {!sendError && lastWarnings.length > 0 && messages.length > 0 ? (
              <ul
                className="mt-4 space-y-1 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2"
                aria-label="Response warnings"
              >
                {lastWarnings.map((warning) => (
                  <li key={warning} className="text-xs text-amber-900">
                    {warning}
                  </li>
                ))}
              </ul>
            ) : null}
          </div>

          <SuggestedQuestions
            questions={suggestedQuestions}
            onSelect={handleSuggestedQuestion}
            disabled={isSending}
          />

          <ChatComposer onSend={sendMessage} isSending={isSending} disabled={isClosing} />
        </section>

        <aside
          className={cn(
            'hidden w-72 shrink-0 border-l border-slate-200 p-4 lg:block',
            'overflow-y-auto',
          )}
          aria-label="Customer context"
        >
          <CustomerContextSelector
            value={customerContext}
            onChange={setCustomerContext}
            disabled={isSending}
          />
        </aside>
      </div>

      <div className="mt-4 lg:hidden">
        <CustomerContextSelector
          value={customerContext}
          onChange={setCustomerContext}
          disabled={isSending}
        />
      </div>

      <EvidencePanel
        open={evidenceOpen}
        onClose={() => setEvidenceOpen(false)}
        evidence={activeEvidence}
      />
    </div>
  )
}
