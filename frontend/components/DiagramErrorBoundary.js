'use client';

import { Component } from 'react';

/**
 * Error boundary specifically designed for diagram rendering failures
 * Provides graceful fallbacks for various types of Mermaid/diagram errors
 */
export class DiagramErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { 
      hasError: false, 
      error: null, 
      errorInfo: null,
      retryCount: 0
    };
  }

  static getDerivedStateFromError(error) {
    // Update state to show fallback UI
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({
      error,
      errorInfo,
      hasError: true
    });

    // Log the error for debugging
    if (process.env.NODE_ENV === 'development') {
      console.error('DiagramErrorBoundary caught an error:', error, errorInfo);
    }

    // Send to error reporting service if available
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  retry = () => {
    if (this.state.retryCount < 3) {
      this.setState(prevState => ({
        hasError: false,
        error: null,
        errorInfo: null,
        retryCount: prevState.retryCount + 1
      }));
    }
  };

  reset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: 0
    });
  };

  renderErrorMessage(error) {
    if (!error) return 'An unknown error occurred while rendering the diagram.';

    const errorMessage = error.message || error.toString();
    
    // Categorize common Mermaid errors
    if (errorMessage.includes('Parse error') || errorMessage.includes('syntax error')) {
      return 'Invalid diagram syntax. Please check your code structure.';
    }
    
    if (errorMessage.includes('Maximum call stack') || errorMessage.includes('recursion')) {
      return 'Diagram is too complex or contains circular references.';
    }
    
    if (errorMessage.includes('module') || errorMessage.includes('import')) {
      return 'Failed to load diagram rendering library. Please try refreshing the page.';
    }
    
    if (errorMessage.includes('timeout') || errorMessage.includes('abort')) {
      return 'Diagram rendering timed out. The diagram may be too large or complex.';
    }

    return `Diagram rendering error: ${errorMessage}`;
  }

  render() {
    if (this.state.hasError) {
      const canRetry = this.state.retryCount < 3;
      const errorMessage = this.renderErrorMessage(this.state.error);

      return (
        <div className="diagram-error-boundary">
          <div className="error-content">
            <div className="error-icon">⚠️</div>
            <div className="error-message">
              <h3>Diagram Rendering Failed</h3>
              <p>{errorMessage}</p>
              
              {process.env.NODE_ENV === 'development' && this.state.error && (
                <details className="error-details">
                  <summary>Error Details (Development)</summary>
                  <pre>{this.state.error.stack}</pre>
                  {this.state.errorInfo && (
                    <pre>{this.state.errorInfo.componentStack}</pre>
                  )}
                </details>
              )}
            </div>
            
            <div className="error-actions">
              {canRetry && (
                <button 
                  onClick={this.retry}
                  className="retry-button"
                  type="button"
                >
                  Retry ({3 - this.state.retryCount} attempts left)
                </button>
              )}
              
              <button 
                onClick={this.reset}
                className="reset-button"
                type="button"
              >
                Reset
              </button>
              
              {this.props.onFallback && (
                <button 
                  onClick={this.props.onFallback}
                  className="fallback-button"
                  type="button"
                >
                  Show Raw Text
                </button>
              )}
            </div>
          </div>

          <style jsx>{`
            .diagram-error-boundary {
              display: flex;
              align-items: center;
              justify-content: center;
              min-height: 200px;
              padding: 2rem;
              border: 2px dashed #e5e7eb;
              border-radius: 8px;
              background-color: #fef2f2;
              color: #991b1b;
              text-align: center;
              margin: 1rem 0;
            }

            .error-content {
              max-width: 500px;
            }

            .error-icon {
              font-size: 3rem;
              margin-bottom: 1rem;
            }

            .error-message h3 {
              margin: 0 0 1rem 0;
              font-size: 1.25rem;
              font-weight: 600;
            }

            .error-message p {
              margin: 0 0 1.5rem 0;
              color: #7f1d1d;
            }

            .error-details {
              text-align: left;
              margin: 1rem 0;
              padding: 1rem;
              background-color: #fee2e2;
              border-radius: 4px;
              font-size: 0.875rem;
            }

            .error-details summary {
              cursor: pointer;
              font-weight: 600;
              margin-bottom: 0.5rem;
            }

            .error-details pre {
              white-space: pre-wrap;
              word-break: break-all;
              font-size: 0.75rem;
              color: #7f1d1d;
              margin: 0.5rem 0;
            }

            .error-actions {
              display: flex;
              gap: 0.75rem;
              justify-content: center;
              flex-wrap: wrap;
            }

            .error-actions button {
              padding: 0.5rem 1rem;
              border: none;
              border-radius: 4px;
              cursor: pointer;
              font-size: 0.875rem;
              font-weight: 500;
              transition: all 0.2s;
            }

            .retry-button {
              background-color: #dc2626;
              color: white;
            }

            .retry-button:hover {
              background-color: #b91c1c;
            }

            .reset-button {
              background-color: #6b7280;
              color: white;
            }

            .reset-button:hover {
              background-color: #4b5563;
            }

            .fallback-button {
              background-color: #059669;
              color: white;
            }

            .fallback-button:hover {
              background-color: #047857;
            }

            .error-actions button:disabled {
              opacity: 0.5;
              cursor: not-allowed;
            }
          `}</style>
        </div>
      );
    }

    return this.props.children;
  }
}

export default DiagramErrorBoundary;