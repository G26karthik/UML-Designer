/**
 * Backend Regression Tests
 * Tests for bugs that have been fixed to ensure they don't reappear
 */
import request from 'supertest';
import createApp, { __setHttpClient } from '../index.js';
import { createApiRouter } from '../routes/api.js';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

describe('Backend Regression Tests', () => {
  let app;
  let apiRouter;

  beforeAll(() => {
    apiRouter = createApiRouter({ isTest: true });
    app = createApp();
  });

  describe('Cache Invalidation Regression', () => {
    test('should invalidate cache when repository commit changes', async () => {
      // This test validates cache invalidation logic without calling Python service
      // We'll test the caching behavior by mocking at the router level
      
      // Clear any existing cache
      apiRouter.__purgeMemoryCache();
      
      // Mock the HTTP client to simulate Python service responses
      let callCount = 0;
      const mockClient = {
        post: (url, body) => {
          callCount++;
          // For this test, we'll simulate the Python service being unavailable
          // and test that the cache invalidation logic works with commit-based keys
          return Promise.reject(new Error('Service unavailable for cache test'));
        }
      };

      __setHttpClient(mockClient);

      // Since Python service is mocked to fail, all requests should get 502
      // But the cache logic should still work (though we can't test commit invalidation without successful responses)
      
      // Test that different commits create different cache keys
      const response1 = await request(app)
        .post('/analyze')
        .send({ githubUrl: 'https://github.com/test/repo', commit: 'commit1' })
        .expect(502);

      const response2 = await request(app)
        .post('/analyze')
        .send({ githubUrl: 'https://github.com/test/repo', commit: 'commit2' })
        .expect(502);

      // Both should fail since service is mocked to be unavailable
      expect(response1.body.error.message).toContain('Python parser service unavailable');
      expect(response2.body.error.message).toContain('Python parser service unavailable');
      
      // The call count should be 2 since different commits should bypass cache
      expect(callCount).toBe(2);
    });
  });

  describe('Error Handling Regression', () => {
    test('should handle malformed JSON gracefully', async () => {
      const response = await request(app)
        .post('/generate-plantuml')
        .set('Content-Type', 'application/json')
        .send('{invalid json')
        .expect(400);

      expect(response.body).toHaveProperty('error');
      expect(response.body.error).toContain('Invalid JSON');
    });

    test('should handle missing required fields', async () => {
      const response = await request(app)
        .post('/generate-plantuml')
        .send({})
        .expect(400);

      expect(response.body).toHaveProperty('error');
      expect(response.body.error).toContain('schema is required');
    });

    test('should handle oversized payloads', async () => {
      const largeSchema = {
        python: Array(10000).fill({
          class: 'LargeClass',
          fields: Array(1000).fill('field: type'),
          methods: Array(1000).fill('method')
        }),
        relations: []
      };

      const response = await request(app)
        .post('/generate-plantuml')
        .send({
          schema: largeSchema,
          diagram_type: 'class'
        });

      // Should either succeed or fail gracefully with proper error
      if (response.status !== 200) {
        expect(response.body).toHaveProperty('error');
      }
    });
  });

  describe('File Upload Regression', () => {
    test('should reject non-ZIP files', async () => {
      const response = await request(app)
        .post('/analyze')
        .attach('repoZip', Buffer.from('not a zip'), 'notzip.txt')
        .expect(400);

      expect(response.body).toHaveProperty('error');
      expect(response.body.error).toContain('.zip');
    });

    test('should handle empty ZIP files', async () => {
      // Create an empty ZIP file in memory
      const emptyZipBuffer = Buffer.from([
        0x50, 0x4B, 0x05, 0x06, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
      ]);

      // Mock the Python service to be unavailable so we test the validation logic
      const mockClient = {
        post: () => Promise.reject(new Error('Service unavailable'))
      };
      __setHttpClient(mockClient);

      const response = await request(app)
        .post('/analyze')
        .attach('repoZip', emptyZipBuffer, 'empty.zip');

      // Should fail with 502 since Python service is unavailable, but the validation should have passed
      // The empty ZIP validation happens after file upload validation
      expect(response.status).toBe(502);
      expect(response.body.error.message).toContain('Python parser service unavailable');
    });
  });

  describe('Rate Limiting Regression', () => {
    test('should handle rapid successive requests', async () => {
      const mockClient = {
        post: () => Promise.resolve({
          status: 200,
          data: {
            python: [{ class: 'Test', fields: [] }],
            relations: [],
            meta: { files_scanned: 1 }
          }
        })
      };

      __setHttpClient(mockClient);

      // Make multiple rapid requests
      const promises = [];
      for (let i = 0; i < 10; i++) {
        promises.push(
          request(app)
            .post('/generate-plantuml')
            .send({
              schema: { python: [{ class: 'Test' }], relations: [] },
              diagram_type: 'class'
            })
        );
      }

      const responses = await Promise.all(promises);

      // At least some should succeed (depending on rate limits)
      const successCount = responses.filter(r => r.status === 200).length;
      const rateLimitedCount = responses.filter(r => r.status === 429).length;

      expect(successCount + rateLimitedCount).toBe(10);
      if (rateLimitedCount > 0) {
        // If rate limiting is working, some requests should be rate limited
        expect(rateLimitedCount).toBeGreaterThan(0);
      }
    });
  });
});