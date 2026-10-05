#!/bin/sh
# influxdb/init-influxdb.sh
# =========================
# Se ejecuta en el contenedor efimero "influxdb_setup" despues de que influxdb
# este sano (depends_on: condition: service_healthy).
#
# Responsabilidades:
#   1. Crear los buckets: meteo, trafico, aire_demo (aire lo crea Docker)
#   2. Generar token escritura para Node-RED (solo meteo+trafico+aire_demo)
#   3. Generar token lectura para Grafana/MCP (todos los buckets)
#   4. Escribir los tokens en /tokens/tokens.env (volumen compartido)
#
# Si /tokens/tokens.env ya existe (reinicio sin -v), sale sin recrear nada.

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

# Si los tokens ya existen no recrear (reinicio sin borrar volumen)
if [ -f "$TOKENS_FILE" ]; then
  echo "[setup] $TOKENS_FILE ya existe, saltando creacion de buckets y tokens."
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

# Token escritura Node-RED (SOLO meteo + trafico + aire_demo; NO puede escribir en aire)
TOKEN_NR=$(influx auth create \
  --org "$ORG" \
  --description "nodered-write: meteo+trafico+aire_demo" \
  --write-bucket "$ID_METEO" \
  --write-bucket "$ID_TRAFICO" \
  --write-bucket "$ID_DEMO" \
  --host "$HOST" --token "$ADMIN_TOKEN" --hide-headers 2>/dev/null | cut -f 3)
echo "[setup] Token escritura Node-RED generado."

# Token lectura para Grafana/MCP (todos los buckets, solo lectura)
TOKEN_READ=$(influx auth create \
  --org "$ORG" \
  --description "read-all: Grafana y MCP futura" \
  --read-bucket "$ID_AIRE" \
  --read-bucket "$ID_METEO" \
  --read-bucket "$ID_TRAFICO" \
  --read-bucket "$ID_DEMO" \
  --host "$HOST" --token "$ADMIN_TOKEN" --hide-headers 2>/dev/null | cut -f 3)
echo "[setup] Token lectura generado."

# Guardar en volumen compartido (no accesible desde git)
mkdir -p /tokens
{
  printf "INFLUXDB_NODERED_WRITE_TOKEN=%s\n" "$TOKEN_NR"
  printf "INFLUXDB_READ_TOKEN=%s\n" "$TOKEN_READ"
} > "$TOKENS_FILE"
echo "[setup] Tokens guardados en $TOKENS_FILE"
echo "[setup] Inicializacion completada."