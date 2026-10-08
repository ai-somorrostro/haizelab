#!/bin/sh
set -eu

# Esperar a que el archivo de tokens exista en el volumen
while [ ! -f /tokens/tokens.env ]; do
  echo "[haizelab-grafana] Esperando tokens en /tokens/tokens.env..."
  sleep 1
done

# Cargar variables de tokens
. /tokens/tokens.env

echo "[haizelab-grafana] Provisionando datasource InfluxDB-HaizeLab con token de lectura..."

mkdir -p /etc/grafana/provisioning/datasources

cat <<EOF > /etc/grafana/provisioning/datasources/influxdb.yaml
apiVersion: 1

datasources:
  - name: InfluxDB-HaizeLab
    uid: InfluxDB-HaizeLab
    type: influxdb
    access: proxy
    url: http://influxdb:8086
    isDefault: true
    jsonData:
      version: Flux
      organization: ${INFLUXDB_ORG:-haizenlab}
      defaultBucket: aire_demo
      tlsSkipVerify: true
    secureJsonData:
      token: "${INFLUXDB_READ_TOKEN}"
    editable: false
EOF

echo "[haizelab-grafana] Datasource provisionado con exito."

# Lanzar Grafana en background, esperar a que suba y luego configurar acceso
echo "[haizelab-grafana] Iniciando servidor Grafana..."
/run.sh "$@" &
GRAFANA_PID=$!

# Control de acceso: esperar a que la API esté disponible antes de configurar
echo "[haizelab-grafana] Esperando a que la API de Grafana esté disponible para configurar acceso..."
INTENTOS=0
until curl -s "http://localhost:3000/api/health" 2>/dev/null | grep -Eq '"database":[[:space:]]*"ok"'; do
  sleep 2
  INTENTOS=$((INTENTOS + 1))
  if [ "$INTENTOS" -ge 40 ]; then
    echo "[haizelab-grafana] AVISO: Grafana tardó demasiado. Saltando setup-access."
    wait "$GRAFANA_PID"
    exit 0
  fi
done

echo "[haizelab-grafana] Ejecutando setup de control de acceso..."
sh /etc/grafana/provisioning/access-control/setup-access.sh || \
  echo "[haizelab-grafana] AVISO: setup-access.sh falló (puede ser re-ejecucion en reinicio)."

echo "[haizelab-grafana] Configuracion completada. Grafana en ejecucion."
wait "$GRAFANA_PID"
