import { useCallback, useState } from 'react'
import { AlertTriangle, Copy, FileSearch, Check } from 'lucide-react'

import type { ChatUiMessage } from '../../hooks/useChatConversation'
import type { ChatEvidence, LLMMode } from '../../types/chat'
import { formatDateTime } from '../../utils/date'
import { cn } from '../../utils/cn'
import { Badge } from '../ui/Badge'
import { Button } from '../ui/Button'

export interface ChatMessageProps {
  message: ChatUiMessage
  mode?: LLMMode | null
  onShowEvidence?: (evidence: ChatEvidence[]) => void
}

function modeBadgeVariant(mode: LLMMode): 'neutral' | 'info' {
  return mode === 'QWEN' ? 'info' : 'neutral'
}

export function ChatMessage({ message, mode, onShowEvidence }: ChatMessageProps) {
  const [copied, setCopied] = useState(false)
  const isUser = message.role === 'USER'
  const isAssistant = message.role === 'ASSISTANT'
  const displayMode = mode ?? (message.mode as LLMMode | undefined)
  const hasEvidence = message.evidence.length > 0
  const hasWarnings = message.warnings.length > 0

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(message.content)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 2000)
    } catch {
      setCopied(false)
    }
  }, [message.content])

  return (
    <article
      className={cn('flex flex-col gap-2', isUser ? 'items-end' : 'items-start')}
      aria-label={isUser ? 'Your message' : 'Assistant message'}
    >
      <div
        className={cn(
          'max-w-[85%] rounded-xl px-4 py-3 text-sm leading-relaxed',
          isUser ? 'bg-slate-900 text-white' : 'bg-white text-slate-900 ring-1 ring-slate-200',
        )}
      >
        <p className="whitespace-pre-wrap break-words">{message.content}</p>
      </div>

      <div
        className={cn(
          'flex max-w-[85%] flex-wrap items-center gap-2 px-1',
          isUser ? 'justify-end' : 'justify-start',
        )}
      >
        <time className="text-xs text-slate-400" dateTime={message.createdAt}>
          {formatDateTime(message.createdAt)}
        </time>

        {isAssistant && displayMode ? (
          <Badge variant={modeBadgeVariant(displayMode)}>{displayMode}</Badge>
        ) : null}

        {isAssistant ? (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            aria-label={copied ? 'Copied to clipboard' : 'Copy response'}
            onClick={() => void handleCopy()}
          >
            {copied ? (
              <Check className="h-3.5 w-3.5 text-emerald-600" aria-hidden="true" />
            ) : (
              <Copy className="h-3.5 w-3.5" aria-hidden="true" />
            )}
            <span className="text-xs">{copied ? 'Copied' : 'Copy'}</span>
          </Button>
        ) : null}

        {isAssistant && hasEvidence && onShowEvidence ? (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            aria-label={`View ${message.evidence.length} evidence items`}
            onClick={() => onShowEvidence(message.evidence)}
          >
            <FileSearch className="h-3.5 w-3.5" aria-hidden="true" />
            <span className="text-xs">Evidence ({message.evidence.length})</span>
          </Button>
        ) : null}
      </div>

      {isAssistant && hasWarnings ? (
        <ul
          className="max-w-[85%] space-y-1 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2"
          aria-label="Warnings"
        >
          {message.warnings.map((warning) => (
            <li key={warning} className="flex items-start gap-2 text-xs text-amber-900">
              <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden="true" />
              <span>{warning}</span>
            </li>
          ))}
        </ul>
      ) : null}
    </article>
  )
}
