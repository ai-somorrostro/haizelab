// scripts/influx_iframe_proxy.js
// Proxy inverso seguro para InfluxDB v2 en modo local.
// Protección defensiva:
//   - Bloqueo estricto de métodos destructivos (DELETE, PUT, PATCH).
//   - Bloqueo de rutas de administración (/api/v2/setup, /api/v2/delete, /api/v2/authorizations, /api/v2/users).
//   - Sin contraseñas hardcodeadas ni inyección de tokens de superadministrador.

const http = require('http');
const fs = require('fs');
const path = require('path');

let readToken = '';

try {
  const envPath = path.join(__dirname, '..', '.env');
  if (fs.existsSync(envPath)) {
    const envContent = fs.readFileSync(envPath, 'utf8');
    for (const line of envContent.split('\n')) {
      const trimmed = line.trim();
      if (trimmed.startsWith('INFLUXDB_READ_TOKEN=')) readToken = trimmed.split('=')[1].trim();
    }
  }
} catch (err) {
  console.warn('[Proxy] Advertencia leyendo .env:', err.message);
}

const INFLUX_HOST = '127.0.0.1';
const INFLUX_PORT = 8086;
const PROXY_PORT = process.env.INFLUX_PROXY_PORT || 8085;

const RUTAS_PROHIBIDAS = [
  '/api/v2/setup',
  '/api/v2/delete',
  '/api/v2/authorizations',
  '/api/v2/users',
  '/api/v2/orgs',
  '/api/v2/buckets'
];

const server = http.createServer((req, res) => {
  const method = (req.method || 'GET').toUpperCase();
  const urlPath = req.url ? req.url.split('?')[0] : '/';

  // 1. Bloqueo de métodos destructivos
  if (method === 'DELETE' || method === 'PUT' || method === 'PATCH') {
    res.writeHead(403, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Operacion no permitida por politica de seguridad.' }));
    return;
  }

  // 2. Bloqueo de rutas administrativas
  const esRutaProhibida = RUTAS_PROHIBIDAS.some(p => urlPath.startsWith(p));
  if (esRutaProhibida && method !== 'GET') {
    res.writeHead(403, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Acceso denegado a rutas administrativas.' }));
    return;
  }

  const headers = { ...req.headers };
  headers.host = `${INFLUX_HOST}:${INFLUX_PORT}`;

  // 3. Token de lectura exclusivo para consultas
  if (urlPath.startsWith('/api/v2/query') && !headers['authorization'] && readToken) {
    headers['authorization'] = `Token ${readToken}`;
  }

  const proxyReq = http.request({
    hostname: INFLUX_HOST,
    port: INFLUX_PORT,
    path: req.url,
    method: req.method,
    headers: headers
  }, (proxyRes) => {
    const resHeaders = { ...proxyRes.headers };

    delete resHeaders['x-frame-options'];
    resHeaders['x-content-type-options'] = 'nosniff';

    if (resHeaders['set-cookie']) {
      resHeaders['set-cookie'] = resHeaders['set-cookie'].map((c) => {
        let mod = c.replace(/SameSite=(Strict|Lax)/gi, 'SameSite=None');
        if (!mod.includes('SameSite=')) mod += '; SameSite=None';
        if (!mod.includes('Secure')) mod += '; Secure';
        return mod;
      });
    }

    res.writeHead(proxyRes.statusCode, resHeaders);
    proxyRes.pipe(res);
  });

  proxyReq.on('error', (err) => {
    console.error('[Proxy] Error en peticion:', err.message);
    res.writeHead(502, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Servicio InfluxDB no disponible temporalmente.' }));
  });

  req.pipe(proxyReq);
});

server.listen(PROXY_PORT, '127.0.0.1', () => {
  console.log(`[Proxy InfluxDB Seguro] Escuchando en 127.0.0.1:${PROXY_PORT} -> http://${INFLUX_HOST}:${INFLUX_PORT}`);
});
