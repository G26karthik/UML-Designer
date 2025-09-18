import request from 'supertest';

describe('Caching behavior', () => {
  let app;
  let post;
  beforeEach(async () => {
    jest.resetModules();
    process.env.CACHE_TTL_MS = '60000';
    process.env.DISK_CACHE_TTL_MS = '1';
    const mod = await import('../index.js');
    app = mod.default;
    post = jest.fn();
    mod.__setHttpClient({ post });
  });

  it('returns cached result for the same URL without calling parser again', async () => {
    const url = 'https://github.com/testuser/testrepo';

  post.mockResolvedValueOnce({
      status: 200,
      data: { meta: { commit: 'abc123' }, schema: { ok: true } },
    });

    const first = await request(app).post('/analyze').send({ githubUrl: url });
    expect(first.status).toBe(200);
    expect(first.body).toHaveProperty('meta.commit', 'abc123');
  expect(post).toHaveBeenCalledTimes(1);

    const second = await request(app).post('/analyze').send({ githubUrl: url });
    expect(second.status).toBe(200);
    expect(second.body).toHaveProperty('meta.commit', 'abc123');
  expect(post).toHaveBeenCalledTimes(1);
  });
});
