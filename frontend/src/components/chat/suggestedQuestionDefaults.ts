export const DEFAULT_SUGGESTED_QUESTIONS = [
  'Who should I call today?',
  'Show high-value, high-risk customers.',
  'Which customers have home-loan inquiries?',
  'How much revenue is currently at risk?',
] as const

export const CUSTOMER_CONTEXT_SUGGESTED_QUESTIONS = [
  'Why is this customer high risk?',
  'Which offers are eligible?',
  'What should I discuss on the call?',
  'What data is stale?',
  'What is the latest recommendation status?',
] as const

export const C004_SUGGESTED_QUESTIONS = [
  'Why are lending offers blocked?',
  'What support option is available?',
  'What should the RM avoid promising?',
] as const

export function resolveSuggestedQuestions(
  customerContext: string | null,
  apiSuggestions: string[],
): string[] {
  if (apiSuggestions.length > 0) return apiSuggestions
  if (customerContext === 'C004') {
    return [...CUSTOMER_CONTEXT_SUGGESTED_QUESTIONS, ...C004_SUGGESTED_QUESTIONS]
  }
  if (customerContext) return [...CUSTOMER_CONTEXT_SUGGESTED_QUESTIONS]
  return [...DEFAULT_SUGGESTED_QUESTIONS]
}
