import type { ReactNode } from 'react'

import { cn } from '../../utils/cn'
import { Badge, type BadgeVariant } from '../ui/Badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/Card'
import { Skeleton } from '../ui/Skeleton'

export type StatusCardState = 'healthy' | 'warning' | 'error' | 'neutral' | 'loading'

export interface StatusCardProps {
  title: string
  statusLabel: string
  state: StatusCardState
  description?: string
  icon?: ReactNode
  children?: ReactNode
  className?: string
}

const STATE_VARIANT: Record<Exclude<StatusCardState, 'loading'>, BadgeVariant> = {
  healthy: 'success',
  warning: 'warning',
  error: 'danger',
  neutral: 'neutral',
}

const STATE_INDICATOR: Record<Exclude<StatusCardState, 'loading'>, string> = {
  healthy: 'bg-emerald-500',
  warning: 'bg-amber-500',
  error: 'bg-red-500',
  neutral: 'bg-slate-400',
}

export function StatusCard({
  title,
  statusLabel,
  state,
  description,
  icon,
  children,
  className,
}: StatusCardProps) {
  return (
    <Card className={cn('h-full', className)}>
      <CardHeader>
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <CardTitle>{title}</CardTitle>
            {description ? <CardDescription>{description}</CardDescription> : null}
          </div>
          {icon ? (
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-600">
              {icon}
            </span>
          ) : null}
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {state === 'loading' ? (
          <Skeleton className="h-6 w-28" />
        ) : (
          <Badge variant={STATE_VARIANT[state]} className="gap-1.5">
            <span
              className={cn('h-2 w-2 rounded-full', STATE_INDICATOR[state])}
              aria-hidden="true"
            />
            {statusLabel}
          </Badge>
        )}
        {children}
      </CardContent>
    </Card>
  )
}
