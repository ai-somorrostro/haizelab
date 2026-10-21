# HaizeLab

Evaluación del efecto de la Zona de Bajas Emisiones (ZBE) de Bilbao sobre el NO₂, para el Ayuntamiento de Bilbao. La pregunta que hay que responder es si conviene **ampliar, mantener o ajustar la ZBE**.

## Qué es

Dos partes que comparten los mismos datos:

- **Análisis** (`notebooks/zbe_bilbao.ipynb`): responde cinco preguntas con los datos horarios de NO₂ y SO₂ de 8 estaciones, del 01/01/2022 al 30/09/2026 (332.619 horas-estación). Compara dos estaciones de dentro de la ZBE con cinco de fuera.
- **Plataforma de seguimiento**: Node-RED recoge datos de forma periódica, InfluxDB los guarda y Grafana los muestra en paneles con alertas y permisos por equipo.

## Resultados

Todas las cifras salen de `resultados/resultados.json`, que el notebook escribe cada vez que se ejecuta.

- **Efecto neto** = lo que bajó el NO₂ dentro de la ZBE menos lo que bajó fuera. Lo que también bajó fuera (tiempo atmosférico, coches más nuevos) no se atribuye a la ZBE. Es el método de diferencias en diferencias, un método estadístico, no inteligencia artificial.
- **Intervalo del 95 %**: margen de error del efecto, calculado sorteando semanas (bootstrap por bloques semanales). Si no incluye el cero, el efecto no se explica por el azar.

| Pregunta | Resultado (µg/m³) | Qué significa |
|---|---|---|
| P1. ¿Bajó el NO₂ dentro más que fuera? | Dentro: 25,50 → 21,91 (−3,59). Fuera: 18,25 → 16,29 (−1,96). Efecto neto: **−1,63** (de −2,38 a −0,94) | Dentro bajó 1,63 µg/m³ más que fuera y el intervalo no incluye el cero: esa bajada propia de dentro no se explica por el azar. |
| P2. ¿Se concentra en el horario de la ZBE? | En horario ZBE: **−2,93** (de −3,82 a −2,06). Fuera de horario: −0,85 (de −1,56 a −0,19) | La bajada propia de dentro es mayor cuando la ZBE está activa, como cabe esperar si se debe a ella. |
| P3. ¿Se mantiene con viento en calma (< 2 m/s)? | Efecto neto en calma: **−1,23** (de −2,05 a −0,42) | Con poco viento la bajada se mantiene: no se explica porque después de la ZBE haya hecho más viento. |
| P4. ¿Baja también el SO₂, que no viene del tráfico? | Efecto neto del SO₂: **0,33** (de −0,01 a 0,66) | El SO₂ no baja más dentro que fuera: el método no encuentra una bajada donde la ZBE no debería actuar. |
| P5. ¿Qué aportó la fase 2? | Fase 1 frente a antes: −1,29 (de −2,43 a −0,13). Fase 2 frente a fase 1: **−0,52** (de −1,72 a 0,74) | La bajada propia de dentro llegó sobre todo con la fase 1; la fase 2 no muestra una bajada adicional que se distinga de cero. |

**Modelo de IA (anexo del notebook).** Random Forest se equivoca de media 8,14 µg/m³ por hora en un periodo que no vio al entrenar (el modelo base sin IA, 10,50). Con él, el efecto de la ZBE es **−0,49** (de −0,86 a −0,12). Con una ZBE ficticia el 15/06/2023 sale 0,33 (de −0,23 a 0,96): incluye el cero, pero se aleja de él una cantidad del mismo orden que el efecto. Qué significa: los dos métodos dicen que dentro bajó algo más que fuera, pero el tamaño exacto depende del método y se da con cautela.

**Limitaciones:** solo hay 2 estaciones dentro de la ZBE; el control es desigual (Europa baja un 26,8 %, más que las de dentro); las estaciones miden la concentración de NO₂ en el aire, no lo que emiten los coches.

El desarrollo está en el [informe para el cliente](docs/informe-cliente-sbd.md) y en la [propuesta de modelo de IA](docs/propuesta-modelo-ia.md).

## Arquitectura

![Arquitectura de HaizeLab: las fuentes entran por Node-RED y por una carga por lotes, se guardan en InfluxDB y se consultan en solo lectura desde Grafana y el servidor MCP](docs/img/arquitectura_haizelab.png)

| Servicio | Puerto | Función |
|---|---:|---|
| `influxdb` | 8086 | Base de datos de series temporales (InfluxDB 2.9) |
| `influxdb_setup` | — | Se ejecuta una vez: crea los buckets y un token por servicio con el permiso mínimo |
| `nodered` | 1880 | Automatización: consulta las fuentes y escribe en InfluxDB (meteorología cada 15 min, tráfico cada 5 min, demo de NO₂ cada 5 s) |
| `grafana` | 3000 | Paneles, alertas y permisos por equipo (Grafana 11.2) |
| `influx-mcp` | 5001 | Servidor MCP de solo lectura sobre InfluxDB |
| `chatbot` | 8000 | Asistente que responde con las cifras de `resultados.json` |
| `presentacion` | 8080 | Presentación web |
| `sbd-pipeline`, `sbd-notebook`, `carga-historica` | — | Tareas por lotes (perfil `pipeline`): descarga y limpieza, notebook y carga del histórico en InfluxDB |

Los puertos solo escuchan en `127.0.0.1`. Ningún token se guarda en el repositorio. El detalle de buckets, tags y fields está en el [organigrama de datos](docs/organigrama-datos.md).

## Arranque paso a paso

Requisito: Docker con Compose v2.

1. **Clonar y crear el fichero de entorno.**
   ```bash
   git clone https://github.com/ai-somorrostro/haizelab.git
   cd haizelab
   cp .env.example .env
   ```
2. **Rellenar `.env`.** Cambiar los valores `cambia_...` de `INFLUXDB_ADMIN_PASSWORD` (mínimo 8 caracteres), `INFLUXDB_ADMIN_TOKEN`, `NODE_RED_CREDENTIAL_SECRET`, `NODE_RED_ADMIN_PASSWORD` y `GRAFANA_DEFAULT_PASSWORD`. Para generar un valor aleatorio: `openssl rand -hex 32`. `.env` no se sube nunca al repositorio.
3. **Levantar la plataforma.**
   ```bash
   docker compose up -d --build
   docker compose ps -a
   ```
   `haizelab_influxdb_setup` debe quedar como `Exited (0)` y el resto como `healthy`.
4. **Cargar el histórico de calidad del aire (obligatorio).** Node-RED rellena `meteo`, `trafico` y `aire_demo`, pero el bucket `aire` solo se llena con este paso:
   ```bash
   docker compose run --rm --build carga-historica --dry-run   # construye la imagen y comprueba sin escribir
   docker compose run --rm carga-historica
   ```
5. **Abrir los servicios.**

   | Servicio | Dirección | Usuario |
   |---|---|---|
   | Grafana | http://localhost:3000 | `admin` (contraseña `INFLUXDB_ADMIN_PASSWORD`) o un usuario de equipo |
   | Node-RED | http://localhost:1880 | `admin` (contraseña `NODE_RED_ADMIN_PASSWORD`) |
   | InfluxDB | http://localhost:8086 | `admin` (contraseña `INFLUXDB_ADMIN_PASSWORD`) |
   | Presentación | http://localhost:8080 | — |
   | Chatbot | http://localhost:8000/docs | — |

   Los usuarios de Grafana los crea `grafana/provisioning/access-control/setup-access.sh`. Su contraseña es `GRAFANA_DEFAULT_PASSWORD` seguida de un sufijo:

   | Equipo | Usuarios | Sufijo | Rol |
   |---|---|---|---|
   | Dirección | `directora`, `ceo`, `coo`, `cfo` | `dir`, `ceo`, `coo`, `cfo` | Viewer |
   | Análisis | `analista1` … `analista6` | `a1` … `a6` | Viewer |
   | IT | `it_admin1`, `it_admin2`, `it_admin3` | `it1`, `it2`, `it3` | Admin (`it_admin1`) y Editor |

6. **Repetir el análisis (opcional).** El notebook solo lee `data/clean/` y vuelve a escribir `resultados/resultados.json` y las figuras de `docs/img/`:
   ```bash
   docker compose run --rm --build sbd-notebook
   ```
   `docker compose run --rm --build sbd-pipeline` vuelve a descargar y limpiar los datos desde las fuentes oficiales. El análisis llega hasta el 30/09/2026; Grafana puede mostrar datos posteriores.

Para parar: `docker compose down` (conserva los datos) o `docker compose down -v` (borra datos y tokens).

## Estructura

| Ruta | Contenido |
|---|---|
| `ingesta/` | `descargar_y_limpiar.py` (descarga, limpieza y cruce) y `carga_historica.py` (carga en InfluxDB) |
| `data/clean/` | Datos limpios que lee el notebook |
| `notebooks/zbe_bilbao.ipynb` | Análisis P1-P5 y anexo del modelo de IA |
| `resultados/resultados.json` | Única fuente de las cifras de los documentos |
| `docs/` | Informe para el cliente, propuesta de modelo de IA, organigrama de datos, infraestructura y registro de mejoras (`MEJORAS.md`). `generar_informe.py` y `generar_mia.py` crean los documentos a partir de `resultados.json` |
| `influxdb/`, `nodered/`, `grafana/`, `mcp/` | Configuración de cada servicio |
| `chatbot/`, `presentacion/` | Asistente y presentación web |
| `docker-compose.yml`, `.env.example` | Arranque de todos los servicios y plantilla de variables |

## Autores

| Persona | Rol | Área |
|---|---|---|
| Alfred Gabriel | Product Owner | Relación con el cliente y desarrollo |
| Iñigo Guzmán | Lead Data Engineer | Datos e infraestructura |
| Kerman Latorre | Scrum Master | Análisis y modelado |

El trabajo se integra en `develop` mediante pull requests revisadas por otro miembro del equipo.
