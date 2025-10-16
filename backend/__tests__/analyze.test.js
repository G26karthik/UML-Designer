import request from 'supertest';

describe('POST /analyze', () => {
  it('should return 400 if no repo provided', async () => {
  const mod = await import('../index.js');
  const app = mod.default();
  const res = await request(app).post('/analyze').send({});
    expect(res.statusCode).toBe(400);
  });
});
