import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { ConfirmDialog } from '../components/ui/ConfirmDialog'

describe('ConfirmDialog', () => {
  it('renders title, description, and footer without modal body content', async () => {
    const user = userEvent.setup()
    const onConfirm = vi.fn()
    const onClose = vi.fn()

    render(
      <ConfirmDialog
        open
        title="Approve for discussion"
        description="Approval allows the RM to discuss the recommendation."
        onConfirm={onConfirm}
        onClose={onClose}
        confirmLabel="Approve"
      />,
    )

    const dialog = screen.getByRole('dialog')
    expect(dialog).toHaveAttribute('aria-labelledby')
    expect(screen.getByRole('heading', { name: 'Approve for discussion' })).toBeInTheDocument()
    expect(screen.getByText('Approval allows the RM to discuss the recommendation.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Approve' })).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Approve' }))
    expect(onConfirm).toHaveBeenCalledOnce()
  })
})
