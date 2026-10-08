// influx_proxy/index.js
// Proxy inverso transparente para InfluxDB v2 que habilita soporte de iframes
// en aplicaciones web modernas (SameSite=None, Secure, Partitioned y bypass de auth para API).

const http = require('http');

const adminUser = process.env.INFLUXDB_ADMIN_USER || 'admin';
const adminPass = process.env.INFLUXDB_ADMIN_PASSWORD || 'haizelab2024seguro';
const adminToken = process.env.INFLUXDB_ADMIN_TOKEN || '';

const INFLUX_HOST = process.env.INFLUX_HOST || 'influxdb';
const INFLUX_PORT = parseInt(process.env.INFLUX_PORT || '8086', 10);
const PROXY_PORT = parseInt(process.env.PROXY_PORT || '8085', 10);

let cachedSessionCookie = '';
let lastCookieFetch = 0;

function refrescarSesionAdmin() {
  const authHeader = 'Basic ' + Buffer.from(`${adminUser}:${adminPass}`).toString('base64');
  const req = http.request({
    hostname: INFLUX_HOST,
    port: INFLUX_PORT,
    path: '/api/v2/signin',
    method: 'POST',
    headers: {
      'Authorization': authHeader,
      'Content-Length': 0
    }
  }, (res) => {
    const cookies = res.headers['set-cookie'];
    if (cookies) {
      for (const c of cookies) {
        if (c.includes('influxdb-oss-session=')) {
          const match = c.match(/influxdb-oss-session=([^;]+)/);
          if (match) {
            cachedSessionCookie = match[1];
            lastCookieFetch = Date.now();
            console.log('[InfluxProxy] Sesión admin renovada con éxito.');
          }
        }
      }
    }
  });
  req.on('error', (e) => console.error('[InfluxProxy] Error renovando sesión admin:', e.message));
  req.end();
}

// Renovar periódicamente
refrescarSesionAdmin();
setInterval(refrescarSesionAdmin, 6 * 3600 * 1000);

const server = http.createServer((req, res) => {
  const clientCookies = req.headers['cookie'] || '';
  const tieneSesionCookie = clientCookies.includes('influxdb-oss-session=');
  const headers = { ...req.headers };

  headers.host = `${INFLUX_HOST}:${INFLUX_PORT}`;

  // Si la petición va a la API y el navegador bloqueó las cookies en el iframe, inyectamos auth de admin
  if (req.url.startsWith('/api/v2/') && !tieneSesionCookie && !headers['authorization']) {
    if (adminToken) {
      headers['authorization'] = `Token ${adminToken}`;
    } else if (cachedSessionCookie) {
      headers['cookie'] = clientCookies ? `${clientCookies}; influxdb-oss-session=${cachedSessionCookie}` : `influxdb-oss-session=${cachedSessionCookie}`;
    }
  }

  const proxyReq = http.request({
    hostname: INFLUX_HOST,
    port: INFLUX_PORT,
    path: req.url,
    method: req.method,
    headers: headers
  }, (proxyRes) => {
    const resHeaders = { ...proxyRes.headers };

    // Eliminar protecciones anti-iframe y permitir cross-origin
    delete resHeaders['x-frame-options'];
    resHeaders['access-control-allow-origin'] = '*';
    resHeaders['access-control-allow-credentials'] = 'true';

    // Reescribir cookies para habilitar Third-Party Cookies en iframes
    if (resHeaders['set-cookie']) {
      resHeaders['set-cookie'] = resHeaders['set-cookie'].map((c) => {
        let mod = c.replace(/SameSite=(Strict|Lax)/gi, 'SameSite=None');
        if (!mod.includes('SameSite=')) mod += '; SameSite=None';
        if (!mod.includes('Secure')) mod += '; Secure';
        if (!mod.includes('Partitioned')) mod += '; Partitioned';
        mod = mod.replace(/Path=\/api\//gi, 'Path=/');
        return mod;
      });
    }

    // Auto-login: inyectar cookie admin si accede a páginas HTML sin sesión previa
    const isHtmlRoute = req.url === '/' || req.url.startsWith('/signin') || req.url.startsWith('/orgs');
    if (isHtmlRoute && !tieneSesionCookie && cachedSessionCookie) {
      const autoCookie = `influxdb-oss-session=${cachedSessionCookie}; Path=/; SameSite=None; Secure; Partitioned; Max-Age=2592000; HttpOnly`;
      if (resHeaders['set-cookie']) {
        if (!resHeaders['set-cookie'].some(c => c.includes('influxdb-oss-session='))) {
          resHeaders['set-cookie'].push(autoCookie);
        }
      } else {
        resHeaders['set-cookie'] = [autoCookie];
      }
    }

    res.writeHead(proxyRes.statusCode, resHeaders);
    proxyRes.pipe(res);
  });

  proxyReq.on('error', (err) => {
    console.error('[InfluxProxy] Error reenviando petición:', err.message);
    res.writeHead(502, { 'Content-Type': 'text/plain' });
    res.end('Bad Gateway: ' + err.message);
  });

  req.pipe(proxyReq);
});

server.listen(PROXY_PORT, '0.0.0.0', () => {
  console.log(`[InfluxProxy] Escuchando en 0.0.0.0:${PROXY_PORT} -> http://${INFLUX_HOST}:${INFLUX_PORT}`);
});
