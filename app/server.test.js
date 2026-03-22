const request = require('supertest');
const app = require('./server');

describe('API Endpoints', () => {
  it('GET /health → 200 healthy', async () => {
    const res = await request(app).get('/health');
    expect(res.statusCode).toBe(200);
    expect(res.body.status).toBe('healthy');
    expect(res.body).toHaveProperty('uptime');
  });

  it('GET /ready → 200 ready', async () => {
    const res = await request(app).get('/ready');
    expect(res.statusCode).toBe(200);
    expect(res.body.ready).toBe(true);
  });

  it('GET /api/info → app metadata', async () => {
    const res = await request(app).get('/api/info');
    expect(res.statusCode).toBe(200);
    expect(res.body.app).toBe('cicd-demo');
    expect(res.body).toHaveProperty('version');
    expect(res.body).toHaveProperty('node');
  });

  it('GET / → serves HTML webpage', async () => {
    const res = await request(app).get('/');
    expect(res.statusCode).toBe(200);
    expect(res.headers['content-type']).toMatch(/html/);
  });
});
