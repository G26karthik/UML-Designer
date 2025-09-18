/**
 * Mock logger for test environment
 * Provides minimal logging functionality without Winston dependencies
 */

// Simple console-based logger for tests
const testLogger = {
  info: (message, meta = {}) => {
    if (process.env.LOG_LEVEL !== 'silent') {
      console.log(`[INFO] ${message}`, meta);
    }
  },
  warn: (message, meta = {}) => {
    if (process.env.LOG_LEVEL !== 'silent') {
      console.warn(`[WARN] ${message}`, meta);
    }
  },
  error: (message, meta = {}) => {
    console.error(`[ERROR] ${message}`, meta);
  },
  debug: (message, meta = {}) => {
    if (process.env.LOG_LEVEL === 'debug') {
      console.log(`[DEBUG] ${message}`, meta);
    }
  },
  http: (message, meta = {}) => {
    if (process.env.LOG_LEVEL === 'debug') {
      console.log(`[HTTP] ${message}`, meta);
    }
  }
};

// Mock middleware functions
export const requestLogger = (req, res, next) => {
  req.id = req.headers['x-request-id'] || `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  next();
};

export const performanceLogger = {
  start: (operation) => {
    const startTime = Date.now();
    return {
      end: (metadata = {}) => {
        const duration = Date.now() - startTime;
        testLogger.info(`Performance: ${operation}`, {
          operation,
          duration: `${duration}ms`,
          ...metadata
        });
        return duration;
      }
    };
  }
};

export const logBusinessEvent = (event, data = {}) => {
  testLogger.info(`Business Event: ${event}`, { event, ...data });
};

export const logSecurityEvent = (event, data = {}) => {
  testLogger.warn(`Security Event: ${event}`, { event, ...data });
};

export const logHealthCheck = (service, status, data = {}) => {
  const level = status === 'healthy' ? 'info' : 'warn';
  testLogger[level](`Health Check: ${service}`, { service, status, ...data });
};

export default testLogger;