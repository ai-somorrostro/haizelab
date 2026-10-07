# InfluxDB MCP (solo lectura)

Servidor Model Context Protocol con acceso de **solo lectura** a InfluxDB 2.9.1
(organización `haizenlab`, buckets `aire, meteo, trafico, aire_demo`).

- Servidor: `mludvig/influxdb-mcp` (PyPI `influxdb-mcp`, fijado a `mcp[cli]==1.9.0`).
  El oficial `influxdata/influxdb3-mcp-server` **no** funciona con InfluxDB 2.x.
- Servicio Docker: `influx-mcp` → `http://127.0.0.1:5001/mcp/`
- Autenticación: token dedicado `INFLUXDB_MCP_TOKEN` (lectura en los 4 buckets, sin escritura),
  autogenerado por `influxdb_setup` (Token 4) junto al resto en `/tokens/tokens.env`.
  Nunca usa los tokens admin ni `read-all`. Override opcional vía `.env`.
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

## 2. Token MCP (automático)

Desde la versión con 4 tokens, `influxdb_setup` (`influxdb/init-influxdb.sh`)
crea la credencial `mcp-read-only: lectura 4 buckets solo MCP` junto a
`nodered-write`, `batch-write` y `read-all`, y la guarda como
`INFLUXDB_MCP_TOKEN` en el volumen `influxdb_tokens` (`/tokens/tokens.env`).
El servicio `influx-mcp` la carga vía `mcp/entrypoint.sh` sin pasos manuales.

- Instalación nueva: `docker compose up -d --build` → token creado solo.
  Verlo: `docker exec haizelab_influxdb cat /tokens/tokens.env` no funciona
  (el fichero vive en el volumen); usa:
  ```bash
  docker run --rm -v haizelab_influxdb_tokens:/tokens:ro alpine cat /tokens/tokens.env | cut -c1-30
  # o: docker compose exec influxdb influx auth find --org haizenlab
  ```
- Volumen antiguo (solo 3 tokens): reinicia `influxdb_setup` una vez;
  detecta que falta `INFLUXDB_MCP_TOKEN` y solo genera/añade ese token
  sin recrear buckets ni el resto:
  ```bash
  docker compose up -d influxdb_setup
  docker compose up -d --build influx-mcp
  ```
- Override manual opcional (no necesario): define `INFLUXDB_MCP_TOKEN=...`
  en `.env`; `mcp/entrypoint.sh` lo prefiere sobre el del volumen.

### Regeneración manual (solo rotación / depuración)

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
# override opcional (nunca subir .env a git):
printf "\nINFLUXDB_MCP_TOKEN=%s\n" "$NEW_TOKEN" >> .env
docker compose up -d --build influx-mcp
```

Verificación (lectura `200` OK, escritura `403` denegada es lo esperado):

```bash
MCP_TOKEN=$(docker run --rm -v haizelab_influxdb_tokens:/tokens:ro alpine sh -c '. /tokens/tokens.env; printf "%s" "$INFLUXDB_MCP_TOKEN"')
curl -s -o /dev/null -w "READ=%{http_code}\n" http://127.0.0.1:8086/api/v2/buckets -H "Authorization: Token $MCP_TOKEN"
curl -s -o /dev/null -w "WRITE=%{http_code}\n" -X POST "http://127.0.0.1:8086/api/v2/write?org=haizenlab&bucket=meteo&precision=s" \
  -H "Authorization: Token $MCP_TOKEN" --data-binary "test,tag=x field=1i"
```

## 3. Servicio

`docker-compose.yml` → servicio `influx-mcp` (construido desde `mcp/Dockerfile` + `mcp/entrypoint.sh`):

```yaml
influx-mcp:
  build: ./mcp
  ports: ["127.0.0.1:5001:5001"]
  depends_on:
    influxdb: { condition: service_healthy }
    influxdb_setup: { condition: service_completed_successfully }
  environment:
    INFLUXDB_HOST: influxdb
    INFLUXDB_PORT: 8086
    INFLUXDB_ORG: ${INFLUXDB_ORG}
    INFLUXDB_TOKEN: ${INFLUXDB_MCP_TOKEN:-} # vacio -> entrypoint carga desde /tokens/tokens.env
  volumes:
    - influxdb_tokens:/tokens:ro
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
| Log MCP `ERROR: ... esperando tokens` | `influxdb_setup` no terminó en `0` → `docker compose ps influxdb_setup`, `docker logs haizelab_influxdb_setup` |
| Log MCP `sin INFLUXDB_MCP_TOKEN` | Volumen antiguo sin Token 4 → `docker compose up -d influxdb_setup` (upgrade automático), luego `up -d --build influx-mcp` |
| Log MCP `No module named 'mcp.server.fastmcp'` | `mcp 2.x` sin fijar → mantener `mcp[cli]==1.9.0` en `mcp/Dockerfile` y reconstruir |
| Log MCP `unexpected keyword argument 'description'` | `mcp 1.x` demasiado nueva → mismo fijado + reconstruir |
| `GET /mcp/ 406` en logs | Normal (la sonda GET no es MCP); el healthcheck usa POST `ping`, el servicio sigue `healthy` |
| Cliente `connection refused` en `:5001` | `docker compose ps influx-mcp` debe estar `Up (healthy)`; si no: `docker compose up -d --build influx-mcp` |

## 7. Seguridad

- `.env` está en `.gitignore` (`chmod 600`), nunca se suben tokens a git.
- Los 4 tokens viven en el volumen `influxdb_tokens` (`/tokens/tokens.env`), no en git.
- `INFLUXDB_MCP_TOKEN` es de solo lectura en 4 buckets; para rotarlo:
  `influx auth delete --id <ID>` + recrear manual (sección 2) o borrar el token
  del fichero y reiniciar `influxdb_setup` para el upgrade automático.
- El puerto `5001` solo escucha en `127.0.0.1`; no exponerlo a internet.
