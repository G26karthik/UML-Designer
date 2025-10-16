/**
 * Configuration Utilities Test Suite
 */
import { validateGitHubUrl, config, apiRequest } from '../utils/config';

describe('Config Utils', () => {
  describe('validateGitHubUrl', () => {
    test('accepts valid GitHub repository URLs', () => {
      const validUrls = [
        'https://github.com/user/repo',
        'https://github.com/user123/repo-name',
        'https://github.com/user_name/repo_name',
        'https://github.com/user-name/repo-name',
        'https://github.com/user/repo/',
      ];

      validUrls.forEach((url) => {
        const result = validateGitHubUrl(url);
        expect(result.isValid).toBe(true);
        expect(result.error).toBeUndefined();
        expect(result.url).toBe(url.endsWith('/') ? url : url);
      });
    });

    test('rejects invalid GitHub URLs', () => {
      const invalidUrls = [
        'http://github.com/user/repo', // HTTP instead of HTTPS
        'https://gitlab.com/user/repo', // Wrong domain
        'https://github.com/user', // Missing repo
        'https://github.com/user/', // Missing repo with slash
        'github.com/user/repo', // Missing protocol
        'https://github.com', // Just domain
        'not-a-url', // Not a URL at all
      ];

      invalidUrls.forEach((url) => {
        const result = validateGitHubUrl(url);
        expect(result.isValid).toBe(false);
        expect(result.error).toBeDefined();
      });
    });

    test('handles empty or null input', () => {
      expect(validateGitHubUrl('').isValid).toBe(false);
      expect(validateGitHubUrl(null).isValid).toBe(false);
      expect(validateGitHubUrl(undefined).isValid).toBe(false);
      expect(validateGitHubUrl('   ').isValid).toBe(false); // Only whitespace
    });

    test('trims whitespace from URLs', () => {
      const urlWithSpaces = '  https://github.com/user/repo  ';
      const result = validateGitHubUrl(urlWithSpaces);
      
      expect(result.isValid).toBe(true);
      expect(result.url).toBe('https://github.com/user/repo');
    });
  });

  describe('config object', () => {
    test('has required API configuration', () => {
      expect(config.api).toBeDefined();
      expect(config.api.baseUrl).toBeDefined();
      expect(config.api.timeout).toBeDefined();
      expect(typeof config.api.timeout).toBe('number');
    });

    test('has environment configuration', () => {
      expect(config.env).toBeDefined();
      expect(typeof config.isDevelopment).toBe('boolean');
      expect(typeof config.isProduction).toBe('boolean');
    });

    test('has GitHub configuration', () => {
      expect(config.github).toBeDefined();
      expect(config.github.urlPattern).toBeInstanceOf(RegExp);
    });

    test('has UI configuration', () => {
      expect(config.ui).toBeDefined();
      expect(config.ui.maxFileSize).toBeDefined();
      expect(config.ui.supportedDiagramTypes).toBeInstanceOf(Array);
    });
  });

  describe('apiRequest', () => {
    // Mock fetch for testing
    const originalFetch = global.fetch;
    
    beforeEach(() => {
      global.fetch = jest.fn();
    });
    
    afterEach(() => {
      global.fetch = originalFetch;
      jest.restoreAllMocks();
    });

    test('makes successful API request', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        json: jest.fn().mockResolvedValue({ success: true, data: 'test' })
      };
      
      global.fetch.mockResolvedValue(mockResponse);
      
      const result = await apiRequest('/test');
      
      expect(result).toEqual({ success: true, data: 'test' });
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/test'),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'X-Correlation-ID': expect.stringMatching(/^fe-\d+-[a-z0-9]+$/)
          })
        })
      );
    });

    test('handles timeout errors', async () => {
      const mockAbortError = new Error('The operation was aborted.');
      mockAbortError.name = 'AbortError';
      
      global.fetch.mockRejectedValue(mockAbortError);
      
      await expect(apiRequest('/test')).rejects.toThrow('Request timed out');
    });

    test('handles network errors', async () => {
      const networkError = new TypeError('Failed to fetch');
      
      global.fetch.mockRejectedValue(networkError);
      
      await expect(apiRequest('/test')).rejects.toThrow('Network connection failed');
    });

    test('handles HTTP error responses', async () => {
      const mockResponse = {
        ok: false,
        status: 404,
        json: jest.fn().mockResolvedValue({ error: 'Not found' })
      };
      
      global.fetch.mockResolvedValue(mockResponse);
      
      await expect(apiRequest('/test')).rejects.toThrow('Not found');
    });

    test('handles invalid JSON responses', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        json: jest.fn().mockRejectedValue(new Error('Invalid JSON'))
      };
      
      global.fetch.mockResolvedValue(mockResponse);
      
      const result = await apiRequest('/test');
      
      expect(result).toEqual({ error: 'Invalid response format from server' });
    });

    test('handles API error responses', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        json: jest.fn().mockResolvedValue({ success: false, error: { message: 'API error' } })
      };
      
      global.fetch.mockResolvedValue(mockResponse);
      
      await expect(apiRequest('/test')).rejects.toThrow('API error');
    });
  });
});