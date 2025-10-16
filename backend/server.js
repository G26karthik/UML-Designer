/**
 * Production entry point for the backend server
 * Uses full Winston logging and monitoring capabilities
 */

import express from 'express';
import multer from 'multer';
import axios from 'axios';
import cors from 'cors';
import dotenv from 'dotenv';
import fs from 'fs/promises';
import fsSync from 'fs';
import path from 'path';
import crypto from 'crypto';
import FormData from 'form-data';
import compression from 'compression';
import { validateCorsOrigin, sanitizeFileName, validateGitHubUrl } from './utils/security.js';
import { 
  AppError, 
  errorHandler, 
  asyncHandler,
  createValidationError,
  createTimeoutError,
  createExternalServiceError,
  ErrorTypes
} from './utils/errorHandler.js';
import { createApiRouter } from './routes/api.js';

// Use full production modules
import logger, { requestLogger, performanceLogger, logBusinessEvent, logSecurityEvent, logHealthCheck } from './utils/logger.js';
import { metricsMiddleware, recordAnalysisMetrics, recordCacheMetrics, recordErrorMetrics, createMonitoringEndpoints, startPeriodicMetricsLogging } from './utils/monitoring.js';

dotenv.config();

const app = express();

// Middleware setup
app.use(compression());

// Metrics collection middleware (before request logging)
app.use(metricsMiddleware);

// Request logging middleware (before other middleware)
app.use(requestLogger);

app.use(express.json({ limit: process.env.JSON_LIMIT || '20mb' }));

// Enhanced CORS configuration with proper security
const allowedOrigins = (process.env.ALLOWED_ORIGINS || 'http://localhost:3000,http://localhost:3001,http://localhost:3002')
  .split(',')
  .map(s => s.trim())
  .filter(Boolean);

logger.info(`Allowed CORS origins: ${allowedOrigins.join(', ')}`);

app.use(cors({
  origin: (origin, callback) => {
    const isAllowed = validateCorsOrigin(origin, allowedOrigins);
    
    if (isAllowed) {
      callback(null, true);
    } else {
      logSecurityEvent('CORS_VIOLATION', {
        origin: origin || 'null',
        allowedOrigins,
        ip: 'unknown'
      });
      callback(new Error(`CORS policy violation: Origin ${origin || 'null'} not allowed`), false);
    }
  },
  credentials: process.env.CORS_CREDENTIALS === 'true',
  methods: ['GET', 'POST', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Correlation-ID']
}));

// Add monitoring endpoints
createMonitoringEndpoints(app);

// Mount API router (versioned); optionally mount legacy alias
const apiRouter = createApiRouter({ logger, httpClient: axios, isTest: process.env.NODE_ENV === 'test' });
app.use('/api/v1', apiRouter);
// Expose the router on the app for tests so they can call helpers like
// apiRouter.__setHttpClient to inject a mock client when needed.
app.locals.apiRouter = apiRouter;
// Back-compat mount for tests and legacy clients that expect /api/* routes
app.use('/api', apiRouter);
if (process.env.ENABLE_LEGACY_ROUTES === 'true') {
  app.use('/', apiRouter);
}

// Add a simple test endpoint
app.get('/test', (req, res) => {
  logger.info('Test endpoint accessed', { 
    requestId: req.id,
    timestamp: new Date().toISOString()
  });
  res.json({ 
    message: 'Production logging test successful!', 
    timestamp: new Date().toISOString(),
    requestId: req.id 
  });
});

// Add error handling middleware
app.use(errorHandler(logger));

const PORT = process.env.PORT || 3001;

// If running tests, do not start an actual HTTP server; export the app so
// supertest can use it directly. In non-test environments, start listening
// as normal.
let server;
if (process.env.NODE_ENV === 'test') {
  // Do not call app.listen in tests to avoid binding ports and to allow
  // supertest to use the app directly.
  logger.info('Server running in test mode: not starting HTTP listener');
} else {
  server = app.listen(PORT, () => {
    logger.info(`🚀 Production backend server started on port ${PORT}`, {
      port: PORT,
      environment: process.env.NODE_ENV || 'production',
      nodeVersion: process.version
    });

    // Start periodic metrics logging
    startPeriodicMetricsLogging();
  });
}

// Graceful shutdown handling
const gracefulShutdown = (signal) => {
  logger.info(`\n🛑 ${signal} received. Starting graceful shutdown...`);
  
  server.close(() => {
    logger.info('✅ HTTP server closed');
    process.exit(0);
  });

  // Force close after 10 seconds
  setTimeout(() => {
    logger.error('❌ Forced shutdown after timeout');
    process.exit(1);
  }, 10000);
};

process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
process.on('SIGINT', () => gracefulShutdown('SIGINT'));

// Export the app for tests (CommonJS and ESM consumers)
export default app;
if (typeof module !== 'undefined' && module.exports) {
  module.exports = app;
}