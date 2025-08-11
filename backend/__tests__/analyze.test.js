import request from 'supertest';

describe('POST /analyze', () => {
  it('should return 400 if no repo provided', async () => {
  const mod = await import('../index.js');
  const res = await request(mod.default).post('/analyze').send({});
    expect(res.statusCode).toBe(400);
  });
});
