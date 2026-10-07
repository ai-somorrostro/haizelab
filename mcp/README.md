# InfluxDB MCP (solo lectura)

Servidor Model Context Protocol con acceso de **solo lectura** a InfluxDB 2.9.1
(organización `haizenlab`, buckets `aire, meteo, trafico, aire_demo`).

- Servidor: `mludvig/influxdb-mcp` (PyPI `influxdb-mcp`, fijado a `mcp[cli]==1.9.0`).
  El oficial `influxdata/influxdb3-mcp-server` **no** funciona con InfluxDB 2.x.
- Servicio Docker: `influx-mcp` → `http://127.0.0.1:5001/mcp/`
- Autenticación: token dedicado `INFLUXDB_MCP_TOKEN` (lectura en los 4 buckets, sin escritura).
  Nunca usa los tokens admin ni `read-all`.
- Clientes: OpenCode (`opencode.json`) + Antigravity (`.agents/mcp_config.json`).

## 1. Requisitos previos

- Motor Docker en marcha:
  ```bash
  docker info
  # si falla:
  sudo systemctl start docker
  ```
- Existe `.env` con (valores distintos, largos y aleatorios):
  ```
  INFLUXDB_ADMIN_PASSWORD=<mín 16 caracteres, sin espacios ni #/$ comillas>
  INFLUXDB_ADMIN_TOKEN=<64 caracteres hex, con: openssl rand -hex 32>
  NODE_RED_CREDENTIAL_SECRET=<64 caracteres hex, se genera una vez y no se cambia>
  ```
- Pila levantada y sana:
  ```bash
  docker compose up -d
  docker compose ps
  # haizelab_influxdb -> healthy, haizelab_influxdb_setup -> Exited (0)
  ```

## 2. Token MCP (una sola vez)

Crea la credencial `mcp-read-only: lectura 4 buckets solo MCP`.

```bash
set -a; source .env; set +a
HOST="http://localhost:8086"
ID_AIRE=$(docker exec haizelab_influxdb influx bucket find --name aire --org "$INFLUXDB_ORG" --host "$HOST" --token "$INFLUXDB_ADMIN_TOKEN" --hide-headers | cut -f1)
ID_METEO=$(docker exec haizelab_influxdb influx bucket find --name meteo --org "$INFLUXDB_ORG" --host "$HOST" --token "$INFLUXDB_ADMIN_TOKEN" --hide-headers | cut -f1)
ID_TRAFICO=$(docker exec haizelab_influxdb influx bucket find --name trafico --org "$INFLUXDB_ORG" --host "$HOST" --token "$INFLUXDB_ADMIN_TOKEN" --hide-headers | cut -f1)
ID_DEMO=$(docker exec haizelab_influxdb influx bucket find --name aire_demo --org "$INFLUXDB_ORG" --host "$HOST" --token "$INFLUXDB_ADMIN_TOKEN" --hide-headers | cut -f1)

NEW_TOKEN=$(docker exec haizelab_influxdb influx auth create \
  --org "$INFLUXDB_ORG" \
  --description "mcp-read-only: lectura 4 buckets solo MCP" \
  --read-bucket "$ID_AIRE" --read-bucket "$ID_METEO" \
  --read-bucket "$ID_TRAFICO" --read-bucket "$ID_DEMO" \
  --host "$HOST" --token "$INFLUXDB_ADMIN_TOKEN" --hide-headers | cut -f3)

# guardar (añadir una vez, nunca subir .env a git):
printf "\nINFLUXDB_MCP_TOKEN=%s\n" "$NEW_TOKEN" >> .env
chmod 600 .env
```

Verificación (lectura `200` OK, escritura `403` denegada es lo esperado):

```bash
set -a; source .env; set +a
curl -s -o /dev/null -w "READ=%{http_code}\n" http://127.0.0.1:8086/api/v2/buckets -H "Authorization: Token $INFLUXDB_MCP_TOKEN"
curl -s -o /dev/null -w "WRITE=%{http_code}\n" -X POST "http://127.0.0.1:8086/api/v2/write?org=haizenlab&bucket=meteo&precision=s" \
  -H "Authorization: Token $INFLUXDB_MCP_TOKEN" --data-binary "test,tag=x field=1i"
```

## 3. Servicio

`docker-compose.yml` → servicio `influx-mcp` (construido desde `mcp/Dockerfile`):

```yaml
influx-mcp:
  build: ./mcp
  ports: ["127.0.0.1:5001:5001"]
  environment:
    INFLUXDB_HOST: influxdb
    INFLUXDB_PORT: 8086
    INFLUXDB_ORG: ${INFLUXDB_ORG}
    INFLUXDB_TOKEN: ${INFLUXDB_MCP_TOKEN}
```

> `mcp[cli]==1.9.0` está fijado a propósito: sin fijar, `mcp 2.x` elimina
> `mcp.server.fastmcp` y las `1.x` nuevas quitan `FastMCP(description=...)`;
> en ambos casos el servidor se cae al arrancar.

```bash
docker compose up -d --build influx-mcp
docker compose ps influx-mcp   # Up (healthy)
docker logs haizelab_influx_mcp --tail 10
# Connected to InfluxDB at http://influxdb:8086
# Uvicorn running on http://0.0.0.0:5001
```

## 4. Clientes

Endpoint común: `http://127.0.0.1:5001/mcp/`

OpenCode (`opencode.json`):

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "influxdb": {
      "type": "remote",
      "url": "http://127.0.0.1:5001/mcp/",
      "enabled": true
    }
  }
}
```

Antigravity (por proyecto `.agents/mcp_config.json`, o global en
`~/.gemini/config/mcp_config.json`):

```json
{
  "mcpServers": {
    "influxdb": { "serverUrl": "http://127.0.0.1:5001/mcp/" }
  }
}
```

Reinicia el cliente tras editar y comprueba que `influxdb` aparece en su lista
de servidores MCP (OpenCode: `opencode mcp list`; Antigravity: `…` → MCP Servers → Manage → Refresh).

## 5. Uso

Herramientas: `test_connection, list_buckets, list_measurements(bucket), execute_flux_query(query)`.

Ejemplos de peticiones:

```
test_connection usando influxdb
list_buckets usando influxdb
lista las measurements del bucket meteo usando influxdb
```

Ejemplos Flux (`execute_flux_query`):

```flux
from(bucket:"meteo") |> range(start:-1h) |> limit(n:5)
from(bucket:"aire_demo") |> range(start:-1h) |> limit(n:5)
from(bucket:"trafico") |> range(start:-1h) |> limit(n:5)
import "influxdata/influxdb/schema"
schema.measurements(bucket:"aire")
```

Comprobación sin cliente:

```bash
curl -X POST http://127.0.0.1:5001/mcp/ \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'
# -> "serverInfo":{"name":"influxdb-mcp",...}
```

## 6. Parar / problemas

```bash
docker compose stop          # pausa, conserva datos
docker compose down          # para + elimina contenedores, conserva datos y tokens
# docker compose down -v     # PELIGRO: borra todos los datos de InfluxDB y los tokens
```

| Síntoma | Causa / solución |
|---|---|
| `influxdb is unhealthy` | Falta `.env` → `cp .env.example .env`, rellenar secretos, `docker compose down && docker compose up -d --build` |
| Aviso `INFLUXDB_MCP_TOKEN is not set` | Token no guardado en `.env` → repetir sección 2 |
| Log MCP `No module named 'mcp.server.fastmcp'` | `mcp 2.x` sin fijar → mantener `mcp[cli]==1.9.0` en `mcp/Dockerfile` y reconstruir |
| Log MCP `unexpected keyword argument 'description'` | `mcp 1.x` demasiado nueva → mismo fijado + reconstruir |
| `GET /mcp/ 406` en logs | Normal (la sonda GET no es MCP); el healthcheck usa POST `ping`, el servicio sigue `healthy` |
| Cliente `connection refused` en `:5001` | `docker compose ps influx-mcp` debe estar `Up (healthy)`; si no: `docker compose up -d --build influx-mcp` |

## 7. Seguridad

- `.env` está en `.gitignore` (`chmod 600`), nunca se suben tokens a git.
- `INFLUXDB_MCP_TOKEN` es de solo lectura en 4 buckets; para rotarlo:
  `influx auth delete --id <ID>` + repetir sección 2.
- El puerto `5001` solo escucha en `127.0.0.1`; no exponerlo a internet.
