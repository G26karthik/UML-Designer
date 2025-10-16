/**
 * Backend Constants
 * Centralized configuration for the backend service
 */

// Cache Configuration
export const CACHE_CONFIG = {
  MEMORY_TTL_MS: parseInt(process.env.CACHE_TTL_MS) || 5 * 60 * 1000, // 5 minutes
  DISK_TTL_MS: parseInt(process.env.DISK_CACHE_TTL_MS) || 24 * 60 * 60 * 1000, // 24 hours
  MAX_ENTRIES: parseInt(process.env.MAX_CACHE_ENTRIES) || 200,
  PURGE_INTERVAL_MS: 60 * 60 * 1000, // 1 hour
};

// File Limits
export const FILE_LIMITS = {
  MAX_SIZE_BYTES: parseInt(process.env.MAX_FILE_BYTES) || 500 * 1024, // 500 KB
  MAX_FILES: parseInt(process.env.MAX_FILES) || 5000,
  UPLOAD_LIMIT_BYTES: parseInt(process.env.UPLOAD_LIMIT_BYTES) || 50 * 1024 * 1024, // 50 MB
  JSON_LIMIT: process.env.JSON_LIMIT || '20mb',
};

// Timeout Configuration
export const TIMEOUTS = {
  ANALYZE_MS: parseInt(process.env.ANALYZE_TIMEOUT_MS) || 120000, // 2 minutes
  HTTP_REQUEST_MS: parseInt(process.env.HTTP_REQUEST_MS) || 30000, // 30 seconds
  GRACEFUL_SHUTDOWN_MS: 10000, // 10 seconds
};

// Rate Limiting
export const RATE_LIMIT = {
  WINDOW_MS: parseInt(process.env.RATE_WINDOW_MS) || 5 * 60 * 1000, // 5 minutes
  MAX: parseInt(process.env.RATE_MAX) || 60, // 60 requests per window
};

// Security Configuration
export const SECURITY_CONFIG = {
  CORS_CREDENTIALS: process.env.CORS_CREDENTIALS === 'true',
  ALLOWED_MIME_TYPES: [
    'application/zip',
    'application/x-zip-compressed',
    'application/octet-stream'
  ],
  ZIP_MAGIC_BYTES: [0x50, 0x4b, 0x03, 0x04], // PK..
  MAX_PATH_LENGTH: 4096,
};

// Supported File Extensions
export const FILE_EXTENSIONS = {
  PYTHON: ['.py'],
  JAVA: ['.java'],
  CSHARP: ['.cs'],
  JAVASCRIPT: ['.js'],
  TYPESCRIPT: ['.ts'],
  CPP: ['.cpp', '.cc', '.cxx', '.hpp', '.h'],
  C: ['.c', '.h'],
  HTML: ['.html', '.htm'],
  CSS: ['.css'],
  ZIP: ['.zip'],
};

// Language Detection Map
export const LANGUAGE_MAP = {
  '.py': 'python',
  '.java': 'java',
  '.cs': 'csharp',
  '.js': 'javascript',
  '.ts': 'typescript',
  '.cpp': 'cpp',
  '.cc': 'cpp',
  '.cxx': 'cpp',
  '.c': 'c',
  '.html': 'html',
  '.htm': 'html',
  '.css': 'css',
};

// Directory Skip List (performance optimization)
export const SKIP_DIRECTORIES = [
  'node_modules',
  '.git',
  '__pycache__',
  'venv',
  'env',
  '.env',
  'dist',
  'build',
  'target',
  'bin',
  'obj',
  '.pytest_cache',
  '.vscode',
  '.idea',
  'coverage',
  '.next',
];

// HTTP Status Codes
export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  NO_CONTENT: 204,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  TIMEOUT: 408,
  PAYLOAD_TOO_LARGE: 413,
  RATE_LIMIT: 429,
  INTERNAL_ERROR: 500,
  BAD_GATEWAY: 502,
  SERVICE_UNAVAILABLE: 503,
};

// Error Messages
export const ERROR_MESSAGES = {
  INVALID_GITHUB_URL: 'Invalid GitHub URL format. Expected: https://github.com/username/repository',
  INVALID_ZIP: 'Invalid ZIP file format',
  FILE_TOO_LARGE: 'File size exceeds maximum allowed limit',
  TOO_MANY_FILES: 'Repository contains too many files',
  TIMEOUT: 'Analysis timed out. Repository may be too large.',
  PYTHON_PARSER_UNAVAILABLE: 'Python parser service is unavailable',
  CACHE_ERROR: 'Cache operation failed',
  DISK_WRITE_ERROR: 'Failed to write to disk cache',
};

// Success Messages
export const SUCCESS_MESSAGES = {
  ANALYSIS_COMPLETE: 'Repository analysis completed successfully',
  CACHE_HIT: 'Analysis retrieved from cache',
  HEALTH_CHECK_PASSED: 'Health check passed',
};

// API Endpoints
export const API_ENDPOINTS = {
  ANALYZE: '/api/v1/analyze',
  HEALTH: '/api/v1/health',
  METRICS: '/api/v1/metrics',
  OPENAPI: '/api/v1/openapi.json',
  RENDER_PLANTUML: '/api/v1/render-plantuml',
};

// Python Parser Configuration
export const PYTHON_PARSER = {
  URL: process.env.PYTHON_PARSER_URL || 'http://localhost:5000',
  ENDPOINTS: {
    ANALYZE: '/analyze',
    HEALTH: '/health',
    UML_FROM_PROMPT: '/uml-from-prompt',
  },
};

// Logging Configuration
export const LOG_CONFIG = {
  LEVEL: process.env.LOG_LEVEL || (process.env.NODE_ENV === 'production' ? 'info' : 'debug'),
  MAX_FILES: '14d', // 14 days of logs
  MAX_SIZE: '20m', // 20 MB per file
  DATE_PATTERN: 'YYYY-MM-DD',
};

// Monitoring Configuration
export const MONITORING = {
  METRICS_INTERVAL_MS: 60000, // 1 minute
  HEALTH_CHECK_INTERVAL_MS: 30000, // 30 seconds
  ENABLE_DETAILED_METRICS: process.env.ENABLE_DETAILED_METRICS === 'true',
};

// PlantUML Configuration
export const PLANTUML_CONFIG = {
  SERVER_URL: process.env.PLANTUML_SERVER_URL || 'http://localhost:8080',
  PUBLIC_URL: 'https://www.plantuml.com/plantuml',
  TIMEOUT_MS: 60000, // 1 minute
  MAX_DIAGRAM_SIZE: 100000, // 100 KB
  DEFAULT_FORMAT: 'svg',
  SUPPORTED_FORMATS: ['svg', 'png', 'pdf', 'txt'],
};

// Environment
export const ENVIRONMENT = {
  NODE_ENV: process.env.NODE_ENV || 'development',
  PORT: parseInt(process.env.PORT) || 3001,
  IS_PRODUCTION: process.env.NODE_ENV === 'production',
  IS_TEST: process.env.NODE_ENV === 'test',
};

export default {
  CACHE_CONFIG,
  FILE_LIMITS,
  TIMEOUTS,
  RATE_LIMIT,
  SECURITY_CONFIG,
  FILE_EXTENSIONS,
  LANGUAGE_MAP,
  SKIP_DIRECTORIES,
  HTTP_STATUS,
  ERROR_MESSAGES,
  SUCCESS_MESSAGES,
  API_ENDPOINTS,
  PYTHON_PARSER,
  LOG_CONFIG,
  MONITORING,
  PLANTUML_CONFIG,
  ENVIRONMENT,
};
