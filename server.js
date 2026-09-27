// Tiny production server for Azure App Service (Node): serves the Angular build and
// proxies /api/* to the backend with the /api prefix removed (same as proxy.conf.js in dev).
// No dependencies: only Node built-ins.
const http = require('node:http');
const https = require('node:https');
const fs = require('node:fs');
const path = require('node:path');

const PORT = process.env.PORT || 8080;
const BACKEND_URL = (process.env.BACKEND_URL || 'http://localhost:7777').replace(/\/$/, '');
const ROOT = path.join(__dirname, 'public');

const TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.ico': 'image/x-icon',
  '.woff2': 'font/woff2',
  '.txt': 'text/plain; charset=utf-8',
};

function proxy(req, res) {
  const target = new URL(BACKEND_URL + req.url.replace(/^\/api/, '') || '/');
  const client = target.protocol === 'https:' ? https : http;
  const upstream = client.request(
    target,
    { method: req.method, headers: { ...req.headers, host: target.host }, timeout: 180000 },
    (up) => {
      res.writeHead(up.statusCode || 502, up.headers);
      up.pipe(res); // streamed as-is, so agent responses keep streaming
    },
  );
  upstream.on('timeout', () => upstream.destroy(new Error('upstream timeout')));
  upstream.on('error', () => {
    if (!res.headersSent) res.writeHead(502, { 'content-type': 'application/json' });
    res.end(JSON.stringify({ detail: 'Backend unreachable' }));
  });
  req.pipe(upstream);
}

function serveStatic(req, res) {
  const clean = decodeURIComponent(req.url.split('?')[0]);
  let file = path.normalize(path.join(ROOT, clean));
  if (!file.startsWith(ROOT)) {
    res.writeHead(403).end();
    return;
  }
  if (!fs.existsSync(file) || fs.statSync(file).isDirectory()) file = path.join(ROOT, 'index.html'); // SPA fallback
  const headers = { 'content-type': TYPES[path.extname(file)] || 'application/octet-stream' };
  if (/\.(js|css|woff2|svg|png|jpg)$/.test(file) && /-[A-Z0-9]{8}\./.test(file)) {
    headers['cache-control'] = 'public, max-age=31536000, immutable'; // hashed build assets
  }
  res.writeHead(200, headers);
  fs.createReadStream(file).pipe(res);
}

http
  .createServer((req, res) => (req.url.startsWith('/api/') ? proxy(req, res) : serveStatic(req, res)))
  .listen(PORT, () => console.log(`Idara frontend on :${PORT}, /api -> ${BACKEND_URL}`));
