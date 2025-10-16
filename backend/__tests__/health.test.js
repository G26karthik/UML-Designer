import request from 'supertest';

describe('GET /health', () => {
  it('should return ok true', async () => {
  const mod = await import('../index.js');
  const app = mod.default();
  const res = await request(app).get('/health');
    expect(res.statusCode).toBe(200);
    expect(res.body).toHaveProperty('ok', true);
  });
});
