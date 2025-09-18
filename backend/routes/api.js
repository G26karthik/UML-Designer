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

import { validateCorsOrigin, sanitizeFileName, validateGitHubUrl, validateUploadFile, hasZipMagicBytes, isZipFilename, isAllowedZipMime, isPathInside } from '../utils/security.js';
import {
  errorHandler,
  asyncHandler,
  createValidationError,
  createTimeoutError,
  createExternalServiceError,
  AppError,
  ErrorTypes,
} from '../utils/errorHandler.js';

const keyHash = s => crypto.createHash('sha1').update(s).digest('hex');
const cacheKey = (url, commit) => (commit ? `${url}@${commit}` : url);

export function createApiRouter(options = {}) {
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
  } = options;

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

        // POST /uml-from-prompt (body: { prompt })
        router.post('/uml-from-prompt', asyncHandler(async (req, res) => {
          const timeout = Number(process.env.ANALYZE_TIMEOUT_MS || 120_000);
          const { prompt } = req.body || {};
          if (!prompt || typeof prompt !== 'string' || !prompt.trim()) {
            throw createValidationError('Prompt is required and must be a non-empty string');
          }
          try {
            // Call Python parser with prompt
            const response = await http.post(`${pythonUrl}/uml-from-prompt`, { prompt }, { timeout });
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
  let http = httpClient;
  router.__setHttpClient = client => { http = client || axios; };
  router.__purgeMemoryCache = () => { memCache.clear(); lastPurge = new Date().toISOString(); };

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
        const commit = data?.meta?.commit;
        const urlKey = cacheKey(v.url);
        const commitKey = commit ? cacheKey(v.url, commit) : null;
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
        return res.status(response.status || 200).json(response.data ?? {});
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
    if (isTest) return res.status(200).json({ ok: true, status: 'healthy' });
    const health = { ok: true, status: 'healthy', services: { pythonParser: 'unknown' } };
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
