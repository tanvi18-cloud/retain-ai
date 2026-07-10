import { useState, type ReactNode } from 'react'

import { cn } from '../../utils/cn'

export interface TabItem {
  id: string
  label: string
  content: ReactNode
}

export interface TabsProps {
  items: TabItem[]
  defaultTab?: string
}

export function Tabs({ items, defaultTab }: TabsProps) {
  const [active, setActive] = useState(defaultTab ?? items[0]?.id)

  const activeItem = items.find((item) => item.id === active) ?? items[0]

  return (
    <div>
      <div
        role="tablist"
        aria-label="Sections"
        className="flex flex-wrap gap-1 border-b border-slate-200"
      >
        {items.map((item) => (
          <button
            key={item.id}
            type="button"
            role="tab"
            aria-selected={active === item.id}
            aria-controls={`tabpanel-${item.id}`}
            id={`tab-${item.id}`}
            className={cn(
              'rounded-t-lg px-4 py-2 text-sm font-medium transition-colors',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400',
              active === item.id
                ? 'border-b-2 border-slate-900 text-slate-900'
                : 'text-slate-500 hover:text-slate-800',
            )}
            onClick={() => setActive(item.id)}
          >
            {item.label}
          </button>
        ))}
      </div>
      <div
        role="tabpanel"
        id={`tabpanel-${activeItem?.id}`}
        aria-labelledby={`tab-${activeItem?.id}`}
        className="py-4"
      >
        {activeItem?.content}
      </div>
    </div>
  )
}
