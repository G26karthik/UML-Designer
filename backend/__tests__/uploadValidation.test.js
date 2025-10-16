import request from 'supertest';
import fs from 'fs';
import os from 'os';
import path from 'path';

describe('Upload validation', () => {
  let app;
  beforeAll(async () => {
    const mod = await import('../index.js');
    app = mod.default();
  });

  it('rejects non-zip file extension', async () => {
    const buf = Buffer.from('hello');
    const res = await request(app)
      .post('/analyze')
      .attach('repoZip', buf, { filename: 'notzip.txt', contentType: 'text/plain' });
    expect(res.statusCode).toBe(400);
    expect(res.body?.success).toBe(false);
  });

  it('rejects bad magic bytes even if .zip extension', async () => {
    const buf = Buffer.from('NOTAZIP');
    const res = await request(app)
      .post('/analyze')
      .attach('repoZip', buf, { filename: 'fake.zip', contentType: 'application/zip' });
    expect(res.statusCode).toBe(400);
    expect(res.body?.success).toBe(false);
  });
});
