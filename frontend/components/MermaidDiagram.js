'use client';

import { useEffect, useRef, useId, useState, useCallback } from 'react';

/**
 * MermaidDiagram Component
 * @component
 * @description Renders Mermaid UML diagrams with error handling and performance optimizations.
 * @param {Object} props - Component props
 * @param {string} props.chart - Mermaid chart definition string
 * @param {function} props.onRender - Callback after successful render
 * @param {function} props.onError - Callback on render error
 * @param {number} [props.timeout=30000] - Render timeout in ms
 * @param {string} [props.className] - CSS class for container
 * @param {JSX.Element|null} [props.fallbackContent] - Fallback content on error
 * @returns {JSX.Element} React component
 */
export default function MermaidDiagram({ 
  chart, 
  onRender, 
  onError,
  timeout = 30000, // 30 second timeout
  className = '',
  fallbackContent = null
}) {
  const ref = useRef(null);
  const uid = useId().replace(/[:]/g, '_');
  const timeoutRef = useRef(null);
  const [isLoading, setIsLoading] = useState(false);
  const [renderAttempts, setRenderAttempts] = useState(0);
  const [svg, setSvg] = useState(null);
  const maxRetries = 3;

  // Cleanup function
  const cleanup = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    setIsLoading(false);
  }, []);

  // Enhanced error handling
  const handleError = useCallback((error, context = '') => {
    cleanup();
    
    const errorDetails = {
      message: error.message || 'Unknown error',
      stack: error.stack,
      context,
      chart: chart?.substring(0, 200) + (chart?.length > 200 ? '...' : ''), // Truncate for logging
      timestamp: new Date().toISOString(),
      attempts: renderAttempts + 1
    };

    if (process.env.NODE_ENV === 'development') {
      console.error('Mermaid render error:', errorDetails);
    }

    // Call external error handler
    if (onError) {
      onError(errorDetails);
    }

    // Show fallback content
    const errorMessage = getErrorMessage(error);
    setSvg(`
      <div style="
        color: #dc2626; 
        background-color: #fef2f2; 
        border: 2px dashed #fecaca; 
        border-radius: 8px; 
        padding: 1.5rem; 
        text-align: center;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      ">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">⚠️</div>
        <div style="font-weight: 600; margin-bottom: 0.5rem;">Diagram Rendering Failed</div>
        <div style="font-size: 0.875rem; color: #7f1d1d;">${errorMessage}</div>
        ${renderAttempts < maxRetries ? `
          <button onclick=\"window.location.reload()\" style=\"
            margin-top: 1rem;
            padding: 0.5rem 1rem;
            background-color: #dc2626;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.875rem;
          \">
            Retry Rendering
          </button>
        ` : ''}
      </div>
    `);

    // Notify parent component
    onRender?.(null, errorDetails);
  }, [chart, onError, onRender, renderAttempts, cleanup]);

  // Timeout handler
  const handleTimeout = useCallback(() => {
    const timeoutError = new Error(`Diagram rendering timed out after ${timeout}ms`);
    timeoutError.name = 'TimeoutError';
    handleError(timeoutError, 'timeout');
  }, [timeout, handleError]);

  // Validate chart syntax before rendering
  const validateChart = useCallback((chartData) => {
    if (!chartData || typeof chartData !== 'string') {
      throw new Error('Invalid chart data: must be a non-empty string');
    }

    if (chartData.length > 50000) {
      throw new Error('Chart data too large: exceeds 50KB limit');
    }

    // Basic syntax validation
    const trimmed = chartData.trim();
    if (!trimmed) {
      throw new Error('Empty chart data');
    }

    // Check for potential infinite loops or excessive complexity
    const lines = trimmed.split('\n').length;
    if (lines > 1000) {
      throw new Error('Chart too complex: exceeds 1000 lines');
    }

    return trimmed;
  }, []);


  // Main render function (not recreated every render)
  async function renderDiagram() {
    if (!chart || !ref.current) return;
    if (isLoading) return;
    try {
      setIsLoading(true);
      const validatedChart = validateChart(chart);
      timeoutRef.current = setTimeout(handleTimeout, timeout);
      let mermaid;
      try {
        const module = await import('mermaid');
        mermaid = module.default;
      } catch (importError) {
        throw new Error(`Failed to load Mermaid library: ${importError.message}`);
      }
      mermaid.initialize({ 
        startOnLoad: false,
        theme: 'default',
        securityLevel: 'strict',
        maxTextSize: 50000,
        maxEdges: 500,
        deterministicIds: true,
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
      });
      const renderResult = await mermaid.render(`mermaid_${uid}_${Date.now()}`, validatedChart);
      cleanup();
      if (!renderResult || !renderResult.svg) {
        throw new Error('Mermaid render returned invalid result');
      }
      setSvg(renderResult.svg);
      onRender?.(renderResult.svg);
      setRenderAttempts(0); // Reset on success
    } catch (error) {
      setRenderAttempts(prev => prev + 1);
      handleError(error, 'render');
    }
  }

  // Only re-render when chart changes
  useEffect(() => {
    renderDiagram();
    return cleanup;
  }, [chart]);

  // Cleanup on unmount
  useEffect(() => {
    return cleanup;
  }, [cleanup]);

  return (
    <div 
      ref={ref} 
      className={`mermaid-diagram ${className}`}
      data-testid="mermaid-diagram"
      style={{ 
        minHeight: isLoading ? '100px' : 'auto',
        position: 'relative'
      }}
    >
      {isLoading && (
        <div style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          color: '#6b7280',
          fontSize: '0.875rem'
        }}>
          Rendering diagram...
        </div>
      )}
      {!isLoading && svg && (
        <div dangerouslySetInnerHTML={{ __html: svg }} />
      )}
      {!isLoading && !svg && fallbackContent}
    </div>
  );
}

/**
 * Generate user-friendly error messages based on error type
 */
function getErrorMessage(error) {
  if (!error) return 'An unknown error occurred while rendering the diagram.';

  const errorMessage = error.message || error.toString();
  
  // Categorize common errors
  if (error.name === 'TimeoutError') {
    return 'Diagram rendering timed out. The diagram may be too complex.';
  }
  
  if (errorMessage.includes('Parse error') || errorMessage.includes('syntax error')) {
    return 'Invalid diagram syntax. Please check your code structure.';
  }
  
  if (errorMessage.includes('Maximum call stack') || errorMessage.includes('recursion')) {
    return 'Diagram is too complex or contains circular references.';
  }
  
  if (errorMessage.includes('module') || errorMessage.includes('import') || errorMessage.includes('load')) {
    return 'Failed to load diagram rendering library. Please refresh the page.';
  }
  
  if (errorMessage.includes('too large') || errorMessage.includes('exceeds')) {
    return 'Diagram is too large or complex to render.';
  }

  if (errorMessage.includes('network') || errorMessage.includes('fetch')) {
    return 'Network error while loading diagram resources. Please check your connection.';
  }

  return `Rendering error: ${errorMessage}`;
}
