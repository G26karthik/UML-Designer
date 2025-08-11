import request from 'supertest';

describe('GET /health', () => {
  it('should return ok true', async () => {
  const mod = await import('../index.js');
  const res = await request(mod.default).get('/health');
    expect(res.statusCode).toBe(200);
    expect(res.body).toHaveProperty('ok', true);
  });
});
