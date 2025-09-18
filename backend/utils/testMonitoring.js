/**
 * Mock monitoring for test environment
 * Provides minimal monitoring functionality without complex dependencies
 */

// Mock metrics middleware
export const metricsMiddleware = (req, res, next) => {
  next();
};

// Mock recording functions
export const recordAnalysisMetrics = (success, duration) => {
  // No-op for tests
};

export const recordCacheMetrics = (hit, type = null) => {
  // No-op for tests
};

export const recordErrorMetrics = (errorType) => {
  // No-op for tests
};

// Mock monitoring endpoints
export const createMonitoringEndpoints = (app) => {
  // Add mock endpoints
  app.get('/metrics', (req, res) => {
    res.json({ 
      status: 'test-mode',
      timestamp: new Date().toISOString()
    });
  });
  
  app.get('/health/summary', (req, res) => {
    res.json({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      performance: { avgResponseTime: 0, cacheHitRate: 100, successRate: 100 },
      resources: { memoryUsage: 0, cpuUsage: 0, activeRequests: 0 },
      counters: { totalRequests: 0, totalAnalyses: 0, totalErrors: 0 }
    });
  });
  
  app.get('/system/info', (req, res) => {
    res.json({
      node: { version: process.version, platform: process.platform },
      environment: 'test',
      timestamp: new Date().toISOString()
    });
  });
};

// Mock periodic logging
export const startPeriodicMetricsLogging = () => {
  // No-op for tests
};