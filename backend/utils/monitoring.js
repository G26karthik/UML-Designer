/**
 * Production monitoring and metrics collection
 * Provides real-time monitoring, performance metrics, and health monitoring
 */

import { EventEmitter } from 'events';
import os from 'os';
import process from 'process';
import logger, { logHealthCheck } from './logger.js';

// Metrics collector class
class MetricsCollector extends EventEmitter {
  constructor() {
    super();
  this.metrics = {
      // Application metrics
      requests: {
        total: 0,
        successful: 0,
        failed: 0,
        current: 0,
        avgResponseTime: 0
      },
      
      // Repository analysis metrics
      analysis: {
        total: 0,
        successful: 0,
        failed: 0,
        avgDuration: 0
      },
      
      // Cache metrics
      cache: {
        hits: 0,
        misses: 0,
        memoryHits: 0,
        diskHits: 0,
        hitRate: 0
      },
      
      // System metrics
      system: {
        cpuUsage: 0,
        memoryUsage: 0,
        uptime: 0,
        loadAverage: [0, 0, 0]
      },
      
      // Error metrics
      errors: {
        total: 0,
        validation: 0,
        timeout: 0,
        external: 0,
        internal: 0
      }
    };
    
    this.responseTimes = [];
    this.analysisDurations = [];
    this.startTime = Date.now();
    
    // Start periodic system metrics collection
  this.systemMetricsInterval = null;
  this.startSystemMetricsCollection();
  }
  
  // Request metrics
  recordRequest() {
    this.metrics.requests.total++;
    this.metrics.requests.current++;
  }
  
  recordRequestComplete(success, responseTime) {
    this.metrics.requests.current--;
    
    if (success) {
      this.metrics.requests.successful++;
    } else {
      this.metrics.requests.failed++;
    }
    
    // Update average response time
    this.responseTimes.push(responseTime);
    if (this.responseTimes.length > 1000) {
      this.responseTimes = this.responseTimes.slice(-1000); // Keep last 1000
    }
    
    this.metrics.requests.avgResponseTime = 
      this.responseTimes.reduce((a, b) => a + b, 0) / this.responseTimes.length;
  }
  
  // Analysis metrics
  recordAnalysis(success, duration) {
    this.metrics.analysis.total++;
    
    if (success) {
      this.metrics.analysis.successful++;
    } else {
      this.metrics.analysis.failed++;
    }
    
    if (duration) {
      this.analysisDurations.push(duration);
      if (this.analysisDurations.length > 100) {
        this.analysisDurations = this.analysisDurations.slice(-100); // Keep last 100
      }
      
      this.metrics.analysis.avgDuration = 
        this.analysisDurations.reduce((a, b) => a + b, 0) / this.analysisDurations.length;
    }
  }
  
  // Cache metrics
  recordCacheHit(type) {
    this.metrics.cache.hits++;
    
    if (type === 'memory') {
      this.metrics.cache.memoryHits++;
    } else if (type === 'disk') {
      this.metrics.cache.diskHits++;
    }
    
    this.updateCacheHitRate();
  }
  
  recordCacheMiss() {
    this.metrics.cache.misses++;
    this.updateCacheHitRate();
  }
  
  updateCacheHitRate() {
    const total = this.metrics.cache.hits + this.metrics.cache.misses;
    this.metrics.cache.hitRate = total > 0 ? (this.metrics.cache.hits / total) * 100 : 0;
  }
  
  // Error metrics
  recordError(type) {
    this.metrics.errors.total++;
    
    switch (type) {
      case 'VALIDATION':
        this.metrics.errors.validation++;
        break;
      case 'TIMEOUT':
        this.metrics.errors.timeout++;
        break;
      case 'EXTERNAL_SERVICE':
        this.metrics.errors.external++;
        break;
      case 'INTERNAL':
        this.metrics.errors.internal++;
        break;
    }
  }
  
  // System metrics collection
  startSystemMetricsCollection() {
    const collectSystemMetrics = () => {
      const cpuUsage = process.cpuUsage();
      const memUsage = process.memoryUsage();
      
      this.metrics.system = {
        cpuUsage: Math.round((cpuUsage.user + cpuUsage.system) / 1000), // Convert to ms
        memoryUsage: Math.round((memUsage.heapUsed / memUsage.heapTotal) * 100),
        uptime: Math.round(process.uptime()),
        loadAverage: os.loadavg().map(avg => Math.round(avg * 100) / 100)
      };
      
      // Emit system metrics event
      this.emit('systemMetrics', this.metrics.system);
    };
    
    collectSystemMetrics(); // Initial collection

    const shouldDisableInterval =
      process.env.NODE_ENV === 'test' ||
      process.env.DISABLE_SYSTEM_METRICS === 'true';

    if (shouldDisableInterval) {
      return;
    }

    // Collect system metrics every 30 seconds
    this.systemMetricsInterval = setInterval(collectSystemMetrics, 30000);

    if (typeof this.systemMetricsInterval.unref === 'function') {
      this.systemMetricsInterval.unref();
    }
  }
  
  // Get current metrics snapshot
  getMetrics() {
    return {
      ...this.metrics,
      timestamp: new Date().toISOString(),
      uptime: Math.round((Date.now() - this.startTime) / 1000)
    };
  }
  
  // Get health summary
  getHealthSummary() {
    const metrics = this.getMetrics();
    
    return {
      status: this.determineOverallHealth(metrics),
      timestamp: metrics.timestamp,
      uptime: metrics.uptime,
      performance: {
        avgResponseTime: Math.round(metrics.requests.avgResponseTime),
        cacheHitRate: Math.round(metrics.cache.hitRate),
        successRate: this.calculateSuccessRate(metrics)
      },
      resources: {
        memoryUsage: metrics.system.memoryUsage,
        cpuUsage: metrics.system.cpuUsage,
        activeRequests: metrics.requests.current
      },
      counters: {
        totalRequests: metrics.requests.total,
        totalAnalyses: metrics.analysis.total,
        totalErrors: metrics.errors.total
      }
    };
  }
  
  determineOverallHealth(metrics) {
    // Check critical thresholds
    if (metrics.system.memoryUsage > 90) return 'critical';
    if (metrics.errors.total > metrics.requests.total * 0.1) return 'degraded'; // >10% error rate
    if (metrics.requests.avgResponseTime > 10000) return 'degraded'; // >10s avg response time
    
    return 'healthy';
  }
  
  calculateSuccessRate(metrics) {
    const total = metrics.requests.total;
    if (total === 0) return 100;
    
    return Math.round((metrics.requests.successful / total) * 100);
  }
}

// Create global metrics instance
const metrics = new MetricsCollector();

// Express middleware for metrics collection
export const metricsMiddleware = (req, res, next) => {
  const startTime = Date.now();
  
  // Record request start
  metrics.recordRequest();
  
  // Override res.end to capture completion
  const originalEnd = res.end;
  res.end = function(...args) {
    const responseTime = Date.now() - startTime;
    const success = res.statusCode < 400;
    
    // Record request completion
    metrics.recordRequestComplete(success, responseTime);
    
    originalEnd.apply(this, args);
  };
  
  next();
};

// Utility functions for business logic metrics
export const recordAnalysisMetrics = (success, duration) => {
  metrics.recordAnalysis(success, duration);
};

export const recordCacheMetrics = (hit, type = null) => {
  if (hit) {
    metrics.recordCacheHit(type);
  } else {
    metrics.recordCacheMiss();
  }
};

export const recordErrorMetrics = (errorType) => {
  metrics.recordError(errorType);
};

// Health monitoring endpoints
export const createMonitoringEndpoints = (app) => {
  // Metrics endpoint
  app.get('/metrics', (req, res) => {
    res.json(metrics.getMetrics());
  });
  
  // Health summary endpoint
  app.get('/health/summary', (req, res) => {
    const summary = metrics.getHealthSummary();
    const statusCode = summary.status === 'healthy' ? 200 : 
                      summary.status === 'degraded' ? 207 : 503;
    
    res.status(statusCode).json(summary);
  });
  
  // Detailed system info endpoint
  app.get('/system/info', (req, res) => {
    const systemInfo = {
      node: {
        version: process.version,
        platform: process.platform,
        arch: process.arch,
        pid: process.pid
      },
      os: {
        type: os.type(),
        release: os.release(),
        hostname: os.hostname(),
        cpus: os.cpus().length,
        totalMemory: Math.round(os.totalmem() / 1024 / 1024 / 1024 * 100) / 100 // GB
      },
      environment: process.env.NODE_ENV || 'development',
      timestamp: new Date().toISOString()
    };
    
    res.json(systemInfo);
  });
};

// Log metrics periodically
export const startPeriodicMetricsLogging = () => {
  const logMetrics = () => {
    const summary = metrics.getHealthSummary();
    
    logger.info('Performance Metrics', {
      avgResponseTime: summary.performance.avgResponseTime,
      cacheHitRate: summary.performance.cacheHitRate,
      successRate: summary.performance.successRate,
      memoryUsage: summary.resources.memoryUsage,
      activeRequests: summary.resources.activeRequests,
      totalRequests: summary.counters.totalRequests,
      totalErrors: summary.counters.totalErrors
    });
    
    // Log health check based on status
    logHealthCheck('application_metrics', summary.status, summary);
  };
  
  // Log metrics every 5 minutes
  setInterval(logMetrics, 5 * 60 * 1000);
};

export default metrics;