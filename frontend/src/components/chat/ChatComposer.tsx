import { useCallback, useId, useState, type FormEvent, type KeyboardEvent } from 'react'
import { Send } from 'lucide-react'

import { cn } from '../../utils/cn'
import { Button } from '../ui/Button'

const DEFAULT_MAX_LENGTH = 2000

export interface ChatComposerProps {
  onSend: (message: string) => void | Promise<void>
  disabled?: boolean
  isSending?: boolean
  placeholder?: string
  maxLength?: number
}

export function ChatComposer({
  onSend,
  disabled = false,
  isSending = false,
  placeholder = 'Ask about customer risk, offers, or portfolio insights…',
  maxLength = DEFAULT_MAX_LENGTH,
}: ChatComposerProps) {
  const labelId = useId()
  const counterId = useId()
  const [value, setValue] = useState('')

  const trimmed = value.trim()
  const charCount = value.length
  const isOverLimit = charCount > maxLength
  const canSend = trimmed.length > 0 && !isOverLimit && !disabled && !isSending

  const submit = useCallback(async () => {
    if (!canSend) return
    const message = trimmed
    setValue('')
    await onSend(message)
  }, [canSend, onSend, trimmed])

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    void submit()
  }

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key !== 'Enter' || event.shiftKey) return
    event.preventDefault()
    void submit()
  }

  return (
    <form onSubmit={handleSubmit} className="border-t border-slate-200 bg-white px-4 py-3">
      <label id={labelId} htmlFor={`${labelId}-input`} className="sr-only">
        Message
      </label>
      <div className="flex flex-col gap-2">
        <textarea
          id={`${labelId}-input`}
          aria-labelledby={labelId}
          aria-describedby={counterId}
          value={value}
          onChange={(event) => setValue(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled || isSending}
          rows={3}
          maxLength={maxLength + 100}
          className={cn(
            'w-full resize-none rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900',
            'placeholder:text-slate-400 focus:border-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-200',
            'disabled:cursor-not-allowed disabled:bg-slate-50 disabled:text-slate-500',
            isOverLimit && 'border-red-300 focus:border-red-400 focus:ring-red-100',
          )}
        />
        <div className="flex items-center justify-between gap-3">
          <p id={counterId} className={cn('text-xs', isOverLimit ? 'text-red-600' : 'text-slate-500')}>
            {charCount}/{maxLength}
            <span className="sr-only"> characters entered</span>
          </p>
          <p className="hidden text-xs text-slate-400 sm:block">
            Enter to send · Shift+Enter for new line
          </p>
          <Button type="submit" size="sm" disabled={!canSend} loading={isSending}>
            <Send className="h-4 w-4" aria-hidden="true" />
            Send
          </Button>
        </div>
      </div>
    </form>
  )
}
