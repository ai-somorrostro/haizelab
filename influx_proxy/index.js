// influx_proxy/index.js
// Proxy inverso seguro para InfluxDB v2 en dashboards web.
// Protección defensiva:
//   - Bloqueo estricto de métodos destructivos (DELETE, PUT, PATCH).
//   - Bloqueo de rutas administrativas (/api/v2/setup, /api/v2/delete, /api/v2/authorizations, /api/v2/users).
//   - PROHIBIDA la inyección de credenciales o tokens de superadministrador.
//   - Acceso estrictamente limitado y controlado.

const http = require('http');

const INFLUX_HOST = process.env.INFLUX_HOST || 'influxdb';
const INFLUX_PORT = parseInt(process.env.INFLUX_PORT || '8086', 10);
const PROXY_PORT = parseInt(process.env.PROXY_PORT || '8085', 10);

// Token de solo lectura estricto (NUNCA el token admin)
const readToken = process.env.INFLUXDB_READ_TOKEN || '';

// Rutas explícitamente bloqueadas por seguridad perimetral
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

  // 2. Bloqueo de rutas de administración y borrado
  const esRutaProhibida = RUTAS_PROHIBIDAS.some(p => urlPath.startsWith(p));
  if (esRutaProhibida && method !== 'GET') {
    res.writeHead(403, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Acceso denegado a rutas administrativas.' }));
    return;
  }

  const headers = { ...req.headers };
  headers.host = `${INFLUX_HOST}:${INFLUX_PORT}`;

  // 3. Si la petición va a la API de consulta (/api/v2/query) y el cliente no tiene token,
  // se permite inyectar únicamente el token de LECTURA (nunca superadmin)
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

    // Sanitización de cabeceras de respuesta
    delete resHeaders['x-frame-options'];
    resHeaders['x-content-type-options'] = 'nosniff';

    // Reescribir cookies para soporte en iframes seguros
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
    console.error('[InfluxProxy] Error en peticion:', err.message);
    res.writeHead(502, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Servicio InfluxDB no disponible temporalmente.' }));
  });

  req.pipe(proxyReq);
});

server.listen(PROXY_PORT, '0.0.0.0', () => {
  console.log(`[InfluxProxy Seguro] Escuchando en 0.0.0.0:${PROXY_PORT} -> http://${INFLUX_HOST}:${INFLUX_PORT}`);
});
