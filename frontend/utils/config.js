/**
 * Application Configuration
 * Centralizes all environment variables and configuration
 */

import { validateApiResponse } from './errorHandler';

export const config = {
  // API Configuration
  api: {
    baseUrl: process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:3001',
    timeout: parseInt(process.env.NEXT_PUBLIC_API_TIMEOUT || '120000'),
  },
  
  // Environment
  env: process.env.NEXT_PUBLIC_ENV || 'development',
  isDevelopment: (process.env.NEXT_PUBLIC_ENV || 'development') === 'development',
  isProduction: (process.env.NEXT_PUBLIC_ENV || 'development') === 'production',
  
  // Validation
  github: {
    urlPattern: /^https:\/\/github\.com\/[a-zA-Z0-9_-]+\/[a-zA-Z0-9_-]+(?:\/)?$/,
  },
  
  // UI Configuration
  ui: {
    maxFileSize: 50 * 1024 * 1024, // 50MB
    supportedDiagramTypes: ['class', 'usecase', 'activity', 'sequence', 'state'],
  }
};

/**
 * Validates GitHub URL format
 */
export const validateGitHubUrl = (url) => {
  if (!url || typeof url !== 'string') {
    return { isValid: false, error: 'URL is required' };
  }
  
  const trimmedUrl = url.trim();
  if (!config.github.urlPattern.test(trimmedUrl)) {
    return { 
      isValid: false, 
      error: 'Please enter a valid GitHub repository URL (e.g., https://github.com/user/repo)' 
    };
  }
  
  return { isValid: true, url: trimmedUrl };
};

/**
 * API Helper for making requests
 */
export const apiRequest = async (endpoint, options = {}) => {
  // Ensure all API requests use versioned endpoints
  let versionedEndpoint = endpoint;
  if (endpoint === '/analyze') versionedEndpoint = '/api/v1/analyze';
  if (endpoint === '/health') versionedEndpoint = '/api/v1/health';
  if (endpoint === '/uml-from-prompt') versionedEndpoint = '/api/v1/uml-from-prompt';
  const url = `${config.api.baseUrl}${versionedEndpoint}`;
  const defaultOptions = {
    timeout: config.api.timeout,
    headers: {
      'Content-Type': 'application/json',
    },
  };
  
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), defaultOptions.timeout);
  
  try {
    const response = await fetch(url, {
      ...defaultOptions,
      ...options,
      signal: controller.signal,
    });
    
    clearTimeout(timeoutId);
    
    let data;
    try {
      data = await response.json();
    } catch {
      data = { error: 'Invalid response format from server' };
    }
    
    // Use standardized validation
    return validateApiResponse(response, data);
    
  } catch (error) {
    clearTimeout(timeoutId);
    
    // Add context to errors
    if (error.name === 'AbortError') {
      const timeoutError = new Error('Request timed out');
      timeoutError.code = 'TIMEOUT';
      throw timeoutError;
    }
    
    if (error instanceof TypeError && error.message.includes('fetch')) {
      const networkError = new Error('Network connection failed');
      networkError.code = 'NETWORK_ERROR';
      throw networkError;
    }
    
    throw error;
  }
};