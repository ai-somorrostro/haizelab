// scripts/influx_iframe_proxy.js
// Proxy inverso transparente para InfluxDB v2 que habilita soporte completo
// en iframes cross-domain (Third-Party Cookies, SameSite=None, Auto-login Admin)

const http = require('http');
const fs = require('fs');
const path = require('path');

// Cargar variables de entorno desde .env de haizelab si están disponibles
let adminUser = 'admin';
let adminPass = 'haizelab2024seguro';
let adminToken = '';

try {
  const envPath = path.join(__dirname, '..', '.env');
  if (fs.existsSync(envPath)) {
    const envContent = fs.readFileSync(envPath, 'utf8');
    for (const line of envContent.split('\n')) {
      const trimmed = line.trim();
      if (trimmed.startsWith('INFLUXDB_ADMIN_USER=')) adminUser = trimmed.split('=')[1].trim();
      if (trimmed.startsWith('INFLUXDB_ADMIN_PASSWORD=')) adminPass = trimmed.split('=')[1].trim();
      if (trimmed.startsWith('INFLUXDB_ADMIN_TOKEN=')) adminToken = trimmed.split('=')[1].trim();
    }
  }
} catch (err) {
  console.warn('[Proxy] Advertencia leyendo .env:', err.message);
}

const INFLUX_HOST = '127.0.0.1';
const INFLUX_PORT = 8086;
const PROXY_PORT = process.env.INFLUX_PROXY_PORT || 8085;

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
            console.log('[Proxy] Sesión de InfluxDB admin renovada con éxito.');
          }
        }
      }
    }
  });
  req.on('error', (e) => console.error('[Proxy] Error renovando sesión admin:', e.message));
  req.end();
}

// Renovar sesión al inicio y cada 12 horas
refrescarSesionAdmin();
setInterval(refrescarSesionAdmin, 12 * 3600 * 1000);

const server = http.createServer((req, res) => {
  const clientCookies = req.headers['cookie'] || '';
  const tieneSesionCookie = clientCookies.includes('influxdb-oss-session=');
  const headers = { ...req.headers };

  // Eliminar host para que no interfiera en la petición hacia el backend
  headers.host = `${INFLUX_HOST}:${INFLUX_PORT}`;

  // Si la petición va a la API y no tiene autorización ni cookie de sesión,
  // inyectamos la autorización de admin para navegadores que bloquean cookies en iframes
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

    // Permitir iframe sin restricciones
    delete resHeaders['x-frame-options'];
    resHeaders['access-control-allow-origin'] = '*';
    resHeaders['access-control-allow-credentials'] = 'true';

    // Reescribir cookies para soporte Third-Party en iframes (SameSite=None, Secure, Partitioned)
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

    // Si el cliente accede a una página HTML principal (como / o /signin) y no tiene cookie,
    // enviamos proactivamente la cookie de sesión admin para auto-login transparente
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
    console.error('[Proxy] Error reenviando petición:', err.message);
    res.writeHead(502, { 'Content-Type': 'text/plain' });
    res.end('Bad Gateway: ' + err.message);
  });

  req.pipe(proxyReq);
});

server.listen(PROXY_PORT, '0.0.0.0', () => {
  console.log(`[Proxy InfluxDB iframe] Escuchando en http://0.0.0.0:${PROXY_PORT} -> http://${INFLUX_HOST}:${INFLUX_PORT}`);
});
