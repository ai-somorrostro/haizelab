# nodered/Dockerfile
# ==================
# Imagen personalizada de Node-RED para el proyecto HaizeLab.
# Basada en la imagen oficial con version fijada (reproducibilidad garantizada).
#
# Incluye:
#   - node-red-contrib-influxdb 0.7.0: nodo para escribir en InfluxDB 2.x
#   - entrypoint.sh: espera al fichero de tokens antes de arrancar Node-RED
#
# Los flujos se cargan desde nodered/flows.json (montado como volumen).

FROM nodered/node-red:5.0.7

# Instalar el nodo de InfluxDB en la imagen para evitar retrasos al arrancar
RUN npm install --prefix /usr/src/node-red \
    node-red-contrib-influxdb@0.7.0 \
    && npm cache clean --force

# Script de arranque: espera el fichero de tokens generado por influxdb_setup
COPY entrypoint.sh /usr/local/bin/entrypoint.sh

# El usuario de la imagen oficial es node-red (1000)
USER root
RUN chmod +x /usr/local/bin/entrypoint.sh
USER node-red

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]