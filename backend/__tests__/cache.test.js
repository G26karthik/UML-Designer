import request from 'supertest';
import { vi } from 'vitest';

describe('Caching behavior', () => {
  let app;
  let post;
  beforeEach(async () => {
    vi.resetModules();
    process.env.CACHE_TTL_MS = '60000';
    process.env.DISK_CACHE_TTL_MS = '1';
    const mod = await import('../index.js');
    app = mod.default();
    post = vi.fn();
    mod.__setHttpClient({ post });
  });

  it('returns cached result for the same URL without calling parser again', async () => {
    const url = 'https://github.com/testuser/testrepo';

  post.mockResolvedValueOnce({
      status: 200,
      data: {
        schema: {
          java: [],
          python: [],
          relations: [],
          endpoints: [],
          patterns: [],
          layers: [],
          meta: {
            commit: 'abc123',
            classes_found: 0,
            files_scanned: 1,
            languages: [],
            system: 'test'
          }
        }
      },
    });

    const first = await request(app).post('/analyze').send({ githubUrl: url });
    expect(first.status).toBe(200);
    expect(first.body.schema.meta).toHaveProperty('commit', 'abc123');
  expect(post).toHaveBeenCalledTimes(1);

    const second = await request(app).post('/analyze').send({ githubUrl: url });
    expect(second.status).toBe(200);
    expect(second.body.schema.meta).toHaveProperty('commit', 'abc123');
  expect(post).toHaveBeenCalledTimes(1);
  });
});
