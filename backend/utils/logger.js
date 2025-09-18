/**
 * Production-ready logging configuration with Winston
 * Provides structured logging, log rotation, and environment-specific configurations
 */

import winston from 'winston';
import DailyRotateFile from 'winston-daily-rotate-file';
import path from 'path';
import { fileURLToPath } from 'url';

// Handle both ESM and CommonJS environments
let __dirname;
if (process.env.NODE_ENV === 'test') {
  // In test environment, use simple path
  __dirname = path.resolve('logs');
} else {
  try {
    const __filename = fileURLToPath(import.meta.url);
    __dirname = path.dirname(__filename);
  } catch (e) {
    // Fallback
    __dirname = path.resolve();
  }
}

// Log levels and colors
const logLevels = {
  error: 0,
  warn: 1,
  info: 2,
  http: 3,
  debug: 4
};

const logColors = {
  error: 'red',
  warn: 'yellow',
  info: 'green',
  http: 'magenta',
  debug: 'cyan'
};

winston.addColors(logColors);

// Custom log format
const logFormat = winston.format.combine(
  winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss.SSS' }),
  winston.format.errors({ stack: true }),
  winston.format.json(),
  winston.format.printf(({ timestamp, level, message, ...meta }) => {
    let logMessage = `${timestamp} [${level.toUpperCase()}]: ${message}`;
    
    // Add metadata if present
    if (Object.keys(meta).length > 0) {
      logMessage += ` ${JSON.stringify(meta, null, 2)}`;
    }
    
    return logMessage;
  })
);

// Console format for development
const consoleFormat = winston.format.combine(
  winston.format.colorize({ all: true }),
  winston.format.timestamp({ format: 'HH:mm:ss.SSS' }),
  winston.format.printf(({ timestamp, level, message, ...meta }) => {
    let logMessage = `${timestamp} [${level}]: ${message}`;
    
    // Add metadata if present (simplified for console)
    if (Object.keys(meta).length > 0) {
      logMessage += ` ${JSON.stringify(meta)}`;
    }
    
    return logMessage;
  })
);

// Create logs directory
const logsDir = path.join(__dirname, '..', 'logs');

// Transport configurations
const transports = [];

// Console transport
if (process.env.NODE_ENV !== 'production') {
  transports.push(
    new winston.transports.Console({
      level: process.env.LOG_LEVEL || 'debug',
      format: consoleFormat
    })
  );
}

// File transports for production and errors
if (process.env.NODE_ENV !== 'test') {
  // Daily rotating file for all logs
  transports.push(
    new DailyRotateFile({
      filename: path.join(logsDir, 'application-%DATE%.log'),
      datePattern: 'YYYY-MM-DD',
      zippedArchive: true,
      maxSize: '20m',
      maxFiles: '14d',
      level: 'info',
      format: logFormat
    })
  );

  // Separate file for errors
  transports.push(
    new DailyRotateFile({
      filename: path.join(logsDir, 'error-%DATE%.log'),
      datePattern: 'YYYY-MM-DD',
      zippedArchive: true,
      maxSize: '20m',
      maxFiles: '30d',
      level: 'error',
      format: logFormat
    })
  );

  // High-frequency access log for HTTP requests
  transports.push(
    new DailyRotateFile({
      filename: path.join(logsDir, 'access-%DATE%.log'),
      datePattern: 'YYYY-MM-DD',
      zippedArchive: true,
      maxSize: '50m',
      maxFiles: '7d',
      level: 'http',
      format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.json()
      )
    })
  );
}

// Create Winston logger instance
const logger = winston.createLogger({
  levels: logLevels,
  level: process.env.LOG_LEVEL || (process.env.NODE_ENV === 'production' ? 'info' : 'debug'),
  format: logFormat,
  transports,
  // Handle uncaught exceptions and rejections
  exceptionHandlers: process.env.NODE_ENV !== 'test' ? [
    new DailyRotateFile({
      filename: path.join(logsDir, 'exceptions-%DATE%.log'),
      datePattern: 'YYYY-MM-DD',
      zippedArchive: true,
      maxSize: '20m',
      maxFiles: '30d'
    })
  ] : [],
  rejectionHandlers: process.env.NODE_ENV !== 'test' ? [
    new DailyRotateFile({
      filename: path.join(logsDir, 'rejections-%DATE%.log'),
      datePattern: 'YYYY-MM-DD',
      zippedArchive: true,
      maxSize: '20m',
      maxFiles: '30d'
    })
  ] : [],
  exitOnError: false
});

// Request logging middleware
export const requestLogger = (req, res, next) => {
  const start = Date.now();
  const originalSend = res.send;
  
  // Generate request ID
  req.id = req.headers['x-request-id'] || `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  
  // Override res.send to capture response data
  res.send = function(data) {
    const duration = Date.now() - start;
    
    // Log HTTP request
    logger.http('HTTP Request', {
      requestId: req.id,
      method: req.method,
      url: req.originalUrl,
      status: res.statusCode,
      duration: `${duration}ms`,
      ip: req.ip,
      userAgent: req.get('User-Agent'),
      contentLength: res.get('Content-Length'),
      contentType: res.get('Content-Type')
    });
    
    originalSend.call(this, data);
  };
  
  next();
};

// Performance monitoring helper
export const performanceLogger = {
  start: (operation) => {
    const startTime = process.hrtime.bigint();
    return {
      end: (metadata = {}) => {
        const endTime = process.hrtime.bigint();
        const duration = Number(endTime - startTime) / 1000000; // Convert to milliseconds
        
        logger.info(`Performance: ${operation}`, {
          operation,
          duration: `${duration.toFixed(2)}ms`,
          ...metadata
        });
        
        return duration;
      }
    };
  }
};

// Error context logger
export const logError = (error, context = {}) => {
  const errorData = {
    message: error.message,
    stack: error.stack,
    name: error.name,
    code: error.code,
    type: error.type,
    statusCode: error.statusCode,
    ...context
  };
  
  logger.error('Application Error', errorData);
};

// Business logic logger with context
export const logBusinessEvent = (event, data = {}) => {
  logger.info(`Business Event: ${event}`, {
    event,
    timestamp: new Date().toISOString(),
    ...data
  });
};

// Security event logger
export const logSecurityEvent = (event, data = {}) => {
  logger.warn(`Security Event: ${event}`, {
    event,
    timestamp: new Date().toISOString(),
    severity: 'security',
    ...data
  });
};

// Health check logger
export const logHealthCheck = (service, status, data = {}) => {
  const level = status === 'healthy' ? 'info' : 'warn';
  logger[level](`Health Check: ${service}`, {
    service,
    status,
    timestamp: new Date().toISOString(),
    ...data
  });
};

export default logger;