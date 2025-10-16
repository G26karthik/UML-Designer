import React from 'react';
// errorHandler.js and related exports removed. Use generic error message rendering below.

class GlobalErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    // Log the error and set state with error and errorInfo
    const safeError = error || new Error('An unknown error occurred.');
    this.setState({ error: safeError, errorInfo });
    console.error('Global Error Boundary caught an error:', {
      error: safeError,
      componentStack: errorInfo.componentStack,
      correlationId: safeError.correlationId
    });
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  render() {
    if (this.state.hasError) {
      const { error } = this.state;

      return (
        <div className="min-h-screen bg-gradient-to-br from-red-50 via-white to-red-50 flex items-center justify-center p-4">
          <div className="max-w-2xl w-full bg-white rounded-2xl shadow-xl p-8">
            <div className="text-center mb-6">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-red-100 rounded-full mb-4">
                <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">Something went wrong</h1>
              <p className="text-gray-600">
                {error.userMessage ? error.userMessage.message : 'An unexpected error occurred'}
              </p>
            </div>

            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0">
                  <svg className="w-5 h-5 text-red-400 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="flex-1">
                  <h3 className="text-sm font-medium text-red-800 mb-1">
                    {error.userMessage ? error.userMessage.title : 'Application Error'}
                  </h3>
                  <p className="text-sm text-red-700 mb-2">
                    {error.userMessage ? error.userMessage.message : error.message}
                  </p>
                  {error.correlationId && (
                    <p className="text-xs text-red-600 mb-2">
                      Correlation ID: {error.correlationId}
                    </p>
                  )}
                  {error.userMessage && error.userMessage.suggestion && (
                    <div className="mt-2 p-2 bg-red-100 rounded text-xs text-red-800">
                      💡 {error.userMessage.suggestion}
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="flex gap-3 justify-center">
              <button
                onClick={this.handleRetry}
                className="bg-emerald-600 text-white px-6 py-2 rounded-lg hover:bg-emerald-700 transition font-medium"
              >
                Try Again
              </button>
              <button
                onClick={() => window.location.reload()}
                className="bg-gray-600 text-white px-6 py-2 rounded-lg hover:bg-gray-700 transition font-medium"
              >
                Reload Page
              </button>
            </div>

            {process.env.NODE_ENV === 'development' && this.state.errorInfo && (
              <details className="mt-6">
                <summary className="cursor-pointer text-sm text-gray-600 hover:text-gray-800">
                  Technical Details (Development Only)
                </summary>
                <div className="mt-2 p-4 bg-gray-100 rounded-lg text-xs font-mono text-gray-800 overflow-auto max-h-40">
                  <p className="mb-2"><strong>Error:</strong> {error.message}</p>
                  <p className="mb-2"><strong>Stack:</strong></p>
                  <pre className="whitespace-pre-wrap">{error.stack}</pre>
                  <p className="mb-2 mt-4"><strong>Component Stack:</strong></p>
                  <pre className="whitespace-pre-wrap">{this.state.errorInfo.componentStack}</pre>
                </div>
              </details>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default GlobalErrorBoundary;