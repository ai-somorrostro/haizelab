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

echo "[haizelab-grafana] Datasource provisionado con exito. Iniciando servidor Grafana..."
exec /run.sh "$@"
