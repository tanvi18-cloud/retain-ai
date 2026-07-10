import { useId, useState, type ReactNode } from 'react'

import { cn } from '../../utils/cn'

export interface TooltipProps {
  content: ReactNode
  children: ReactNode
  className?: string
}

export function Tooltip({ content, children, className }: TooltipProps) {
  const [open, setOpen] = useState(false)
  const tooltipId = useId()

  return (
    <span
      className={cn('relative inline-flex', className)}
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
      onFocus={() => setOpen(true)}
      onBlur={() => setOpen(false)}
    >
      <span aria-describedby={open ? tooltipId : undefined} tabIndex={0} className="inline-flex">
        {children}
      </span>
      {open ? (
        <span
          id={tooltipId}
          role="tooltip"
          className="absolute bottom-full left-1/2 z-20 mb-2 w-56 -translate-x-1/2 rounded-lg bg-slate-900 px-3 py-2 text-xs text-white shadow-lg"
        >
          {content}
        </span>
      ) : null}
    </span>
  )
}

export const BANKING_TOOLTIPS = {
  dpd: 'Days Past Due indicates the maximum recorded repayment delay in the configured period.',
  churnScore: 'Churn score estimates how likely the customer is to reduce or end the relationship.',
  customerValue: 'Customer value score reflects estimated annual relationship value and depth.',
  priorityScore: 'Priority score combines churn risk and customer value for RM outreach ranking.',
  revenueAtRisk: 'Revenue at risk is the estimated annual value exposed if the customer churns.',
} as const
