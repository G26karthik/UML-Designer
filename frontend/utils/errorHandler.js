/**
 * Frontend Error Handling Utilities
 * Provides consistent error handling and user feedback
 */

/**
 * Standard error types for frontend categorization
 */
export const ErrorTypes = {
  NETWORK: 'NETWORK',
  VALIDATION: 'VALIDATION', 
  TIMEOUT: 'TIMEOUT',
  SERVER: 'SERVER',
  CLIENT: 'CLIENT',
  UNKNOWN: 'UNKNOWN'
};

/**
 * Application Error class for frontend
 */
export class AppError extends Error {
  constructor(message, type = ErrorTypes.UNKNOWN, details = null, cause = null) {
    super(message);
    this.name = 'AppError';
    this.type = type;
    this.details = details;
    this.cause = cause;
    this.timestamp = new Date().toISOString();
    this.isRetryable = ['NETWORK', 'TIMEOUT', 'SERVER'].includes(type);
  }
}

/**
 * Categorizes errors based on their characteristics
 */
export const categorizeError = (error) => {
  // Network-related errors
  if (error.name === 'AbortError' || error.message?.includes('aborted')) {
    return new AppError('Request was cancelled', ErrorTypes.TIMEOUT, null, error);
  }
  
  if (error.name === 'TimeoutError' || error.code === 'ECONNABORTED') {
    return new AppError('Request timed out', ErrorTypes.TIMEOUT, null, error);
  }
  
  if (error.name === 'TypeError' && error.message?.includes('fetch')) {
    return new AppError('Network connection failed', ErrorTypes.NETWORK, null, error);
  }
  
  // HTTP errors
  if (error.status) {
    if (error.status >= 400 && error.status < 500) {
      const type = error.status === 400 ? ErrorTypes.VALIDATION : ErrorTypes.CLIENT;
      return new AppError(error.message || `Client error (${error.status})`, type, { status: error.status }, error);
    }
    
    if (error.status >= 500) {
      return new AppError(error.message || 'Server error occurred', ErrorTypes.SERVER, { status: error.status }, error);
    }
  }
  
  // Validation errors
  if (error.message?.toLowerCase().includes('invalid') || 
      error.message?.toLowerCase().includes('validation')) {
    return new AppError(error.message, ErrorTypes.VALIDATION, null, error);
  }
  
  // Default categorization
  return new AppError(error.message || 'An unexpected error occurred', ErrorTypes.UNKNOWN, null, error);
};

/**
 * Creates user-friendly error messages
 */
export const createUserMessage = (error) => {
  const appError = error instanceof AppError ? error : categorizeError(error);
  
  switch (appError.type) {
    case ErrorTypes.NETWORK:
      return {
        title: 'Connection Problem',
        message: 'Please check your internet connection and try again.',
        action: 'Retry'
      };
      
    case ErrorTypes.TIMEOUT:
      return {
        title: 'Request Timed Out',
        message: 'The analysis is taking longer than expected. Large repositories may require more time.',
        action: 'Try Again'
      };
      
    case ErrorTypes.VALIDATION:
      return {
        title: 'Invalid Input', 
        message: appError.message,
        action: 'Fix Input'
      };
      
    case ErrorTypes.SERVER:
      return {
        title: 'Server Error',
        message: 'The analysis service is experiencing issues. Please try again later.',
        action: 'Retry Later'
      };
      
    case ErrorTypes.CLIENT:
      return {
        title: 'Request Error',
        message: appError.message || 'There was a problem with your request.',
        action: 'Check Input'
      };
      
    default:
      return {
        title: 'Unexpected Error',
        message: appError.message || 'Something went wrong. Please try again.',
        action: 'Try Again'
      };
  }
};

/**
 * Enhanced error handler with retry logic and user feedback
 */
export class ErrorHandler {
  constructor(setError, setLoading) {
    this.setError = setError;
    this.setLoading = setLoading;
    this.retryAttempts = new Map();
    this.maxRetries = 3;
  }
  
  /**
   * Handles errors with automatic retry for retryable errors
   */
  async handleError(error, operation, retryFn = null) {
    console.error('Operation failed:', error);
    
    const appError = categorizeError(error);
    const operationKey = operation || 'default';
    const attempts = this.retryAttempts.get(operationKey) || 0;
    
    // Auto-retry for retryable errors
    if (appError.isRetryable && attempts < this.maxRetries && retryFn) {
      this.retryAttempts.set(operationKey, attempts + 1);
      
      // Exponential backoff: 1s, 2s, 4s
      const delay = Math.pow(2, attempts) * 1000;
      
      if (process.env.NODE_ENV === 'development') {
        console.log(`Retrying operation ${operationKey} (attempt ${attempts + 1}/${this.maxRetries}) after ${delay}ms`);
      }
      
      setTimeout(async () => {
        try {
          await retryFn();
          this.retryAttempts.delete(operationKey); // Reset on success
        } catch (retryError) {
          await this.handleError(retryError, operation, retryFn);
        }
      }, delay);
      
      return;
    }
    
    // Reset retry counter after max attempts or non-retryable error
    this.retryAttempts.delete(operationKey);
    
    // Create user-friendly message
    const userMessage = createUserMessage(appError);
    const displayMessage = `${userMessage.title}: ${userMessage.message}`;
    
    // Update UI state
    if (this.setLoading) this.setLoading(false);
    if (this.setError) this.setError(displayMessage);
    
    return appError;
  }
  
  /**
   * Clears any existing errors
   */
  clearError() {
    if (this.setError) this.setError('');
  }
  
  /**
   * Manual retry with reset
   */
  retry(operation) {
    this.retryAttempts.delete(operation);
    this.clearError();
  }
}

/**
 * Hook for using error handler in React components
 */
export const useErrorHandler = (setError, setLoading) => {
  return new ErrorHandler(setError, setLoading);
};

/**
 * Global error boundary error handler
 */
export const handleGlobalError = (error, errorInfo) => {
  console.error('Global error caught:', error, errorInfo);
  
  // Log to external service in production
  if (process.env.NODE_ENV === 'production') {
    // Send to monitoring service
    try {
      // Example: Sentry, LogRocket, etc.
      if (process.env.NODE_ENV === 'development') {
        console.log('Would send to monitoring service:', {
          error: error.toString(),
          stack: error.stack,
          componentStack: errorInfo?.componentStack,
          timestamp: new Date().toISOString()
        });
      }
    } catch (loggingError) {
      if (process.env.NODE_ENV === 'development') {
        console.error('Failed to log error:', loggingError);
      }
    }
  }
};

/**
 * Validates API responses and throws appropriate errors
 */
export const validateApiResponse = (response, data) => {
  if (!response.ok) {
    const errorMessage = data?.error?.message || data?.error || `HTTP ${response.status}`;
    const error = new Error(errorMessage);
    error.status = response.status;
    throw error;
  }
  
  if (data?.success === false) {
    const error = new Error(data.error?.message || 'API returned error');
    error.status = response.status;
    throw error;
  }
  
  return data;
};