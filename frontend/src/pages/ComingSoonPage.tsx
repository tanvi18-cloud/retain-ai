import { Link } from 'react-router-dom'

import { PageHeader } from '../components/layout/PageHeader'
import { useDocumentTitle } from '../hooks/useDocumentTitle'

export function ComingSoonPage({ title }: { title: string }) {
  useDocumentTitle(title)

  return (
    <div className="mx-auto max-w-lg py-16 text-center">
      <PageHeader
        title={title}
        description="Coming in the next phase. This navigation item is reserved for Prompt 13."
      />
      <Link
        to="/"
        className="inline-flex h-10 items-center rounded-lg border border-slate-300 bg-white px-4 text-sm font-medium text-slate-800 hover:bg-slate-50"
      >
        Return to portfolio
      </Link>
    </div>
  )
}
