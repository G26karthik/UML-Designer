/**
 * Security utilities for the backend service
 */
import fs from 'fs';
import path from 'path';

/**
 * Validates CORS origin against allowed list
 */
export const validateCorsOrigin = (origin, allowedOrigins) => {
  // In test environment, allow all origins for testing
  if (process.env.NODE_ENV === 'test') {
    return true;
  }
  
  // In development, allow localhost origins with any port
  if (process.env.NODE_ENV === 'development') {
    if (!origin) return true; // Allow requests with no origin in dev (Postman, etc.)
    
    // Allow localhost with any port for development
    if (/^https?:\/\/localhost(:\d+)?$/.test(origin)) {
      return true;
    }
  }
  
  // Production: strict origin checking
  if (!origin) return false; // No origin not allowed in production
  
  const allowed = allowedOrigins || [];
  return allowed.includes(origin);
};

/**
 * Sanitizes file names for safe storage
 */
export const sanitizeFileName = (fileName) => {
  if (!fileName || typeof fileName !== 'string') {
    return 'unknown';
  }
  
  return fileName
    .replace(/[^a-zA-Z0-9.-]/g, '_')
    .replace(/^\.+/, '') // Remove leading dots
    .substring(0, 255); // Limit length
};

/**
 * Validates GitHub URL format
 */
export const validateGitHubUrl = (url) => {
  if (!url || typeof url !== 'string') {
    return { isValid: false, error: 'URL is required' };
  }
  
  const githubPattern = /^https:\/\/github\.com\/[a-zA-Z0-9_.-]+\/[a-zA-Z0-9_.-]+\/?$/;
  const trimmedUrl = url.trim();
  
  if (!githubPattern.test(trimmedUrl)) {
    return { 
      isValid: false, 
      error: 'Invalid GitHub URL format' 
    };
  }
  
  return { isValid: true, url: trimmedUrl };
};

/**
 * Upload security helpers for ZIP files
 */
export const isZipFilename = (name) => typeof name === 'string' && /\.zip$/i.test(name.trim());

export const isAllowedZipMime = (mime) => {
  if (typeof mime !== 'string') return false;
  const allowed = new Set([
    'application/zip',
    'application/x-zip-compressed',
    'multipart/x-zip',
    'application/octet-stream', // some browsers use this for zip uploads
  ]);
  return allowed.has(mime);
};

export const isPathInside = (childPath, parentPath) => {
  try {
    const resolvedChild = path.resolve(childPath);
    const resolvedParent = path.resolve(parentPath);
    const rel = path.relative(resolvedParent, resolvedChild);
    return rel === '' || (!rel.startsWith('..') && !path.isAbsolute(rel));
  } catch {
    return false;
  }
};

export const validateUploadFile = (file, uploadDir) => {
  if (!file) return { isValid: false, error: 'No file provided' };
  if (!isZipFilename(file.originalname)) return { isValid: false, error: 'Only .zip files are allowed' };
  if (!isAllowedZipMime(file.mimetype)) return { isValid: false, error: `Invalid file type: ${file.mimetype}` };
  if (!isPathInside(file.path, uploadDir)) return { isValid: false, error: 'Unsafe upload path' };
  return { isValid: true };
};

export const hasZipMagicBytes = (filePath) => {
  try {
    const fd = fs.openSync(filePath, 'r');
    const buffer = Buffer.alloc(4);
    const bytesRead = fs.readSync(fd, buffer, 0, 4, 0);
    fs.closeSync(fd);
    if (bytesRead < 4) return false;
    // ZIP files typically start with 'PK\u0003\u0004' or 'PK\u0005\u0006' (empty archive)
    return buffer[0] === 0x50 && buffer[1] === 0x4B && (buffer[2] === 0x03 || buffer[2] === 0x05);
  } catch {
    return false;
  }
};

/**
 * Rate limiting configuration
 */
export const createRateLimitConfig = () => {
  return {
    windowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS || '900000'), // 15 minutes
    max: parseInt(process.env.RATE_LIMIT_MAX_REQUESTS || '100'), // limit each IP to 100 requests per windowMs
    message: {
      error: 'Too many requests from this IP, please try again later.',
      retryAfter: Math.ceil(parseInt(process.env.RATE_LIMIT_WINDOW_MS || '900000') / 1000)
    },
    standardHeaders: true, // Return rate limit info in the `RateLimit-*` headers
    legacyHeaders: false, // Disable the `X-RateLimit-*` headers
  };
};

/**
 * Request timeout configuration
 */
export const createTimeoutConfig = () => {
  const timeout = parseInt(process.env.ANALYZE_TIMEOUT_MS || '120000');
  return {
    timeout,
    timeoutErrorMessage: `Request timeout after ${timeout/1000} seconds`
  };
};