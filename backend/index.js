import express from 'express';
import mongoose from 'mongoose';
import multer from 'multer';
import axios from 'axios';
import cors from 'cors';
import dotenv from 'dotenv';
import fs from 'fs';
import path from 'path';
import crypto from 'crypto';
import FormData from 'form-data';
import compression from 'compression';
dotenv.config();

const app = express();
// gzip responses to reduce payload to the frontend
app.use(compression());
app.use(express.json({ limit: process.env.JSON_LIMIT || '5mb' }));

// CORS: allow all by default, or restrict via ALLOWED_ORIGINS (comma-separated)
const allowed = (process.env.ALLOWED_ORIGINS || '').split(',').map(s => s.trim()).filter(Boolean);
app.use(cors({
  origin: (origin, cb) => {
    if (!origin || allowed.length === 0) return cb(null, true);
    return cb(null, allowed.includes(origin));
  }
}));

const upload = multer({
  dest: 'uploads/',
  limits: { fileSize: Number(process.env.UPLOAD_LIMIT_BYTES || 50 * 1024 * 1024) } // 50MB default
});

// Optional MongoDB connection
if (process.env.NODE_ENV !== 'test' && process.env.MONGO_URL) {
  mongoose.connect(process.env.MONGO_URL, { useNewUrlParser: true, useUnifiedTopology: true })
    .then(() => console.log('Mongo connected'))
    .catch(err => console.warn('Mongo connection failed:', err.message));
}

// Base URL for python-parser service (default to localhost when not in Docker)
const PYTHON_PARSER_URL = process.env.PYTHON_PARSER_URL || 'http://localhost:5000';

// Simple in-memory cache for analyze results (reset on server restart)
const cache = new Map(); // key: cacheKey(url, commit?), value: { data, ts }
const MAX_CACHE_ENTRIES = Number(process.env.MAX_CACHE_ENTRIES || 200);
const ensureCacheCapacity = () => {
  while (cache.size > MAX_CACHE_ENTRIES) {
    const firstKey = cache.keys().next().value;
    if (!firstKey) break;
    cache.delete(firstKey);
  }
};
const CACHE_TTL_MS = Number(process.env.CACHE_TTL_MS || 5 * 60 * 1000);

// Persistent disk cache (optional)
const DISK_CACHE_DIR = process.env.DISK_CACHE_DIR || path.join(process.cwd(), 'cache');
const DISK_CACHE_TTL_MS = Number(process.env.DISK_CACHE_TTL_MS || 24 * 60 * 60 * 1000); // 24h
try { fs.mkdirSync(DISK_CACHE_DIR, { recursive: true }); } catch {}
const diskKey = (key) => crypto.createHash('sha1').update(key).digest('hex');
const readDiskCache = (key) => {
  try {
  const file = path.join(DISK_CACHE_DIR, `${diskKey(key)}.json`);
    if (!fs.existsSync(file)) return null;
    const stat = fs.statSync(file);
    if ((Date.now() - stat.mtimeMs) > DISK_CACHE_TTL_MS) return null;
    const txt = fs.readFileSync(file, 'utf8');
    return JSON.parse(txt);
  } catch { return null; }
};
const writeDiskCache = (key, data) => {
  try {
  const file = path.join(DISK_CACHE_DIR, `${diskKey(key)}.json`);
    fs.writeFileSync(file, JSON.stringify(data));
  } catch {}
};

const cacheKey = (url, commit) => commit ? `${url}@${commit}` : url;

// Allow tests to inject a mock HTTP client
let http = axios;
export const __setHttpClient = (client) => { http = client || axios; };

// /analyze endpoint
app.post('/analyze', upload.single('repoZip'), async (req, res) => {
  const { githubUrl } = req.body;
  try {
    if (githubUrl) {
      const now = Date.now();
      // Attempt to get cached by URL alone first
      let key = cacheKey(githubUrl);
      let cached = cache.get(key);
      if (cached && (now - cached.ts) < CACHE_TTL_MS) {
        return res.status(200).json(cached.data);
      }
      let disk = readDiskCache(key);
      if (disk) {
        cache.set(key, { data: disk, ts: Date.now() });
        return res.status(200).json(disk);
      }
  const response = await http.post(`${PYTHON_PARSER_URL}/analyze`, { githubUrl }, { timeout: Number(process.env.ANALYZE_TIMEOUT_MS || 120000) });
      // store cache on success only
      if (response.status >= 200 && response.status < 300) {
        const commit = response.data?.meta?.commit;
        const commitKey = cacheKey(githubUrl, commit);
        const urlKey = cacheKey(githubUrl);
        // store under commit-specific key
        cache.set(commitKey, { data: response.data, ts: Date.now() });
        // also store/update URL-only alias for quick hits
        cache.set(urlKey, { data: response.data, ts: Date.now() });
        ensureCacheCapacity();
        writeDiskCache(commitKey, response.data);
        writeDiskCache(urlKey, response.data);
      }
      return res.status(response.status).json(response.data);
    } else if (req.file) {
      const form = new FormData();
      form.append('repoZip', fs.createReadStream(req.file.path), req.file.originalname || 'repo.zip');
  const response = await http.post(`${PYTHON_PARSER_URL}/analyze`, form, {
        headers: form.getHeaders(),
        maxBodyLength: Infinity,
        maxContentLength: Infinity,
        timeout: Number(process.env.ANALYZE_TIMEOUT_MS || 120000),
      });
      // cleanup temp upload
  try { fs.unlink(req.file.path, () => {}); } catch {}
      return res.status(response.status).json(response.data);
    } else {
      return res.status(400).json({ error: 'No repo provided.' });
    }
  } catch (err) {
    const status = err.response?.status || 500;
    const data = err.response?.data || { error: err.message || 'Unknown error' };
    console.error('Analyze error:', status, data);
    return res.status(status).json({ error: 'Analysis failed', details: data });
  }
});

// Basic health endpoint
app.get('/health', (req, res) => {
  res.json({ ok: true, pythonParser: process.env.PYTHON_PARSER_URL || 'http://localhost:5000' });
});

// Export app for testing
export default app;

// Only start server if run directly (simple ESM check)
if (process.env.NODE_ENV !== 'test' && process.argv[1] && process.argv[1].toLowerCase().endsWith('index.js')) {
  const port = process.env.PORT || 3001;
  app.listen(port, () => {
    console.log(`Backend running on port ${port}`);
  });
}
