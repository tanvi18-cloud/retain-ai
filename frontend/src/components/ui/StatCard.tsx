import type { ReactNode } from 'react'

import { cn } from '../../utils/cn'
import { Card, CardContent } from './Card'
import { Tooltip } from './Tooltip'

export interface StatCardProps {
  label: string
  value: ReactNode
  description: string
  icon?: ReactNode
  tooltip?: string
  className?: string
}

export function StatCard({ label, value, description, icon, tooltip, className }: StatCardProps) {
  const content = (
    <Card className={cn('h-full', className)}>
      <CardContent className="flex h-full flex-col gap-3">
        <div className="flex items-start justify-between gap-3">
          <p className="text-sm font-medium text-slate-500">{label}</p>
          {icon ? (
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-600">
              {icon}
            </span>
          ) : null}
        </div>
        <p className="text-2xl font-semibold tracking-tight text-slate-900">{value}</p>
        <p className="text-xs text-slate-500">{description}</p>
      </CardContent>
    </Card>
  )

  if (tooltip) {
    return <Tooltip content={tooltip}>{content}</Tooltip>
  }

  return content
}
