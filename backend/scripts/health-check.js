#!/usr/bin/env node

/**
 * Health Check Script for UML Backend
 * Performs comprehensive health checks for monitoring and deployment verification
 */

import axios from 'axios';
import { performance } from 'perf_hooks';

// Configuration
const BASE_URL = process.env.HEALTH_CHECK_URL || 'http://localhost:3001';
const TIMEOUT = parseInt(process.env.HEALTH_CHECK_TIMEOUT) || 30000;
const VERBOSE = process.env.VERBOSE === 'true';

// Color codes for console output
const colors = {
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  reset: '\x1b[0m',
  bold: '\x1b[1m'
};

// Logging utility
const log = {
  info: (msg) => console.log(`${colors.blue}ℹ${colors.reset} ${msg}`),
  success: (msg) => console.log(`${colors.green}✅${colors.reset} ${msg}`),
  warning: (msg) => console.log(`${colors.yellow}⚠${colors.reset} ${msg}`),
  error: (msg) => console.log(`${colors.red}❌${colors.reset} ${msg}`),
  verbose: (msg) => VERBOSE && console.log(`${colors.blue}🔍${colors.reset} ${msg}`)
};

// Health check results
const results = {
  checks: [],
  overall: 'unknown',
  startTime: performance.now()
};

// Individual health check functions
const healthChecks = {
  // Basic connectivity test
  async basicConnectivity() {
    const start = performance.now();
    try {
      const response = await axios.get(`${BASE_URL}/health`, { 
        timeout: TIMEOUT,
        validateStatus: () => true // Accept any status code
      });
      
      const duration = Math.round(performance.now() - start);
      const success = response.status === 200;
      
      return {
        name: 'Basic Connectivity',
        success,
        duration,
        details: {
          status: response.status,
          statusText: response.statusText,
          responseTime: `${duration}ms`
        },
        message: success ? 'Service is reachable' : `HTTP ${response.status}: ${response.statusText}`
      };
    } catch (error) {
      const duration = Math.round(performance.now() - start);
      return {
        name: 'Basic Connectivity',
        success: false,
        duration,
        details: { error: error.message },
        message: `Connection failed: ${error.message}`
      };
    }
  },

  // Detailed health check
  async detailedHealth() {
    const start = performance.now();
    try {
      const response = await axios.get(`${BASE_URL}/health`, { timeout: TIMEOUT });
      const duration = Math.round(performance.now() - start);
      
      const health = response.data;
      const isHealthy = health.status === 'healthy';
      
      return {
        name: 'Detailed Health',
        success: isHealthy,
        duration,
        details: {
          applicationStatus: health.status,
          version: health.version,
          services: health.services,
          timestamp: health.timestamp
        },
        message: isHealthy ? 'All services healthy' : `Service status: ${health.status}`
      };
    } catch (error) {
      const duration = Math.round(performance.now() - start);
      return {
        name: 'Detailed Health',
        success: false,
        duration,
        details: { error: error.message },
        message: `Health check failed: ${error.message}`
      };
    }
  },

  // Performance metrics check
  async performanceMetrics() {
    const start = performance.now();
    try {
      const response = await axios.get(`${BASE_URL}/health/summary`, { timeout: TIMEOUT });
      const duration = Math.round(performance.now() - start);
      
      const summary = response.data;
      const goodPerformance = summary.performance?.avgResponseTime < 5000; // < 5 seconds
      
      return {
        name: 'Performance Metrics',
        success: goodPerformance,
        duration,
        details: {
          avgResponseTime: summary.performance?.avgResponseTime,
          cacheHitRate: summary.performance?.cacheHitRate,
          successRate: summary.performance?.successRate,
          memoryUsage: summary.resources?.memoryUsage,
          activeRequests: summary.resources?.activeRequests
        },
        message: goodPerformance ? 'Performance within acceptable limits' : 'Performance may be degraded'
      };
    } catch (error) {
      const duration = Math.round(performance.now() - start);
      return {
        name: 'Performance Metrics',
        success: false,
        duration,
        details: { error: error.message },
        message: `Metrics check failed: ${error.message}`
      };
    }
  },

  // System information check
  async systemInfo() {
    const start = performance.now();
    try {
      const response = await axios.get(`${BASE_URL}/system/info`, { timeout: TIMEOUT });
      const duration = Math.round(performance.now() - start);
      
      const info = response.data;
      
      return {
        name: 'System Information',
        success: true,
        duration,
        details: {
          nodeVersion: info.node?.version,
          platform: info.node?.platform,
          environment: info.environment,
          cpuCount: info.os?.cpus,
          totalMemory: info.os?.totalMemory
        },
        message: 'System information retrieved successfully'
      };
    } catch (error) {
      const duration = Math.round(performance.now() - start);
      return {
        name: 'System Information',
        success: false,
        duration,
        details: { error: error.message },
        message: `System info check failed: ${error.message}`
      };
    }
  },

  // Response time performance test
  async responseTimeTest() {
    const start = performance.now();
    try {
      const promises = Array(5).fill().map(() => 
        axios.get(`${BASE_URL}/health`, { timeout: TIMEOUT })
      );
      
      const responses = await Promise.all(promises);
      const duration = Math.round(performance.now() - start);
      const avgResponseTime = duration / 5;
      const goodResponseTime = avgResponseTime < 2000; // < 2 seconds average
      
      return {
        name: 'Response Time Test',
        success: goodResponseTime,
        duration,
        details: {
          totalRequests: 5,
          totalDuration: `${duration}ms`,
          averageResponseTime: `${avgResponseTime}ms`,
          allRequestsSuccessful: responses.every(r => r.status === 200)
        },
        message: goodResponseTime ? 'Response times are acceptable' : 'Response times may be slow'
      };
    } catch (error) {
      const duration = Math.round(performance.now() - start);
      return {
        name: 'Response Time Test',
        success: false,
        duration,
        details: { error: error.message },
        message: `Response time test failed: ${error.message}`
      };
    }
  }
};

// Run all health checks
async function runHealthChecks() {
  log.info(`Starting health checks for: ${BASE_URL}`);
  log.info(`Timeout: ${TIMEOUT}ms`);
  console.log();

  for (const [checkName, checkFunction] of Object.entries(healthChecks)) {
    log.verbose(`Running ${checkName}...`);
    
    try {
      const result = await checkFunction();
      results.checks.push(result);
      
      if (result.success) {
        log.success(`${result.name}: ${result.message} (${result.duration}ms)`);
      } else {
        log.error(`${result.name}: ${result.message} (${result.duration}ms)`);
      }
      
      if (VERBOSE && result.details) {
        console.log('   Details:', JSON.stringify(result.details, null, 2));
      }
    } catch (error) {
      const failedResult = {
        name: checkName,
        success: false,
        duration: 0,
        details: { error: error.message },
        message: `Check execution failed: ${error.message}`
      };
      
      results.checks.push(failedResult);
      log.error(`${failedResult.name}: ${failedResult.message}`);
    }
    
    console.log();
  }
}

// Generate summary report
function generateSummary() {
  const totalChecks = results.checks.length;
  const passedChecks = results.checks.filter(c => c.success).length;
  const failedChecks = totalChecks - passedChecks;
  const totalDuration = Math.round(performance.now() - results.startTime);
  
  // Determine overall health
  if (passedChecks === totalChecks) {
    results.overall = 'healthy';
  } else if (passedChecks >= totalChecks * 0.7) {
    results.overall = 'degraded';
  } else {
    results.overall = 'unhealthy';
  }
  
  console.log(`${colors.bold}=== HEALTH CHECK SUMMARY ===${colors.reset}`);
  console.log();
  console.log(`Overall Status: ${results.overall === 'healthy' ? colors.green : results.overall === 'degraded' ? colors.yellow : colors.red}${results.overall.toUpperCase()}${colors.reset}`);
  console.log(`Total Duration: ${totalDuration}ms`);
  console.log(`Checks Passed: ${colors.green}${passedChecks}${colors.reset}/${totalChecks}`);
  console.log(`Checks Failed: ${colors.red}${failedChecks}${colors.reset}/${totalChecks}`);
  console.log();
  
  if (failedChecks > 0) {
    console.log(`${colors.bold}Failed Checks:${colors.reset}`);
    results.checks
      .filter(c => !c.success)
      .forEach(check => {
        console.log(`  ${colors.red}❌${colors.reset} ${check.name}: ${check.message}`);
      });
    console.log();
  }
  
  return results.overall === 'healthy' ? 0 : results.overall === 'degraded' ? 1 : 2;
}

// Main execution
async function main() {
  try {
    await runHealthChecks();
    const exitCode = generateSummary();
    
    // Output JSON results if requested
    if (process.env.OUTPUT_JSON === 'true') {
      console.log(JSON.stringify(results, null, 2));
    }
    
    process.exit(exitCode);
  } catch (error) {
    log.error(`Health check script failed: ${error.message}`);
    process.exit(3);
  }
}

// Handle uncaught errors
process.on('uncaughtException', (error) => {
  log.error(`Uncaught exception: ${error.message}`);
  process.exit(3);
});

process.on('unhandledRejection', (reason) => {
  log.error(`Unhandled rejection: ${reason}`);
  process.exit(3);
});

// Run the health checks
main();