/**
 * Frontend Logger Utility
 * Provides structured logging for frontend application
 * Replaces console.log/error statements with proper logging
 */

class Logger {
  constructor() {
    this.isDevelopment = process.env.NODE_ENV !== 'production';
    this.enableConsole = this.isDevelopment || process.env.NEXT_PUBLIC_ENABLE_DEBUG === 'true';
  }

  /**
   * Format log message with timestamp and metadata
   */
  _formatMessage(level, message, meta = {}) {
    return {
      timestamp: new Date().toISOString(),
      level,
      message,
      ...meta,
      userAgent: typeof window !== 'undefined' ? window.navigator.userAgent : 'unknown',
      url: typeof window !== 'undefined' ? window.location.href : 'unknown'
    };
  }

  /**
   * Send log to monitoring service (placeholder for future implementation)
   */
  _sendToMonitoring(logData) {
    // TODO: Implement monitoring service integration
    // Example: Send to Datadog, Sentry, LogRocket, etc.
    if (typeof window !== 'undefined' && window.DD_LOGS) {
      window.DD_LOGS.logger.log(logData.message, logData);
    }
  }

  /**
   * Log info message
   */
  info(message, meta = {}) {
    const logData = this._formatMessage('info', message, meta);
    
    if (this.enableConsole) {
      console.log(`[INFO] ${message}`, meta);
    }
    
    // Send to monitoring in production
    if (!this.isDevelopment) {
      this._sendToMonitoring(logData);
    }
  }

  /**
   * Log warning message
   */
  warn(message, meta = {}) {
    const logData = this._formatMessage('warn', message, meta);
    
    if (this.enableConsole) {
      console.warn(`[WARN] ${message}`, meta);
    }
    
    this._sendToMonitoring(logData);
  }

  /**
   * Log error message
   */
  error(message, meta = {}) {
    const logData = this._formatMessage('error', message, meta);
    
    // Always show errors in console
    console.error(`[ERROR] ${message}`, meta);
    
    // Send to error tracking service
    this._sendToMonitoring(logData);
    
    // Send to error tracking service (e.g., Sentry)
    if (typeof window !== 'undefined' && window.Sentry) {
      window.Sentry.captureException(new Error(message), {
        extra: meta
      });
    }
  }

  /**
   * Log debug message (only in development)
   */
  debug(message, meta = {}) {
    if (this.isDevelopment) {
      const logData = this._formatMessage('debug', message, meta);
      console.debug(`[DEBUG] ${message}`, meta);
    }
  }

  /**
   * Log performance metric
   */
  performance(operation, duration, meta = {}) {
    const logData = this._formatMessage('performance', `${operation} took ${duration}ms`, {
      operation,
      duration,
      ...meta
    });
    
    if (this.enableConsole) {
      console.log(`[PERF] ${operation}: ${duration}ms`, meta);
    }
    
    this._sendToMonitoring(logData);
  }

  /**
   * Log user action for analytics
   */
  analytics(action, meta = {}) {
    const logData = this._formatMessage('analytics', action, meta);
    
    if (this.enableConsole) {
      console.log(`[ANALYTICS] ${action}`, meta);
    }
    
    // Send to analytics service (Google Analytics, Mixpanel, etc.)
    if (typeof window !== 'undefined' && window.gtag) {
      window.gtag('event', action, meta);
    }
  }

  /**
   * Log API call
   */
  api(method, url, status, duration, meta = {}) {
    const logData = this._formatMessage('api', `${method} ${url} ${status}`, {
      method,
      url,
      status,
      duration,
      ...meta
    });
    
    if (this.enableConsole) {
      const emoji = status >= 200 && status < 300 ? '✅' : '❌';
      console.log(`[API] ${emoji} ${method} ${url} - ${status} (${duration}ms)`, meta);
    }
    
    this._sendToMonitoring(logData);
  }
}

// Create singleton instance
const logger = new Logger();

export default logger;
