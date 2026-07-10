import { MessageCircleQuestion } from 'lucide-react'

import { cn } from '../../utils/cn'
import { Button } from '../ui/Button'

export interface SuggestedQuestionsProps {
  questions: string[]
  onSelect: (question: string) => void
  disabled?: boolean
}

export function SuggestedQuestions({ questions, onSelect, disabled = false }: SuggestedQuestionsProps) {
  if (questions.length === 0) return null

  return (
    <section aria-label="Suggested questions" className="border-t border-slate-100 bg-slate-50 px-4 py-3">
      <div className="mb-2 flex items-center gap-2 text-xs font-medium text-slate-600">
        <MessageCircleQuestion className="h-3.5 w-3.5" aria-hidden="true" />
        Suggested questions
      </div>
      <div className="flex flex-wrap gap-2">
        {questions.map((question) => (
          <Button
            key={question}
            type="button"
            variant="outline"
            size="sm"
            disabled={disabled}
            className={cn('h-auto whitespace-normal py-2 text-left')}
            onClick={() => onSelect(question)}
          >
            {question}
          </Button>
        ))}
      </div>
    </section>
  )
}
