/**
 * Standardized Error Handling Utility
 * Provides consistent error responses across the backend service
 */

/**
 * Standard error types for better categorization
 */
export const ErrorTypes = {
  VALIDATION: 'VALIDATION',
  AUTHENTICATION: 'AUTHENTICATION', 
  AUTHORIZATION: 'AUTHORIZATION',
  NOT_FOUND: 'NOT_FOUND',
  RATE_LIMIT: 'RATE_LIMIT',
  EXTERNAL_SERVICE: 'EXTERNAL_SERVICE',
  INTERNAL: 'INTERNAL',
  TIMEOUT: 'TIMEOUT',
  PAYLOAD_TOO_LARGE: 'PAYLOAD_TOO_LARGE'
};

/**
 * Standard error codes mapping to HTTP status codes
 */
const ErrorCodes = {
  [ErrorTypes.VALIDATION]: 400,
  [ErrorTypes.AUTHENTICATION]: 401,
  [ErrorTypes.AUTHORIZATION]: 403,
  [ErrorTypes.NOT_FOUND]: 404,
  [ErrorTypes.RATE_LIMIT]: 429,
  [ErrorTypes.EXTERNAL_SERVICE]: 502,
  [ErrorTypes.INTERNAL]: 500,
  [ErrorTypes.TIMEOUT]: 408,
  [ErrorTypes.PAYLOAD_TOO_LARGE]: 413
};

/**
 * Application Error class for consistent error handling
 */
export class AppError extends Error {
  constructor(message, type = ErrorTypes.INTERNAL, details = null, cause = null) {
    super(message);
    this.name = 'AppError';
    this.type = type;
    this.statusCode = ErrorCodes[type] || 500;
    this.details = details;
    this.cause = cause;
    this.timestamp = new Date().toISOString();
    this.isOperational = true; // Marks this as an expected error vs programming error
    
    // Capture stack trace
    Error.captureStackTrace(this, AppError);
  }
}

/**
 * Creates standardized error response format
 */
export const createErrorResponse = (error, requestId = null) => {
  const response = {
    success: false,
    error: {
      message: error.message || 'An unexpected error occurred',
      type: error.type || ErrorTypes.INTERNAL,
      timestamp: error.timestamp || new Date().toISOString(),
      ...(error.details && { details: error.details }),
      ...(requestId && { requestId })
    }
  };
  
  // Don't expose internal error details in production
  if (process.env.NODE_ENV === 'production' && error.type === ErrorTypes.INTERNAL) {
    response.error.message = 'Internal server error';
    delete response.error.details;
  }
  
  return response;
};

/**
 * Express error handling middleware
 */
export const errorHandler = (logger) => (err, req, res, next) => {
  let error = err;
  
  // Convert non-AppError errors to AppError
  if (!(err instanceof AppError)) {
    // Handle specific known error types
    if (err.code === 'ENOTFOUND' || err.code === 'ECONNREFUSED') {
      error = new AppError('External service unavailable', ErrorTypes.EXTERNAL_SERVICE, null, err);
    } else if (err.code === 'ETIMEDOUT' || err.type === 'timeout') {
      error = new AppError('Request timeout', ErrorTypes.TIMEOUT, null, err);
    } else if (err.type === 'entity.too.large') {
      error = new AppError('Request payload too large', ErrorTypes.PAYLOAD_TOO_LARGE, null, err);
    } else if (err.type === 'entity.parse.failed' || err instanceof SyntaxError || /Unexpected token/.test(err.message || '')) {
      // JSON parse errors from body-parser should be treated as validation failures
      error = new AppError('Invalid JSON payload', ErrorTypes.VALIDATION, null, err);
    } else {
      error = new AppError(err.message || 'Internal server error', ErrorTypes.INTERNAL, null, err);
    }
  }
  
  // Log error details
  const logLevel = error.statusCode >= 500 ? 'error' : 'warn';
  logger[logLevel](`${error.type} (${error.statusCode}): ${error.message}`, {
    error: {
      name: error.name,
      type: error.type,
      statusCode: error.statusCode,
      stack: error.stack,
      cause: error.cause?.message,
      details: error.details
    },
    request: {
      method: req.method,
      url: req.url,
      ip: req.ip,
      userAgent: req.get('User-Agent')
    }
  });
  
  // Send standardized error response
  const requestId = req.id || req.headers['x-request-id'];
  const errorResponse = createErrorResponse(error, requestId);
  
  // For validation errors (tests expect a simple string in .body.error), provide compatibility
  if (error.type === ErrorTypes.VALIDATION || error.type === ErrorTypes.PAYLOAD_TOO_LARGE) {
    // Some legacy endpoints (file uploads under /analyze) expect a success:false envelope
    try {
      const p = req.path || req.originalUrl || '';
      if (typeof p === 'string' && p.startsWith('/analyze')) {
        return res.status(error.statusCode).json({ success: false, error: error.message });
      }
    } catch (e) {
      // ignore and fallthrough
    }
    // Default: return the simple string error for other endpoints (tests expect this)
    return res.status(error.statusCode).json({ error: error.message });
  }

  res.status(error.statusCode).json(errorResponse);
};

/**
 * Async wrapper to catch errors in async route handlers
 */
export const asyncHandler = (fn) => (req, res, next) => {
  Promise.resolve(fn(req, res, next)).catch(next);
};

/**
 * Common error creators for frequent scenarios
 */
export const createValidationError = (message, details = null) => 
  new AppError(message, ErrorTypes.VALIDATION, details);

export const createNotFoundError = (resource = 'Resource') => 
  new AppError(`${resource} not found`, ErrorTypes.NOT_FOUND);

export const createTimeoutError = (operation = 'Operation') => 
  new AppError(`${operation} timed out`, ErrorTypes.TIMEOUT);

export const createExternalServiceError = (service, originalError = null) => 
  new AppError(`${service} service unavailable`, ErrorTypes.EXTERNAL_SERVICE, null, originalError);