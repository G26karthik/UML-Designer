/**
 * Dev/Test entry for UML Designer Backend (ESM)
 * Mounts shared API router at root for unversioned endpoints used by tests.
 */


import express from 'express';
import axios from 'axios';
import cors from 'cors';
import dotenv from 'dotenv';
import compression from 'compression';
import { validateCorsOrigin } from './utils/security.js';
import pino from 'pino';
import pinoHttp from 'express-pino-logger';
import { errorHandler } from './utils/errorHandler.js';
import { createApiRouter } from './routes/api.js';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

dotenv.config();


const isTest = process.env.NODE_ENV === 'test';
// For ES modules, we need to construct __dirname differently, but only when not in test
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const logDir = join(__dirname, 'logs');
const logger = pino({
  level: process.env.LOG_LEVEL || (isTest ? 'warn' : 'info'),
  transport: !isTest ? {
    target: 'pino/file',
    options: { destination: `${logDir}/backend.log`, mkdir: true }
  } : undefined
});


const app = express();
app.use(compression());
app.use(pinoHttp({ logger }));
app.use(express.json({ limit: process.env.JSON_LIMIT || '20mb' }));

const allowedOrigins = (process.env.ALLOWED_ORIGINS || 'http://localhost:3000,http://localhost:3001')
  .split(',')
  .map(s => s.trim())
  .filter(Boolean);

app.use(cors({
  origin: (origin, callback) => {
    if (!origin || isTest) return callback(null, true);
    const isAllowed = validateCorsOrigin(origin, allowedOrigins);
    return isAllowed ? callback(null, true) : callback(new Error(`CORS policy violation: ${origin}`), false);
  },
  credentials: process.env.CORS_CREDENTIALS === 'true',
  methods: ['GET', 'POST', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));


// Shared API router mounted unversioned for tests/dev
const apiRouter = createApiRouter({ logger, httpClient: axios, isTest });
app.use('/', apiRouter);

// Expose __setHttpClient for tests
export const __setHttpClient = client => { apiRouter.__setHttpClient(client); };

// Error handler last
app.use(errorHandler(logger));

// Export a function that returns the app for testing
export default () => app;

// Allow running directly (manual dev run)
if (!isTest && process.argv[1] && process.argv[1].toLowerCase().endsWith('index.js')) {
  const port = process.env.PORT || 3001;
  app.listen(port, () => logger.info(`Backend server listening on ${port}`));
}
 

