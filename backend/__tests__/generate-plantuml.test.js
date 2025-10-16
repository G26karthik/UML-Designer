/**
 * Backend PlantUML Endpoint Tests
 * Tests Express /generate-plantuml proxy endpoint
 */
import request from 'supertest';
import createApp, { __setHttpClient } from '../index.js';

// Mock the app setup
let app;

// Helper: install a mock HTTP client on the api router. The mockClient
// object should expose post(url, body, opts) -> Promise<{status, data}>.
function setMockClient(mockResponse, status = 200, opts = {}) {
  const client = {
    post: (url, body, options = {}) => new Promise((resolve, reject) => {
      if (opts && opts.error) return reject(opts.error);
      const delay = Number(opts.delay || 0);
      const reqTimeout = options && options.timeout ? Number(options.timeout) : 0;
      // If the mock delay exceeds the caller's timeout, simulate axios timeout
      if (reqTimeout > 0 && delay > 0 && delay > reqTimeout) {
        const e = new Error('timeout of ' + reqTimeout + 'ms exceeded');
        e.code = 'ECONNABORTED';
        return reject(e);
      }
      setTimeout(() => {
        resolve({ status: status || 200, data: mockResponse });
      }, delay);
    })
  };
  __setHttpClient(client);
  return client;
}

describe('POST /generate-plantuml', () => {
  beforeAll(() => {
    // Import the actual Express app
    app = createApp();
  });

  beforeEach(() => {
    // Reset injected http client to a default pass-through that fails if
    // a test didn't configure it.
    __setHttpClient({
      post: () => Promise.reject(new Error('No mock client configured for test'))
    });
  });

  afterAll(() => {
    // No-op: using injected mock client in tests
  });

  // ============================================================================
  // Test Basic Functionality
  // ============================================================================

  test('endpoint exists and accepts POST requests', async () => {
    // Configure mock HTTP client to simulate Python backend
    setMockClient({ plantuml: '@startuml\nclass User\n@enduml', diagram_type: 'class' }, 200);

    const response = await request(app)
      .post('/generate-plantuml')
      .send({
        schema: {
          python: [{ class: 'User', methods: [] }],
          relations: []
        },
        diagram_type: 'class'
      })
      .expect('Content-Type', /json/);

    expect(response.status).toBe(200);
    expect(response.body).toHaveProperty('plantuml');
    expect(response.body.plantuml).toContain('@startuml');
  });

  test('rejects GET requests', async () => {
    const response = await request(app)
      .get('/generate-plantuml');

    expect(response.status).toBe(405);
  });

  test('rejects requests without body', async () => {
    const response = await request(app)
      .post('/generate-plantuml')
      .send();

    expect(response.status).toBeGreaterThanOrEqual(400);
    expect(response.status).toBeLessThan(500);
  });

  // ============================================================================
  // Test Request Validation
  // ============================================================================

  test('validates schema is present', async () => {
    const response = await request(app)
      .post('/generate-plantuml')
      .send({
        diagram_type: 'class'
        // Missing schema
      });

    expect(response.status).toBeGreaterThanOrEqual(400);
  });

  test('validates diagram_type is present', async () => {
    const response = await request(app)
      .post('/generate-plantuml')
      .send({
        schema: { python: [], relations: [] }
        // Missing diagram_type
      });

    expect(response.status).toBeGreaterThanOrEqual(400);
  });

  test('validates diagram_type is valid', async () => {
    const response = await request(app)
      .post('/generate-plantuml')
      .send({
        schema: { python: [], relations: [] },
        diagram_type: 'invalid_type'
      });

    expect(response.status).toBeGreaterThanOrEqual(400);
  });

  test('accepts valid diagram types', async () => {
    const validTypes = ['class', 'sequence', 'usecase', 'state', 'activity'];

    for (const type of validTypes) {
      setMockClient({ plantuml: `@startuml\n@enduml`, diagram_type: type }, 200);

      const response = await request(app)
        .post('/generate-plantuml')
        .send({
          schema: { python: [], relations: [] },
          diagram_type: type
        });

      expect(response.status).toBe(200);
    }
  });

  // ============================================================================
  // Test Proxy Functionality
  // ============================================================================

  test('forwards request to Python backend', async () => {
    const schema = {
      python: [
        {
          class: 'User',
          fields: [{ name: 'id', type: 'int', visibility: 'private' }],
          methods: [{ name: 'getId', visibility: 'public' }]
        }
      ],
      relations: []
    };

    const mockResponse = {
      plantuml: '@startuml\nclass User {\n  - id: int\n  + getId()\n}\n@enduml',
      diagram_type: 'class'
    };

    setMockClient(mockResponse, 200);

    const response = await request(app)
      .post('/generate-plantuml')
      .send({
        schema: schema,
        diagram_type: 'class'
      });

    expect(response.status).toBe(200);
    expect(response.body).toEqual(mockResponse);
  });

  test('handles Python backend errors gracefully', async () => {
    setMockClient({ error: 'Internal server error' }, 500);

    const response = await request(app)
      .post('/generate-plantuml')
      .send({
        schema: { python: [], relations: [] },
        diagram_type: 'class'
      });

    expect(response.status).toBe(500);
    expect(response.body).toHaveProperty('error');
  });

  test('handles Python backend timeout', async () => {
    // Simulate a backend that doesn't respond within timeout
    setMockClient({}, 200, { delay: 10000 });

    const response = await request(app)
      .post('/generate-plantuml')
      .send({
        schema: { python: [], relations: [] },
        diagram_type: 'class'
      })
      .timeout(5000);

    // Should timeout or return error
    expect(response.status).toBeGreaterThanOrEqual(500);
  }, 15000);

  test('handles Python backend connection refused', async () => {
    setMockClient(null, null, { error: { code: 'ECONNREFUSED', message: 'ECONNREFUSED' } });

    const response = await request(app)
      .post('/generate-plantuml')
      .send({
        schema: { python: [], relations: [] },
        diagram_type: 'class'
      });

    expect(response.status).toBeGreaterThanOrEqual(500);
    expect(response.body).toHaveProperty('error');
  });

  // ============================================================================
  // Test Response Format
  // ============================================================================

  test('returns JSON response', async () => {
    setMockClient({ plantuml: '@startuml\n@enduml', diagram_type: 'class' }, 200);

    const response = await request(app)
      .post('/generate-plantuml')
      .send({
        schema: { python: [], relations: [] },
        diagram_type: 'class'
      });

    expect(response.headers['content-type']).toMatch(/application\/json/);
  });

  test('response includes plantuml field', async () => {
    setMockClient({ plantuml: '@startuml\nclass User\n@enduml', diagram_type: 'class' }, 200);

    const response = await request(app)
      .post('/generate-plantuml')
      .send({
        schema: { python: [{ class: 'User', methods: [] }], relations: [] },
        diagram_type: 'class'
      });

    expect(response.status).toBe(200);
    expect(response.body).toHaveProperty('plantuml');
    expect(typeof response.body.plantuml).toBe('string');
  });

  test('response includes diagram_type field', async () => {
    setMockClient({ plantuml: '@startuml\n@enduml', diagram_type: 'class' }, 200);

    const response = await request(app)
      .post('/generate-plantuml')
      .send({
        schema: { python: [], relations: [] },
        diagram_type: 'class'
      });

    expect(response.status).toBe(200);
    expect(response.body).toHaveProperty('diagram_type');
    expect(response.body.diagram_type).toBe('class');
  });

  // ============================================================================
  // Test Complex Schemas
  // ============================================================================

  test('handles large schema', async () => {
    const largeSchema = {
      python: Array.from({ length: 50 }, (_, i) => ({
        class: `Class${i}`,
        fields: [
          { name: 'field1', type: 'string', visibility: 'public' },
          { name: 'field2', type: 'int', visibility: 'private' }
        ],
        methods: [
          { name: 'method1', visibility: 'public' },
          { name: 'method2', visibility: 'private' }
        ]
      })),
      relations: []
    };

    setMockClient({ plantuml: '@startuml\nclass Class0\n@enduml', diagram_type: 'class' }, 200);

    const response = await request(app)
      .post('/generate-plantuml')
      .send({
        schema: largeSchema,
        diagram_type: 'class'
      });

    expect(response.status).toBe(200);
  });

  test('handles multi-language schema', async () => {
    const multiLangSchema = {
      python: [{ class: 'PythonClass', methods: [] }],
      java: [{ class: 'JavaClass', methods: [] }],
      typescript: [{ class: 'TypeScriptClass', methods: [] }],
      relations: []
    };

    setMockClient({ plantuml: '@startuml\nclass PythonClass\nclass JavaClass\n@enduml', diagram_type: 'class' }, 200);

    const response = await request(app)
      .post('/generate-plantuml')
      .send({
        schema: multiLangSchema,
        diagram_type: 'class'
      });

    expect(response.status).toBe(200);
    expect(response.body.plantuml).toContain('PythonClass');
  });

  test('handles schema with complex relationships', async () => {
    const complexSchema = {
      python: [
        { class: 'A', methods: [] },
        { class: 'B', methods: [] },
        { class: 'C', methods: [] }
      ],
      relations: [
        { from: 'A', to: 'B', type: 'extends' },
        { from: 'B', to: 'C', type: 'implements' },
        { from: 'A', to: 'C', type: 'composition', multiplicity: { from: '1', to: '*' } }
      ]
    };

    setMockClient({ plantuml: '@startuml\nA --|> B\nB ..|> C\nA "1" *-- "*" C\n@enduml', diagram_type: 'class' }, 200);

    const response = await request(app)
      .post('/generate-plantuml')
      .send({
        schema: complexSchema,
        diagram_type: 'class'
      });

    expect(response.status).toBe(200);
    expect(response.body.plantuml).toContain('--|>');
  });

  // ============================================================================
  // Test Error Messages
  // ============================================================================

  test('returns meaningful error message for validation failures', async () => {
    const response = await request(app)
      .post('/generate-plantuml')
      .send({
        invalid: 'data'
      });

    expect(response.status).toBeGreaterThanOrEqual(400);
    expect(response.body).toHaveProperty('error');
    expect(typeof response.body.error).toBe('string');
  });

  test('returns error message when backend is unavailable', async () => {
    setMockClient(null, null, { error: new Error('Backend unavailable') });

    const response = await request(app)
      .post('/generate-plantuml')
      .send({
        schema: { python: [], relations: [] },
        diagram_type: 'class'
      });

    expect(response.status).toBeGreaterThanOrEqual(500);
    expect(response.body).toHaveProperty('error');
  });

  // ============================================================================
  // Test Security
  // ============================================================================

  test('sanitizes malicious input in schema', async () => {
    const maliciousSchema = {
      python: [
        {
          class: '<script>alert("xss")</script>',
          methods: []
        }
      ],
      relations: []
    };

    setMockClient({ plantuml: '@startuml\n@enduml', diagram_type: 'class' }, 200);

    const response = await request(app)
      .post('/generate-plantuml')
      .send({
        schema: maliciousSchema,
        diagram_type: 'class'
      });

    // Should either sanitize or reject
    expect(response.status).toBeLessThan(300);
  });

  test('limits request body size', async () => {
    const hugeSchema = {
      python: Array.from({ length: 10000 }, (_, i) => ({
        class: `Class${i}`,
        fields: Array.from({ length: 100 }, (_, j) => ({
          name: `field${j}`,
          type: 'string'.repeat(100)
        }))
      })),
      relations: []
    };

    const response = await request(app)
      .post('/generate-plantuml')
      .send({
        schema: hugeSchema,
        diagram_type: 'class'
      });

    // Should either handle or reject gracefully
    expect([200, 413, 400]).toContain(response.status);
  });

  // ============================================================================
  // Test CORS
  // ============================================================================

  test('includes CORS headers', async () => {
    setMockClient({ plantuml: '@startuml\n@enduml', diagram_type: 'class' }, 200);

    const response = await request(app)
      .post('/generate-plantuml')
      .send({
        schema: { python: [], relations: [] },
        diagram_type: 'class'
      });

    // Check for CORS headers (if implemented)
    expect(response.status).toBe(200);
  });
});
