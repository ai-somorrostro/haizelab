#!/bin/sh
# mcp/entrypoint.sh
# ==================
# Entrypoint del servidor MCP HaizeLab (solo lectura).
# 1. Si INFLUXDB_TOKEN ya viene definido (override manual via .env
#    INFLUXDB_MCP_TOKEN), lo respeta y arranca directamente.
# 2. Si no, espera a /tokens/tokens.env generado por influxdb_setup
#    y exporta INFLUXDB_MCP_TOKEN como INFLUXDB_TOKEN.
# 3. Arranca el servidor influxdb-mcp.

set -eu

TOKENS_FILE="/tokens/tokens.env"
MAX_ESPERA=120

# Override explicito (retrocompatibilidad con .env manual): compose mapea
# INFLUXDB_MCP_TOKEN -> INFLUXDB_TOKEN. Si ya hay token, no esperar al volumen.
if [ -n "${INFLUXDB_TOKEN:-}" ]; then
  echo "[haizelab-mcp] Usando INFLUXDB_TOKEN explicito (override .env)."
  exec python -m influxdb_mcp
fi

echo "[haizelab-mcp] Esperando tokens en $TOKENS_FILE ..."
INICIO=$(date +%s)
while [ ! -f "$TOKENS_FILE" ]; do
  AHORA=$(date +%s)
  if [ $((AHORA - INICIO)) -ge $MAX_ESPERA ]; then
    echo "[haizelab-mcp] ERROR: timeout tras ${MAX_ESPERA}s esperando tokens"
    echo "[haizelab-mcp] Sugerencia: comprueba que influxdb_setup termino en 0."
    exit 1
  fi
  sleep 3
done

# Cargar fichero linea a linea (ignora comentarios y vacias)
while IFS= read -r linea; do
  case "$linea" in
    ''|\#*) continue ;;
  esac
  export "$linea"
done < "$TOKENS_FILE"

if [ -z "${INFLUXDB_MCP_TOKEN:-}" ]; then
  echo "[haizelab-mcp] ERROR: $TOKENS_FILE existe pero sin INFLUXDB_MCP_TOKEN."
  echo "[haizelab-mcp] Si el volumen es de una version anterior, reinicia influxdb_setup para el upgrade automatico."
  exit 1
fi

export INFLUXDB_TOKEN="$INFLUXDB_MCP_TOKEN"
PREVIEW=$(printf "%s" "$INFLUXDB_TOKEN" | cut -c 1-8)
echo "[haizelab-mcp] Token MCP cargado desde volumen (primeros 8 chars): ${PREVIEW}..."

echo "[haizelab-mcp] Iniciando influxdb-mcp..."
exec python -m influxdb_mcp
