#!/bin/sh
# nodered/entrypoint.sh
# =====================
# Entrypoint de Node-RED HaizeLab.
# 1. Espera al fichero /tokens/tokens.env generado por influxdb_setup
# 2. Exporta INFLUXDB_NODERED_WRITE_TOKEN e INFLUXDB_READ_TOKEN como variables de entorno
# 3. Copia settings.js al directorio /data si no existe ya
# 4. Inicia Node-RED con el fichero de flujos montado

TOKENS_FILE="/tokens/tokens.env"
MAX_ESPERA=120
INICIO=$(date +%s)

echo "[haizelab-entrypoint] Esperando tokens en $TOKENS_FILE ..."
while [ ! -f "$TOKENS_FILE" ]; do
  AHORA=$(date +%s)
  if [ $((AHORA - INICIO)) -ge $MAX_ESPERA ]; then
    echo "[haizelab-entrypoint] ERROR: timeout tras ${MAX_ESPERA}s esperando tokens"
    exit 1
  fi
  sleep 3
done
echo "[haizelab-entrypoint] Tokens encontrados, cargando..."

while IFS= read -r linea; do
  case "$linea" in
    ''|\#*) continue ;;
  esac
  export "$linea"
done < "$TOKENS_FILE"

TOKEN_PREVIEW=$(printf "%s" "$INFLUXDB_NODERED_WRITE_TOKEN" | cut -c 1-8)
echo "[haizelab-entrypoint] Token NR cargado (primeros 8 chars): ${TOKEN_PREVIEW}..."

# Generar fichero de credenciales para el nodo de InfluxDB
if [ -n "$INFLUXDB_NODERED_WRITE_TOKEN" ]; then
  cat <<EOF > /data/flows_cred.json
{
  "influx_cfg_haizelab": {
    "token": "$INFLUXDB_NODERED_WRITE_TOKEN"
  }
}
EOF
  echo "[haizelab-entrypoint] Credenciales inyectadas en /data/flows_cred.json"
fi

# Copiar settings.js al directorio de datos si no existe
if [ ! -f "/data/settings.js" ]; then
  cp /usr/src/node-red/settings.js /data/settings.js 2>/dev/null || true
fi

echo "[haizelab-entrypoint] Iniciando Node-RED..."
exec node /usr/src/node-red/node_modules/.bin/node-red \
  --userDir /data \
  --flowFile flows.json \
  --settings /data/settings.js \
  "$@"