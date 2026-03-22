const express = require('express');
const path = require('path');
const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());

// Serve the static webpage from public/
app.use(express.static(path.join(__dirname, 'public')));

// Health check (used by Docker HEALTHCHECK + GitHub Actions)
app.get('/health', (req, res) => {
  res.status(200).json({
    status: 'healthy',
    uptime: process.uptime(),
    timestamp: new Date().toISOString(),
  });
});

// Readiness probe
app.get('/ready', (req, res) => res.json({ ready: true }));

// Build info — read by the webpage via fetch('/api/info')
app.get('/api/info', (req, res) => {
  res.json({
    app: 'cicd-demo',
    version: process.env.BUILD_VERSION || 'dev',
    buildDate: process.env.BUILD_DATE || null,
    env: process.env.NODE_ENV || 'development',
    node: process.version,
  });
});

// Catch-all: serve index.html for any unmatched route
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

const server = app.listen(PORT, () => {
  console.log(`Server running on http://0.0.0.0:${PORT}`);
  console.log(`Version: ${process.env.BUILD_VERSION || 'dev'}`);
  console.log(`Env:     ${process.env.NODE_ENV || 'development'}`);
});

process.on('SIGTERM', () => {
  console.log('SIGTERM — shutting down gracefully...');
  server.close(() => process.exit(0));
});

module.exports = app;
