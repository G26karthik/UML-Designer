#!/usr/bin/env node

/**
 * Deployment Verification Script
 * Verifies that the deployment is successful and all features are working
 */

import axios from 'axios';
import { performance } from 'perf_hooks';

// Configuration
const BASE_URL = process.env.DEPLOYMENT_URL || 'http://localhost:3001';
const TIMEOUT = 30000;

const log = {
  info: (msg) => console.log(`🔍 ${msg}`),
  success: (msg) => console.log(`✅ ${msg}`),
  warning: (msg) => console.log(`⚠️ ${msg}`),
  error: (msg) => console.log(`❌ ${msg}`)
};

class DeploymentVerifier {
  constructor() {
    this.results = [];
    this.startTime = performance.now();
  }

  async verify() {
    log.info(`Starting deployment verification for: ${BASE_URL}`);
    console.log();

    // Core functionality tests
    await this.testBasicConnectivity();
    await this.testHealthEndpoint();
    await this.testMonitoringEndpoints();
    await this.testErrorHandling();
    await this.testSecurity();
    await this.testPerformance();

    return this.generateReport();
  }

  async testBasicConnectivity() {
    log.info('Testing basic connectivity...');
    try {
      const response = await axios.get(`${BASE_URL}/health`, { timeout: TIMEOUT });
      if (response.status === 200) {
        this.addResult('Basic Connectivity', true, 'Service is accessible');
      } else {
        this.addResult('Basic Connectivity', false, `Unexpected status: ${response.status}`);
      }
    } catch (error) {
      this.addResult('Basic Connectivity', false, `Connection failed: ${error.message}`);
    }
  }

  async testHealthEndpoint() {
    log.info('Testing health endpoint...');
    try {
      const response = await axios.get(`${BASE_URL}/health`, { timeout: TIMEOUT });
      const health = response.data;
      
      const hasRequiredFields = health.status && health.timestamp && health.version;
      if (hasRequiredFields) {
        this.addResult('Health Endpoint', true, `Status: ${health.status}, Version: ${health.version}`);
      } else {
        this.addResult('Health Endpoint', false, 'Missing required health check fields');
      }
    } catch (error) {
      this.addResult('Health Endpoint', false, `Health check failed: ${error.message}`);
    }
  }

  async testMonitoringEndpoints() {
    log.info('Testing monitoring endpoints...');
    
    const endpoints = [
      { path: '/health/summary', name: 'Health Summary' },
      { path: '/metrics', name: 'Metrics' },
      { path: '/system/info', name: 'System Info' }
    ];

    for (const endpoint of endpoints) {
      try {
        const response = await axios.get(`${BASE_URL}${endpoint.path}`, { timeout: TIMEOUT });
        if (response.status === 200 && response.data) {
          this.addResult(`${endpoint.name} Endpoint`, true, 'Endpoint accessible and returning data');
        } else {
          this.addResult(`${endpoint.name} Endpoint`, false, `Invalid response: ${response.status}`);
        }
      } catch (error) {
        this.addResult(`${endpoint.name} Endpoint`, false, `Endpoint failed: ${error.message}`);
      }
    }
  }

  async testErrorHandling() {
    log.info('Testing error handling...');
    try {
      // Test 404 error
      const response = await axios.get(`${BASE_URL}/nonexistent-endpoint`, {
        timeout: TIMEOUT,
        validateStatus: () => true
      });
      
      if (response.status === 404) {
        this.addResult('404 Error Handling', true, 'Proper 404 response for nonexistent endpoints');
      } else {
        this.addResult('404 Error Handling', false, `Expected 404, got ${response.status}`);
      }
    } catch (error) {
      this.addResult('404 Error Handling', false, `Error handling test failed: ${error.message}`);
    }
  }

  async testSecurity() {
    log.info('Testing security headers...');
    try {
      const response = await axios.get(`${BASE_URL}/health`, { timeout: TIMEOUT });
      const headers = response.headers;
      
      // Check for security headers
      const securityHeaders = ['x-powered-by', 'x-frame-options', 'x-content-type-options'];
      const hasSecurityHeaders = securityHeaders.some(header => headers[header] !== undefined);
      
      this.addResult('Security Headers', hasSecurityHeaders, 
        hasSecurityHeaders ? 'Security headers present' : 'Security headers may be missing');
    } catch (error) {
      this.addResult('Security Headers', false, `Security test failed: ${error.message}`);
    }
  }

  async testPerformance() {
    log.info('Testing performance...');
    const tests = [];
    
    try {
      // Run 5 concurrent requests
      for (let i = 0; i < 5; i++) {
        tests.push(this.timeRequest(`${BASE_URL}/health`));
      }
      
      const times = await Promise.all(tests);
      const avgTime = times.reduce((a, b) => a + b, 0) / times.length;
      const maxTime = Math.max(...times);
      
      const performanceGood = avgTime < 2000 && maxTime < 5000; // 2s avg, 5s max
      
      this.addResult('Performance Test', performanceGood,
        `Avg: ${avgTime.toFixed(0)}ms, Max: ${maxTime.toFixed(0)}ms`);
    } catch (error) {
      this.addResult('Performance Test', false, `Performance test failed: ${error.message}`);
    }
  }

  async timeRequest(url) {
    const start = performance.now();
    await axios.get(url, { timeout: TIMEOUT });
    return performance.now() - start;
  }

  addResult(test, success, message) {
    this.results.push({ test, success, message });
    if (success) {
      log.success(`${test}: ${message}`);
    } else {
      log.error(`${test}: ${message}`);
    }
  }

  generateReport() {
    const totalTests = this.results.length;
    const passedTests = this.results.filter(r => r.success).length;
    const failedTests = totalTests - passedTests;
    const totalTime = Math.round(performance.now() - this.startTime);
    
    console.log('\n=== DEPLOYMENT VERIFICATION REPORT ===\n');
    console.log(`Total Duration: ${totalTime}ms`);
    console.log(`Tests Passed: ${passedTests}/${totalTests}`);
    console.log(`Tests Failed: ${failedTests}/${totalTests}`);
    
    if (failedTests > 0) {
      console.log('\nFailed Tests:');
      this.results
        .filter(r => !r.success)
        .forEach(result => console.log(`  ❌ ${result.test}: ${result.message}`));
    }
    
    console.log('\nDetailed Results:');
    this.results.forEach(result => {
      const status = result.success ? '✅' : '❌';
      console.log(`  ${status} ${result.test}: ${result.message}`);
    });
    
    const success = failedTests === 0;
    console.log(`\n🎯 Deployment Status: ${success ? '✅ SUCCESS' : '❌ FAILED'}`);
    
    if (success) {
      console.log('\n🚀 Deployment verified successfully! Service is ready for production use.');
    } else {
      console.log('\n⚠️ Deployment verification failed. Please review the failed tests above.');
    }
    
    return success ? 0 : 1;
  }
}

// Main execution
async function main() {
  try {
    const verifier = new DeploymentVerifier();
    const exitCode = await verifier.verify();
    process.exit(exitCode);
  } catch (error) {
    log.error(`Verification script failed: ${error.message}`);
    process.exit(1);
  }
}

main();