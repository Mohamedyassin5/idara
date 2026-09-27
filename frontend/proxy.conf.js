// Dev proxy: /api/* -> AgentOS.
// Docker compose publishes AgentOS on :8000, while `python -m app.main` listens on :7777.
// The target is BACKEND_URL when set, otherwise the first of these ports that answers at startup.
const { spawnSync } = require('node:child_process');

const CANDIDATE_PORTS = [8000, 7777];

function isListening(port) {
  const probe = `
    const s = require('node:net').connect({ host: 'localhost', port: ${port} });
    s.on('connect', () => { s.destroy(); process.exit(0); });
    s.on('error', () => process.exit(1));
    setTimeout(() => process.exit(1), 800);`;
  return spawnSync(process.execPath, ['-e', probe]).status === 0;
}

function pickTarget() {
  if (process.env.BACKEND_URL) return process.env.BACKEND_URL;
  const port = CANDIDATE_PORTS.find(isListening) ?? CANDIDATE_PORTS[0];
  console.log(`[proxy] /api -> http://localhost:${port}` + (isListening(port) ? '' : ' (no backend detected yet: start it, then restart ng serve)'));
  return `http://localhost:${port}`;
}

module.exports = {
  '/api': {
    target: pickTarget(),
    secure: false,
    changeOrigin: true,
    pathRewrite: { '^/api': '' },
    timeout: 180000,
    proxyTimeout: 180000,
  },
};
