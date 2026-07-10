import { beforeAll, afterAll, afterEach, describe, expect, it } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { ChatPage } from '../pages/ChatPage'
import {
  C004_SUGGESTED_QUESTIONS,
  DEFAULT_SUGGESTED_QUESTIONS,
} from '../components/chat/suggestedQuestionDefaults'
import { resetMockState, server, setClosedConversation, setQwenUnavailable } from './handlers'
import { renderWithProviders } from './utils'

beforeAll(() => server.listen())
afterEach(() => {
  server.resetHandlers()
  resetMockState()
})
afterAll(() => server.close())

describe('RM Copilot chat', () => {
  it('shows default suggested questions', async () => {
    renderWithProviders(<ChatPage />, { route: '/chat' })
    for (const question of DEFAULT_SUGGESTED_QUESTIONS) {
      expect(await screen.findByRole('button', { name: question })).toBeInTheDocument()
    }
  })

  it('sends a message and displays assistant response', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ChatPage />, { route: '/chat' })

    const textarea = await screen.findByLabelText('Message')
    await user.type(textarea, 'Who should I call today?')
    await user.click(screen.getByRole('button', { name: 'Send' }))

    expect(
      await screen.findByText('Start with C001 — high priority score and unacknowledged alerts.'),
    ).toBeInTheDocument()
  })

  it('selects customer context and shows C004 suggestions', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ChatPage />, { route: '/chat' })

    const c004Options = await screen.findAllByRole('option', { name: /^C004\b/ })
    await user.click(c004Options[0])

    for (const question of C004_SUGGESTED_QUESTIONS) {
      expect(await screen.findByRole('button', { name: question })).toBeInTheDocument()
    }
  })

  it('submits suggested question', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ChatPage />, { route: '/chat' })

    await user.click(await screen.findByRole('button', { name: DEFAULT_SUGGESTED_QUESTIONS[0] }))
    expect(
      await screen.findByText('Start with C001 — high priority score and unacknowledged alerts.'),
    ).toBeInTheDocument()
  })

  it('shows evidence panel', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ChatPage />, { route: '/chat' })

    await user.click(await screen.findByRole('button', { name: DEFAULT_SUGGESTED_QUESTIONS[0] }))
    await screen.findByText('Start with C001 — high priority score and unacknowledged alerts.')

    await user.click(screen.getByRole('button', { name: /View 1 evidence items/i }))
    expect(await screen.findByText('priority_score')).toBeInTheDocument()
  })

  it('shows warnings from assistant response', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ChatPage />, { route: '/chat' })

    await user.click(await screen.findByRole('button', { name: DEFAULT_SUGGESTED_QUESTIONS[0] }))
    expect(
      await screen.findAllByText('Synthetic data — not for production decisions.'),
    ).not.toHaveLength(0)
  })

  it('reuses existing conversation from sidebar', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ChatPage />, { route: '/chat' })

    await user.click(await screen.findByRole('button', { name: /Portfolio priorities/i }))
    expect(screen.getByRole('article', { name: 'Your message' })).toHaveTextContent(
      'Who should I call today?',
    )
  })

  it('shows closed-conversation error', async () => {
    setClosedConversation()
    const user = userEvent.setup()
    renderWithProviders(<ChatPage />, { route: '/chat' })

    await user.click(await screen.findByRole('button', { name: DEFAULT_SUGGESTED_QUESTIONS[0] }))
    expect(
      await screen.findByText('This conversation is closed. Start a new conversation.'),
    ).toBeInTheDocument()
  })

  it('shows Qwen unavailable error', async () => {
    setQwenUnavailable()
    const user = userEvent.setup()
    renderWithProviders(<ChatPage />, { route: '/chat' })

    await user.click(await screen.findByRole('button', { name: DEFAULT_SUGGESTED_QUESTIONS[0] }))
    expect(
      await screen.findByText('Qwen is unavailable. Check system status or use mock mode.'),
    ).toBeInTheDocument()
  })

  it('sends on Enter and inserts newline on Shift+Enter', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ChatPage />, { route: '/chat' })

    const textarea = await screen.findByLabelText('Message')
    await user.type(textarea, 'Line one{Shift>}{Enter}Line two')
    expect(textarea).toHaveValue('Line one\nLine two')

    await user.type(textarea, '{Enter}')
    await waitFor(() =>
      expect(
        screen.getByText('Start with C001 — high priority score and unacknowledged alerts.'),
      ).toBeInTheDocument(),
    )
  })

  it('disables blank message submission', async () => {
    renderWithProviders(<ChatPage />, { route: '/chat' })
    const sendButton = await screen.findByRole('button', { name: 'Send' })
    expect(sendButton).toBeDisabled()
  })
})
