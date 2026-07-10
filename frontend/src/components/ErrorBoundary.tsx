import { Component, type ErrorInfo, type ReactNode } from 'react'

import { ErrorState } from './ui/ErrorState'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  message: string
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, message: '' }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, message: error.message || 'An unexpected error occurred.' }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Application error:', error, info)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-svh items-center justify-center p-6">
          <div className="max-w-lg">
            <ErrorState
              title="Application error"
              message={this.state.message}
              onRetry={() => this.setState({ hasError: false, message: '' })}
            />
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
