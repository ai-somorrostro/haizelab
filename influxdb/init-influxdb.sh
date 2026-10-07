#!/bin/sh
# influxdb/init-influxdb.sh
# =========================
# Se ejecuta en el contenedor efimero "influxdb_setup" despues de que influxdb
# este sano (depends_on: condition: service_healthy).
#
# Responsabilidades:
#   1. Crear los buckets: meteo, trafico, aire_demo (aire lo crea Docker)
#   2. Generar token escritura para Node-RED (solo meteo+trafico+aire_demo)
#   3. Generar token escritura carga historica (aire+meteo)
#   4. Generar token lectura para Grafana (todos los buckets)
#   5. Generar token lectura dedicado para MCP (todos los buckets, solo MCP)
#   6. Escribir los tokens en /tokens/tokens.env (volumen compartido)
#
# Si /tokens/tokens.env ya existe con los 4 tokens (reinicio sin -v),
# sale sin recrear nada. Si existe pero le falta INFLUXDB_MCP_TOKEN
# (volumen creado con una version anterior), solo genera y añade ese token.

set -eu

HOST="http://influxdb:8086"
ORG="${DOCKER_INFLUXDB_INIT_ORG}"
ADMIN_TOKEN="${DOCKER_INFLUXDB_INIT_ADMIN_TOKEN}"
TOKENS_FILE="/tokens/tokens.env"

echo "[setup] Esperando a InfluxDB en $HOST..."
until influx ping --host "$HOST" > /dev/null 2>&1; do
  sleep 3
done
echo "[setup] InfluxDB disponible."

# Si los tokens ya existen no recrear (reinicio sin borrar volumen),
# salvo que falte el token MCP (actualizacion desde version de 3 tokens).
if [ -f "$TOKENS_FILE" ]; then
  if grep -q "^INFLUXDB_MCP_TOKEN=" "$TOKENS_FILE" 2>/dev/null; then
    echo "[setup] $TOKENS_FILE ya existe con los 4 tokens, saltando creacion."
    exit 0
  fi
  echo "[setup] $TOKENS_FILE existe pero sin INFLUXDB_MCP_TOKEN, generando solo ese token..."
  ID_AIRE_UPG=$(influx bucket find --name "aire" --org "$ORG" \
    --host "$HOST" --token "$ADMIN_TOKEN" --hide-headers 2>/dev/null | cut -f 1)
  ID_METEO_UPG=$(influx bucket find --name "meteo" --org "$ORG" \
    --host "$HOST" --token "$ADMIN_TOKEN" --hide-headers 2>/dev/null | cut -f 1)
  ID_TRAFICO_UPG=$(influx bucket find --name "trafico" --org "$ORG" \
    --host "$HOST" --token "$ADMIN_TOKEN" --hide-headers 2>/dev/null | cut -f 1)
  ID_DEMO_UPG=$(influx bucket find --name "aire_demo" --org "$ORG" \
    --host "$HOST" --token "$ADMIN_TOKEN" --hide-headers 2>/dev/null | cut -f 1)
  TOKEN_MCP_UPG=$(influx auth create \
    --org "$ORG" \
    --description "mcp-read-only: lectura 4 buckets solo MCP" \
    --read-bucket "$ID_AIRE_UPG" \
    --read-bucket "$ID_METEO_UPG" \
    --read-bucket "$ID_TRAFICO_UPG" \
    --read-bucket "$ID_DEMO_UPG" \
    --host "$HOST" --token "$ADMIN_TOKEN" --hide-headers 2>/dev/null | cut -f 3)
  printf "INFLUXDB_MCP_TOKEN=%s\n" "$TOKEN_MCP_UPG" >> "$TOKENS_FILE"
  echo "[setup] Token 4 (mcp-read-only) añadido a $TOKENS_FILE (upgrade)."
  exit 0
fi

# Funcion: crear bucket si no existe
crear_bucket() {
  local nombre=$1
  local retencion=$2
  local desc=$3
  if influx bucket find --name "$nombre" --org "$ORG" \
       --host "$HOST" --token "$ADMIN_TOKEN" --hide-headers 2>/dev/null | grep -q "$nombre"; then
    echo "[setup] Bucket '$nombre' ya existe."
  else
    if [ "$retencion" = "0" ]; then
      influx bucket create \
        --name "$nombre" --org "$ORG" \
        --host "$HOST" --token "$ADMIN_TOKEN" \
        --description "$desc"
    else
      influx bucket create \
        --name "$nombre" --org "$ORG" \
        --retention "${retencion}s" \
        --host "$HOST" --token "$ADMIN_TOKEN" \
        --description "$desc"
    fi
    echo "[setup] Bucket '$nombre' creado (retencion=${retencion}s)."
  fi
}

crear_bucket "meteo"     "${INFLUXDB_RETENTION_METEO}"     "Meteo tiempo real Open-Meteo Bilbao"
crear_bucket "trafico"   "${INFLUXDB_RETENTION_TRAFICO}"   "Trafico Bilbao Open Data cada 5 min"
crear_bucket "aire_demo" "${INFLUXDB_RETENTION_AIRE_DEMO}" "Reproduccion acelerada historico NO2"

# Obtener IDs de los buckets
get_id() {
  influx bucket find --name "$1" --org "$ORG" \
    --host "$HOST" --token "$ADMIN_TOKEN" --hide-headers 2>/dev/null | cut -f 1
}
ID_METEO=$(get_id "meteo")
ID_TRAFICO=$(get_id "trafico")
ID_DEMO=$(get_id "aire_demo")
ID_AIRE=$(get_id "aire")
echo "[setup] IDs: aire=$ID_AIRE meteo=$ID_METEO trafico=$ID_TRAFICO aire_demo=$ID_DEMO"

# ── Tokens con minimo privilegio ──────────────────────────────────────────────
# Criterio: un token por rol, nunca uno solo para todo (puntua como deficiente).
#
# Token 1: nodered-write  → escritura meteo + trafico + aire_demo (NO aire)
# Token 2: batch-write    → escritura SOLO en aire y meteo (carga historica Python)
# Token 3: read-all       → lectura de los 4 buckets (Grafana)
# Token 4: mcp-read-only  → lectura de los 4 buckets (solo servidor MCP)
#
# Tags recomendados en los puntos escritos por Node-RED:
#   meteo:     ubicacion=bilbao, fuente=open-meteo
#   trafico:   codigo_seccion=<id>
#   aire_demo: estacion=<nombre>, zona=dentro|fuera|fondo
#
# Tags en la carga historica (carga_historica.py):
#   aire:      estacion=<nombre>, zona=<clasificacion>
#   meteo:     ubicacion=bilbao, fuente=historico-open-meteo
# ──────────────────────────────────────────────────────────────────────────────

# Token 1: escritura Node-RED (SOLO meteo + trafico + aire_demo; NO puede escribir en aire)
TOKEN_NR=$(influx auth create \
  --org "$ORG" \
  --description "nodered-write: meteo+trafico+aire_demo" \
  --write-bucket "$ID_METEO" \
  --write-bucket "$ID_TRAFICO" \
  --write-bucket "$ID_DEMO" \
  --host "$HOST" --token "$ADMIN_TOKEN" --hide-headers 2>/dev/null | cut -f 3)
echo "[setup] Token 1 (nodered-write) generado."

# Token 2: escritura carga historica (buckets aire y meteo; no puede tocar trafico ni aire_demo)
TOKEN_BATCH=$(influx auth create \
  --org "$ORG" \
  --description "batch-write: carga historica aire y meteo" \
  --write-bucket "$ID_AIRE" \
  --write-bucket "$ID_METEO" \
  --host "$HOST" --token "$ADMIN_TOKEN" --hide-headers 2>/dev/null | cut -f 3)
echo "[setup] Token 2 (batch-write) generado."

# Token 3: lectura para Grafana (todos los buckets, solo lectura)
TOKEN_READ=$(influx auth create \
  --org "$ORG" \
  --description "read-all: Grafana" \
  --read-bucket "$ID_AIRE" \
  --read-bucket "$ID_METEO" \
  --read-bucket "$ID_TRAFICO" \
  --read-bucket "$ID_DEMO" \
  --host "$HOST" --token "$ADMIN_TOKEN" --hide-headers 2>/dev/null | cut -f 3)
echo "[setup] Token 3 (read-all) generado."

# Token 4: lectura dedicada para MCP (todos los buckets, solo lectura, nunca escritura)
TOKEN_MCP=$(influx auth create \
  --org "$ORG" \
  --description "mcp-read-only: lectura 4 buckets solo MCP" \
  --read-bucket "$ID_AIRE" \
  --read-bucket "$ID_METEO" \
  --read-bucket "$ID_TRAFICO" \
  --read-bucket "$ID_DEMO" \
  --host "$HOST" --token "$ADMIN_TOKEN" --hide-headers 2>/dev/null | cut -f 3)
echo "[setup] Token 4 (mcp-read-only) generado."

# Guardar en volumen compartido (no accesible desde git)
mkdir -p /tokens
{
  printf "INFLUXDB_NODERED_WRITE_TOKEN=%s\n" "$TOKEN_NR"
  printf "INFLUXDB_BATCH_WRITE_TOKEN=%s\n"   "$TOKEN_BATCH"
  printf "INFLUXDB_READ_TOKEN=%s\n"          "$TOKEN_READ"
  printf "INFLUXDB_MCP_TOKEN=%s\n"          "$TOKEN_MCP"
} > "$TOKENS_FILE"
echo "[setup] 4 tokens guardados en $TOKENS_FILE"
echo "[setup] Inicializacion completada."