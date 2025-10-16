import express from 'express';
import multer from 'multer';
import axios from 'axios';
import fs from 'fs/promises';
import fsSync from 'fs';
import path from 'path';
import crypto from 'crypto';
import FormData from 'form-data';
import compression from 'compression';
import rateLimit from 'express-rate-limit';

import { validateUmlSchema } from '../utils/schemaValidator.js';
import {
  errorHandler,
  asyncHandler,
  createValidationError,
  createTimeoutError,
  createExternalServiceError,
  AppError,
  ErrorTypes,
} from '../utils/errorHandler.js';
import { ensurePythonParserAvailable } from '../utils/pythonServiceManager.js';
import {
  validateGitHubUrl,
  sanitizeFileName,
  isPathInside,
  hasZipMagicBytes,
  isZipFilename,
  isAllowedZipMime,
} from '../utils/security.js';

const keyHash = s => crypto.createHash('sha1').update(s).digest('hex');
const cacheKey = (url, commit) => (commit ? `${url}@${commit}` : url);

export function createApiRouter(options = {}) {
  const env = process.env.NODE_ENV || 'development';
  const defaultAutoStartPython = env !== 'production' && env !== 'test';

  const {
    logger = console,
    httpClient = axios,
    pythonUrl = process.env.PYTHON_PARSER_URL || 'http://localhost:5000',
    diskDir = process.env.DISK_CACHE_DIR || path.join(process.cwd(), 'cache'),
    cacheTtlMs = Number(process.env.CACHE_TTL_MS || 5 * 60 * 1000),
    diskTtlMs = Number(process.env.DISK_CACHE_TTL_MS || 24 * 60 * 60 * 1000),
    maxEntries = Number(process.env.MAX_CACHE_ENTRIES || 200),
    isTest = process.env.NODE_ENV === 'test',
    adminToken = process.env.ADMIN_TOKEN || null,
    rateWindowMs = Number(process.env.RATE_WINDOW_MS || 5 * 60 * 1000),
    rateMax = Number(process.env.RATE_MAX || 60),
    packageVersion = process.env.npm_package_version || '0.0.0',
  } = options;

  const autoStartPython = options.autoStartPython ?? defaultAutoStartPython;

  const router = express.Router();
  router.use(compression());
  router.use(express.json({ limit: process.env.JSON_LIMIT || '20mb' }));

  // Rate limit for analyze (skip in tests)
  if (!isTest) {
    const analyzeLimiter = rateLimit({ windowMs: rateWindowMs, max: rateMax, standardHeaders: true, legacyHeaders: false });
    router.use('/analyze', analyzeLimiter);
  }

  // Ensure upload directory exists and is absolute
  const uploadDir = path.isAbsolute(process.env.UPLOAD_DIR || '')
    ? process.env.UPLOAD_DIR
    : path.join(process.cwd(), process.env.UPLOAD_DIR || 'uploads');
  fs.mkdir(uploadDir, { recursive: true }).catch(() => {});

  const upload = multer({
    dest: uploadDir,
    limits: { fileSize: Number(process.env.UPLOAD_LIMIT_BYTES || 50 * 1024 * 1024) },
    fileFilter: (req, file, cb) => {
      if (!isZipFilename(file.originalname)) return cb(new AppError('Only .zip files are allowed', ErrorTypes.VALIDATION));
      if (!isAllowedZipMime(file.mimetype)) return cb(new AppError(`Invalid file type: ${file.mimetype}`, ErrorTypes.VALIDATION));
      cb(null, true);
    }
  });

  // Caching (memory + disk)
  const memCache = new Map();
  fs.mkdir(diskDir, { recursive: true }).catch(() => {});
  let lastPurge = null;

  const ensureCapacity = () => {
    while (memCache.size > maxEntries) {
      const first = memCache.keys().next().value;
      if (!first) break;
      memCache.delete(first);
    }
  };

  const readDisk = async key => {
    try {
      const file = path.join(diskDir, `${keyHash(key)}.json`);
      const stat = await fs.stat(file);
      if (Date.now() - stat.mtimeMs > diskTtlMs) {
        await fs.unlink(file).catch(() => {});
        return null;
      }
      return JSON.parse(await fs.readFile(file, 'utf8'));
    } catch {
      return null;
    }
  };

        // POST /uml-from-prompt (body: { prompt, diagramType?, format?, context?, stylePreferences?, focus? })
        router.post('/uml-from-prompt', asyncHandler(async (req, res) => {
          const timeout = Number(process.env.ANALYZE_TIMEOUT_MS || 120_000);
          const {
            prompt,
            diagramType = 'class',
            format = 'plantuml',
            context,
            stylePreferences,
            focus,
          } = req.body || {};

          if (!prompt || typeof prompt !== 'string' || !prompt.trim()) {
            throw createValidationError('Prompt is required and must be a non-empty string');
          }

          const validFormats = ['plantuml', 'mermaid'];
          const normalizedFormat = typeof format === 'string' ? format.toLowerCase() : 'plantuml';
          if (!validFormats.includes(normalizedFormat)) {
            throw createValidationError(`Invalid format: ${format}. Must be one of: ${validFormats.join(', ')}`);
          }

          // Format-specific diagram type validation
          const plantUMLTypes = ['class', 'sequence', 'usecase', 'state', 'activity', 'component', 'communication', 'deployment'];
          const mermaidTypes = ['class', 'sequence', 'usecase', 'state', 'activity', 'entity', 'gantt', 'component', 'communication', 'deployment'];
          const validTypes = normalizedFormat === 'mermaid' ? mermaidTypes : plantUMLTypes;
          
          const normalizedType = typeof diagramType === 'string' ? diagramType.toLowerCase() : '';
          if (!validTypes.includes(normalizedType)) {
            throw createValidationError(`Invalid diagramType '${diagramType}' for format '${normalizedFormat}'. Must be one of: ${validTypes.join(', ')}`);
          }

          const payload = {
            prompt,
            diagramType: normalizedType,
            format: normalizedFormat,
          };
          if (context && typeof context === 'object') payload.context = context;
          if (stylePreferences && typeof stylePreferences === 'object') payload.stylePreferences = stylePreferences;
          if (Array.isArray(focus)) payload.focus = focus;
          if (typeof focus === 'string' && focus.trim()) payload.focus = focus;

          try {
            const response = await http.post(`${pythonUrl}/uml-from-prompt`, payload, { timeout });
            return res.status(response.status || 200).json(response.data ?? {});
          } catch (err) {
            if (err?.code === 'ECONNABORTED' || err?.code === 'ETIMEDOUT') throw createTimeoutError('Prompt analysis');
            if (err?.response) {
              const { status, data } = err.response;
              if (status >= 400 && status < 500) throw createValidationError(data?.error || `Prompt analysis failed: ${status}`);
            }
            throw createExternalServiceError('Python parser', err);
          }
        }));
  const writeDisk = async (key, data) => {
    try {
      const file = path.join(diskDir, `${keyHash(key)}.json`);
      await fs.writeFile(file, JSON.stringify(data));
    } catch (e) {
      logger.warn?.(`Disk cache write failed: ${e.message}`);
    }
  };

  // Swappable HTTP client for tests
  // In test mode, prefer a minimal Node http(s) client so test HTTP
  // mocking libraries (nock) reliably intercept requests and we avoid
  // adapter/fetch-related interception issues.
  let http = httpClient;
  if (isTest && httpClient === axios) {
    // lightweight node http client
    const nodeHttpClient = {
      post: (urlStr, body, opts = {}) => new Promise((resolve, reject) => {
        try {
          const u = new URL(urlStr);
          const isSecure = u.protocol === 'https:';
          const lib = isSecure ? awaitImport('https') : awaitImport('http');
          const data = typeof body === 'string' ? body : JSON.stringify(body || {});
          const headers = { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data), ...(opts.headers || {}) };
          const reqOpts = { method: 'POST', hostname: u.hostname, port: u.port || (isSecure ? 443 : 80), path: u.pathname + (u.search || ''), headers };
          const req = lib.request(reqOpts, (res) => {
            const chunks = [];
            res.on('data', (c) => chunks.push(c));
            res.on('end', () => {
              const raw = Buffer.concat(chunks).toString('utf8');
              let parsed = raw;
              try { parsed = raw ? JSON.parse(raw) : {}; } catch (e) { /* keep raw */ }
              resolve({ status: res.statusCode, data: parsed });
            });
          });
          req.on('error', (e) => reject(e));
          if (opts.timeout) req.setTimeout(opts.timeout, () => { req.destroy(new Error('timeout')); });
          req.write(data);
          req.end();
        } catch (e) {
          reject(e);
        }
      }),
    };
    // Helper to dynamic import http/https in ESM-safe way
    function awaitImport(name) {
      // Dynamic require shim: use synchronous require via module.createRequire
      // to avoid top-level await/import complexity.
      try {
        // eslint-disable-next-line global-require, import/no-dynamic-require
        return require(name);
      } catch (e) {
        // fallback to dynamic import (shouldn't be necessary in Node)
        return import(name);
      }
    }
    http = nodeHttpClient;
  }
  router.__setHttpClient = client => { http = client || axios; };
  router.__purgeMemoryCache = () => { memCache.clear(); lastPurge = new Date().toISOString(); };

  // Reject non-POSTs to /generate-plantuml with 405 (method not allowed)
  router.all('/generate-plantuml', (req, res, next) => {
    if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });
    return next();
  });

  // POST /generate-plantuml (body: { schema, diagram_type, language_filter?, config? })
  router.post('/generate-plantuml', asyncHandler(async (req, res) => {
    const timeout = Number(process.env.GENERATE_TIMEOUT_MS || 4000);
    const { schema, diagram_type, language_filter, config } = req.body || {};

    if (!schema) throw createValidationError('schema is required');
    if (!diagram_type) throw createValidationError('diagram_type is required');
    const validTypes = ['class', 'sequence', 'usecase', 'state', 'activity', 'component', 'communication', 'deployment'];
    if (!validTypes.includes(diagram_type)) {
      throw createValidationError(`Invalid diagram_type: ${diagram_type}. Must be one of: ${validTypes.join(', ')}`);
    }

    try {
      if (!isTest) {
        try {
          await ensurePythonParserAvailable({
            pythonUrl,
            logger,
            timeoutMs: Math.min(timeout, 750),
            allowAutoStart: autoStartPython,
            autoStartTimeoutMs: Math.max(timeout, 5000),
          });
        } catch (preErr) {
          throw createExternalServiceError('Python parser', preErr);
        }
      }
      // Instrument outbound request for debugging when running tests or
      // when DEBUG_OUTBOUND=1 is set in the environment. This logs the
      // exact URL, payload and options so we can confirm nock/msw will
      // match the request during tests.
      const outboundPayload = { schema, diagram_type, language_filter, config };
      const outboundOptions = { timeout };
      const debugRequests = isTest || process.env.DEBUG_OUTBOUND === '1';
      if (debugRequests) {
        const out = { pythonUrl, url: `${pythonUrl}/generate-plantuml`, payload: outboundPayload, options: outboundOptions };
        (logger.debug || logger.log || console.log)('OUTBOUND_REQUEST', out);
      }

      const response = await http.post(
        `${pythonUrl}/generate-plantuml`,
        outboundPayload,
        outboundOptions
      );
      return res.status(response.status || 200).json(response.data ?? {});
    } catch (err) {
      // Debug outbound errors to help test/mocking diagnosis
      if (isTest || process.env.DEBUG_OUTBOUND === '1') {
        try {
          const outErr = {
            message: err?.message,
            code: err?.code,
            responseStatus: err?.response?.status,
            responseDataType: typeof err?.response?.data,
            configUrl: err?.config?.url,
          };
          (logger.debug || logger.error || console.error)('OUTBOUND_ERROR', outErr);
        } catch (e) {
          // swallow any debug logging failures
        }
      }
      if (err?.code === 'ECONNABORTED' || err?.code === 'ETIMEDOUT') {
        throw createExternalServiceError('Python parser', err);
      }
      if (err?.response) {
        const { status, data } = err.response;
        if (status >= 400 && status < 500) throw createValidationError(data?.error || `PlantUML generation failed: ${status}`);
        if (status >= 500) throw new AppError('Python parser error', ErrorTypes.INTERNAL, null, err);
      }
      throw createExternalServiceError('Python parser', err);
    }
  }));

  // POST /analyze (body: { githubUrl } or upload field repoZip)
  router.post('/analyze', upload.single('repoZip'), asyncHandler(async (req, res) => {
    const timeout = Number(process.env.ANALYZE_TIMEOUT_MS || 120_000);
    const { githubUrl } = req.body || {};

    if (githubUrl) {
      const v = validateGitHubUrl(githubUrl);
      if (!v.isValid) throw createValidationError(v.error);

      const k = cacheKey(v.url);
      const cached = memCache.get(k);
      if (cached && Date.now() - cached.ts < cacheTtlMs) {
        return res.status(200).json(cached.data);
      }

      const disk = await readDisk(k);
      if (disk) {
        memCache.set(k, { data: disk, ts: Date.now() });
        ensureCapacity();
        return res.status(200).json(disk);
      }

      try {

        const response = await http.post(`${pythonUrl}/analyze`, { githubUrl: v.url }, { timeout });
        const data = response?.data ?? {};

        // Log the actual schema and meta for debugging
        logger.info('PYTHON PARSER RAW RESPONSE', {
          dataKeys: Object.keys(data),
          meta: data?.schema?.meta,
          schemaKeys: data?.schema ? Object.keys(data.schema) : undefined
        });

        // Patch: Inject default meta if missing or invalid
        if (data && data.schema && (!data.schema.meta || typeof data.schema.meta !== 'object')) {
          data.schema.meta = {
            classes_found: 0,
            files_scanned: 0,
            languages: [],
            system: 'UnknownSystem'
          };
        }

        // Validate schema structure
        const validation = validateUmlSchema(data);
        if (!validation.isValid) {
          logger.warn('Invalid schema received from Python parser', {
            errors: validation.errors,
            url: v.url,
            dataKeys: Object.keys(data),
            meta: data?.schema?.meta,
            schemaKeys: data?.schema ? Object.keys(data.schema) : undefined
          });
          throw createValidationError(`Invalid schema structure: ${validation.errors.join(', ')}`);
        }

        const commit = data?.meta?.commit;
        const urlKey = cacheKey(v.url);
        const commitKey = commit ? cacheKey(v.url, commit) : null;

        // Check for commit mismatch and invalidate old cache
        const existingUrlCache = memCache.get(urlKey);
        if (existingUrlCache && commit && existingUrlCache.data?.meta?.commit !== commit) {
          // Repository has been updated to a new commit, invalidate old cache
          logger.info('Repository commit changed, invalidating old cache', {
            url: v.url,
            oldCommit: existingUrlCache.data?.meta?.commit,
            newCommit: commit
          });
          memCache.delete(urlKey);
          // Also try to remove from disk cache
          try {
            const oldFile = path.join(diskDir, `${keyHash(urlKey)}.json`);
            await fs.unlink(oldFile).catch(() => {});
          } catch {}
        }

        // Cache the new data
        memCache.set(urlKey, { data, ts: Date.now() });
        if (commitKey) memCache.set(commitKey, { data, ts: Date.now() });
        ensureCapacity();
        writeDisk(urlKey, data).catch(() => {});
        if (commitKey) writeDisk(commitKey, data).catch(() => {});

        return res.status(response.status || 200).json(data);
      } catch (err) {
        if (err?.code === 'ECONNABORTED' || err?.code === 'ETIMEDOUT') throw createTimeoutError('Repository analysis');
        if (err?.response) {
          const { status, data } = err.response;
          if (status >= 400 && status < 500) throw createValidationError(data?.error || `Analysis failed: ${status}`);
        }
        throw createExternalServiceError('Python parser', err);
      }
    }

    if (req.file) {
      const sanitizedName = sanitizeFileName(req.file.originalname || 'repo.zip');
      const form = new FormData();
      // Verify magic bytes to ensure it's actually a ZIP
      if (!isPathInside(req.file.path, uploadDir)) {
        await fs.unlink(req.file.path).catch(() => {});
        throw createValidationError('Unsafe upload path');
      }
      if (!hasZipMagicBytes(req.file.path)) {
        await fs.unlink(req.file.path).catch(() => {});
        throw createValidationError('Uploaded file is not a valid ZIP archive');
      }
      form.append('repoZip', fsSync.createReadStream(req.file.path), sanitizedName);
      try {
        const response = await http.post(`${pythonUrl}/analyze`, form, {
          headers: form.getHeaders(),
          maxBodyLength: Infinity,
          maxContentLength: Infinity,
          timeout,
        });
        fs.unlink(req.file.path).catch(() => {});
        const data = response.data ?? {};

        // Validate schema structure
        const validation = validateUmlSchema(data);
        if (!validation.isValid) {
          logger.warn('Invalid schema received from Python parser for uploaded file', {
            errors: validation.errors,
            filename: sanitizedName,
            dataKeys: Object.keys(data)
          });
          throw createValidationError(`Invalid schema structure: ${validation.errors.join(', ')}`);
        }

        return res.status(response.status || 200).json(data);
      } catch (err) {
        fs.unlink(req.file.path).catch(() => {});
        if (err?.code === 'ECONNABORTED' || err?.code === 'ETIMEDOUT') throw createTimeoutError('File analysis');
        if (err?.response) {
          const { status, data } = err.response;
          if (status >= 400 && status < 500) throw createValidationError(data?.error || `File analysis failed: ${status}`);
        }
        throw createExternalServiceError('Python parser', err);
      }
    }

    throw createValidationError('No repository provided');
  }));

  // GET /health
  router.get('/health', asyncHandler(async (req, res) => {
    const basePayload = {
      ok: true,
      status: 'healthy',
      timestamp: new Date().toISOString(),
      version: packageVersion,
      uptimeSeconds: Math.round(process.uptime()),
      services: { pythonParser: 'unknown' }
    };

    if (isTest) {
      return res.status(200).json(basePayload);
    }

    const health = { ...basePayload };
    try {
      const r = await http.get(`${pythonUrl}/health`, { timeout: 5000 });
      health.services.pythonParser = r.status === 200 ? 'healthy' : 'unhealthy';
    } catch {
      health.status = 'degraded';
      health.services.pythonParser = 'unreachable';
    }
    const code = health.status === 'healthy' ? 200 : 503;
    return res.status(code).json(health);
  }));

  // Admin cache endpoints (token-guarded, disabled if no token)
  const adminGuard = (req, res, next) => {
    if (!adminToken) return res.status(404).json({ success: false, error: { message: 'Not found' } });
    const token = req.get('X-Admin-Token');
    if (token && token === adminToken) return next();
    return res.status(403).json({ success: false, error: { message: 'Forbidden' } });
  };

  router.get('/admin/cache/info', adminGuard, asyncHandler(async (req, res) => {
    // Count disk files
    let diskFiles = 0;
    try {
      const files = await fs.readdir(diskDir);
      diskFiles = files.filter(f => f.endsWith('.json')).length;
    } catch {}
    res.json({
      success: true,
      memoryEntries: memCache.size,
      maxEntries,
      cacheTtlMs,
      diskDir,
      diskTtlMs,
      diskFiles,
      lastPurge,
    });
  }));

  router.post('/admin/cache/purge', adminGuard, asyncHandler(async (req, res) => {
    // Purge memory
    memCache.clear();
    // Purge disk (best effort)
    try {
      const files = await fs.readdir(diskDir);
      await Promise.all(files.filter(f => f.endsWith('.json')).map(f => fs.unlink(path.join(diskDir, f)).catch(() => {})));
    } catch {}
    lastPurge = new Date().toISOString();
    res.json({ success: true, lastPurge });
  }));

  // Error handler local to router (uses provided logger)
  router.use(errorHandler(logger));

  return router;
}
