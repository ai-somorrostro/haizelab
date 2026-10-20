# HaizeLab

Evaluación del efecto de la Zona de Bajas Emisiones (ZBE) de Bilbao sobre la concentración de NO₂, con datos horarios de 2022 a 2026, y plataforma de monitorización en tiempo real construida con Node-RED, InfluxDB y Grafana.

Proyecto del Reto 0 "HERE WE GO" del Centro de Formación Somorrostro, curso de especialización en Inteligencia Artificial y Big Data.

## Contenido

- [Resultado](#resultado)
- [Arquitectura](#arquitectura)
- [Puesta en marcha](#puesta-en-marcha)
- [Carga del histórico](#carga-del-histórico)
- [Pipeline analítico](#pipeline-analítico)
- [Grafana: usuarios, roles y alertas](#grafana-usuarios-roles-y-alertas)
- [Servidor MCP](#servidor-mcp)
- [Asistente inteligente (Chatbot)](#asistente-inteligente-chatbot)
- [Presentación web](#presentación-web)
- [Estructura del repositorio](#estructura-del-repositorio)
- [Documentación](#documentación)
- [Flujo de trabajo](#flujo-de-trabajo)
- [Equipo](#equipo)

## Resultado

La pregunta del cliente es si la ZBE ha reducido el NO₂ en el centro más de lo que ha bajado en el resto del área metropolitana. Se responde con un diseño de diferencias en diferencias (DiD): dos estaciones dentro del perímetro frente a cinco estaciones de control fuera, antes y después del 15 de junio de 2024.

| Indicador | Antes | Después | Variación |
|---|---:|---:|---:|
| NO₂ dentro de la ZBE (Mazarredo y Mª Díaz de Haro) | 25,50 µg/m³ | 21,90 µg/m³ | -3,59 µg/m³ (-14,1 %) |
| NO₂ en las estaciones de control (Gran Bilbao) | 18,25 µg/m³ | 16,29 µg/m³ | -1,96 µg/m³ (-10,8 %) |
| **Efecto neto atribuible a la ZBE (DiD)** | | | **-1,63 µg/m³ (-6,4 %)** |

El estimador DiD tiene un intervalo de confianza al 95 % de -1,87 a -1,39 µg/m³ (p < 0,001). Tres comprobaciones lo acompañan:

| Comprobación | Resultado | Qué descarta |
|---|---|---|
| Regresión con controles de meteorología y mes | -1,74 µg/m³ | Que el efecto se deba a un periodo posterior más ventoso o lluvioso |
| Horas de calma (viento inferior a 2 m/s), dentro de la ZBE | De 28,10 a 25,47 µg/m³ en la fase 1 (-9,4 %) y a 23,56 µg/m³ en la fase 2 (-16,2 %) | Que la mejora dependa de la ventilación |
| Placebo con SO₂, que no procede del tráfico | DiD de +0,33 µg/m³ | Que cualquier contaminante baje más dentro que fuera |

El aforo del acceso de San Mamés pasó de 50.127 vehículos al día en 2023 a 45.052 en 2024 (-10,1 %) y repuntó a 48.543 en 2025, un 3,2 % por debajo de 2023.

La conclusión es un efecto confirmado pero moderado: algo más de la mitad de la bajada observada en el centro se habría producido igualmente, porque también bajó fuera. Limitaciones que hay que tener presentes al leer las cifras:

- Solo hay dos estaciones oficiales dentro del perímetro.
- Se miden concentraciones en el aire, no emisiones de los vehículos.
- Coinciden otros cambios en el mismo periodo, como la renovación del parque móvil.

El desarrollo completo está en el [informe para el cliente](docs/informe-cliente-sbd.md) y en el [notebook](notebooks/zbe_bilbao.ipynb). Las cifras de esta sección salen de la ejecución de ese notebook sobre 332.776 registros horarios de ocho estaciones.

### Modelos utilizados: Gradient Boosting (Propuesta MIA) y Diferencias en Diferencias (Contraste SBD)

Para garantizar la máxima solidez, el proyecto articula dos enfoques metodológicos que están **implementados y ejecutados** en el [notebook](notebooks/zbe_bilbao.ipynb):

1. **Gradient Boosting (Modelo de IA Elegido en MIA):** Un modelo de Machine Learning (`HistGradientBoostingRegressor`) que captura interacciones meteorológicas no lineales complejas (velocidad y ángulo de viento, lluvia, temperatura, estacionalidad y hora). Entrenado con los datos previos (2022–junio 2024), predice el contrafactual de lo que habría ocurrido en el centro sin ZBE. Estima una reducción neta de **-2,87 µg/m³ (-11,6 %)**. La justificación técnica formal se detalla en la [Propuesta de modelo de IA](docs/propuesta-modelo-ia.md), y su ejecución práctica está en las celdas 18 y 19 del notebook.
2. **Diferencias en Diferencias (DiD - Contraste Econométrico en SBD):** Modelo causal cuasiexperimental de referencia que compara las dos estaciones interiores frente a cinco estaciones metropolitanas de control, aislando un impacto neto atribuible de **-1,63 µg/m³ (-6,4 %)** (p < 0,001). Actúa como contraste de robustez para validar que ambas aproximaciones (Machine Learning y Econometría) convergen en la misma conclusión.

## Arquitectura

<picture>
  <img src="docs/img/arquitectura_haizelab.png" alt="Arquitectura de HaizeLab: las fuentes abiertas entran por Node-RED y por una carga por lotes, se almacenan en InfluxDB y se consultan en solo lectura desde Grafana y el servidor MCP" width="100%">
</picture>

Las flechas siguen el sentido del dato. Cada flujo de Node-RED escribe en su propio bucket y ningún servicio de consumo puede escribir. Junto a cada bucket aparece su retención.

### Servicios

Todo se levanta con Docker Compose. Los puertos se publican solo en `127.0.0.1`.

| Servicio | Imagen | Puerto | Función |
|---|---|---:|---|
| `influxdb` | `influxdb:2.9.1` | 8086 | Base de datos de series temporales |
| `influxdb_setup` | `influxdb:2.9.1` | | Contenedor efímero que crea los buckets y los tokens en el primer arranque |
| `nodered` | `nodered/node-red:5.0.7` con `node-red-contrib-influxdb` 0.7.0 | 1880 | Ingesta continua de meteorología, tráfico y demo de NO₂ |
| `grafana` | `grafana/grafana:11.2.0` | 3000 | Dashboards, alertas y control de acceso |
| `influx-mcp` | `python:3.12-slim` con `influxdb-mcp` | 5001 | Servidor MCP de solo lectura (requisito PIA) |
| `chatbot` | `python:3.11-slim` con FastAPI | 8000 | Asistente inteligente explicable con base de conocimiento local |
| `presentacion` | `nginx:alpine` | 8080 | Diapositivas interactivas con dashboards embebidos |

### Buckets

| Bucket | Measurement | Retención | Quién escribe |
|---|---|---|---|
| `aire` | `contaminantes` | Sin límite | Carga por lotes con pandas |
| `meteo` | `clima` | Sin límite | Node-RED cada 15 minutos y carga por lotes del histórico |
| `trafico` | `estado` | 30 días | Node-RED cada 5 minutos |
| `aire_demo` | `contaminantes` | 7 días | Node-RED cada 5 segundos, reproduciendo el histórico |

El detalle de tags y fields está en el [organigrama de datos](docs/organigrama-datos.md).

### Tokens

El script [`influxdb/init-influxdb.sh`](influxdb/init-influxdb.sh), ejecutado por el contenedor `influxdb_setup`, genera automáticamente los cuatro tokens con el principio de mínimo privilegio y los deposita en el volumen compartido `influxdb_tokens`. **No es necesario crear ningún token a mano en la interfaz de InfluxDB**, ya que los servicios los consumen directamente del volumen en solo lectura. Ningún token se guarda en el repositorio.

| Token | Permiso | Lo usa |
|---|---|---|
| `nodered-write` | Escritura en `meteo`, `trafico` y `aire_demo` | Node-RED |
| `batch-write` | Escritura en `aire` y `meteo` | `ingesta/carga_historica.py` |
| `read-all` | Lectura de los cuatro buckets | Grafana |
| `mcp-read-only` | Lectura de los cuatro buckets | Servidor MCP |

## Puesta en marcha

Requisito: Docker con Compose v2.

**1. Clonar el repositorio y crear el fichero de entorno.** En una terminal:

```bash
git clone https://github.com/ai-somorrostro/haizelab.git
cd haizelab
cp .env.example .env
```

**2. Editar `.env`** y sustituir los cinco valores de ejemplo. El fichero está en `.gitignore` y no debe subirse.

| Variable | Para qué sirve |
|---|---|
| `INFLUXDB_ADMIN_PASSWORD` | Contraseña del administrador de InfluxDB y de Grafana |
| `INFLUXDB_ADMIN_TOKEN` | Token de administración de InfluxDB, usado solo por `influxdb_setup` |
| `NODE_RED_CREDENTIAL_SECRET` | Clave con la que Node-RED cifra sus credenciales |
| `NODE_RED_ADMIN_PASSWORD` | Contraseña del editor de Node-RED |
| `GRAFANA_DEFAULT_PASSWORD` | Base de las contraseñas de los usuarios de Grafana |
| `ALERT_EMAIL_TO` *(Opcional)* | Correo destinatario que recibirá las alertas (por defecto `alfred.ciuca-andrei06@somo.eus`) |
| `GF_SMTP_*` *(Opcional)* | 	Configuración del servidor SMTP emisor para que Grafana pueda enviar los correos. GF_SMTP_PASSWORD no es la contraseña normal del correo, sino una contraseña de aplicación. Con Gmail, activa primero la verificación en dos pasos en tu cuenta de Google y después crea la contraseña en myaccount.google.com/apppasswords. Cópiala sin espacios |
| `GEMINI_API_KEY` *(Opcional)* | Clave gratuita de Google Gemini para activar el razonamiento con IA del chatbot |

Para generar un valor aleatorio:

```bash
openssl rand -hex 32
```

**3. Levantar la plataforma.**

```bash
docker compose up -d --build
```

Durante el primer arranque, el contenedor efímero `haizelab_influxdb_setup` ejecuta automáticamente [`influxdb/init-influxdb.sh`](influxdb/init-influxdb.sh), creando los buckets adicionales (`meteo`, `trafico`, `aire_demo`) y aprovisionando los cuatro tokens con sus permisos mínimos.

> **Nota:** Si en algún momento necesitas verificar o regenerar los buckets y tokens manualmente (por ejemplo, tras modificar retenciones en `.env` sin reiniciar los volúmenes), puedes invocar el script directamente con:
> ```bash
> docker compose run --rm influxdb_setup
> ```

**4. Comprobar el estado.**

```bash
docker compose ps -a
```

`haizelab_influxdb_setup` debe aparecer como `Exited (0)` y el resto de contenedores como `healthy`.

| Servicio | Dirección | Usuario | Contraseña | Notas |
|---|---|---|---|---|
| Presentación interactiva | http://localhost:8080 | — | — | Sin autenticación |
| Grafana | http://localhost:3000 | `admin` *(o ver tabla RBAC)* | `admin` | Ver detalle de usuarios y roles abajo |
| Node-RED | http://localhost:1880 | `admin` | `admin` | Configurado en `.env` |
| InfluxDB | http://localhost:8086 | `admin` | `adminadmin` | Organización: `haizenlab` (mín. 8 caracteres) |
| Servidor MCP | http://127.0.0.1:5001/mcp/ | — | — | Autenticado internamente por token |
| Chatbot (API / Docs) | http://localhost:8000/docs | — | — | Sin autenticación |

Para detener la plataforma conservando los datos:

```bash
docker compose down
```

Para detenerla borrando también los datos y los tokens:

```bash
docker compose down -v
```

## Carga del histórico

Tras el primer arranque, `aire_demo`, `meteo` y `trafico` empiezan a recibir datos por Node-RED. El bucket `aire`, con el histórico oficial de NO₂, se rellena una vez con el script de carga, que se ejecuta en un contenedor y no requiere instalar nada en el host.

**1. Validar sin escribir.** La plataforma debe estar levantada (`docker compose ps -a` con `influxdb` en `healthy`).

```bash
docker compose run --rm carga-historica --dry-run
```

**2. Cargar.**

```bash
docker compose run --rm carga-historica
```

El contenedor usa automáticamente el token `batch-write` generado por `init-influxdb.sh` y recurre al de administración si no lo encuentra. Para cargar un solo bucket: `docker compose run --rm carga-historica --bucket aire`.

<details>
<summary>Alternativa: ejecutar desde el host con entorno virtual</summary>

En Debian/Ubuntu recientes `pip` no permite instalar paquetes en el Python del sistema (PEP 668), por eso la carga se ejecuta desde el host en su propio entorno virtual.

```bash
sudo apt install python3-full python3-venv   # solo la primera vez
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python ingesta/carga_historica.py --bucket all --dry-run
python ingesta/carga_historica.py --bucket all
```

El directorio `.venv/` ya está en `.gitignore`. El entorno hay que activarlo con `source .venv/bin/activate` en cada terminal nueva.

Si `pip install` falla con tu versión de Python (por ejemplo, 3.14), crea el entorno con Python 3.12:

```bash
pipx install uv
uv venv --python 3.12 .venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

</details>

## Pipeline analítico

Hay un solo pipeline. `ingesta/descargar_y_limpiar.py` descarga los datos de Open Data Euskadi y Open-Meteo, los limpia y los cruza; `notebooks/zbe_bilbao.ipynb` hace el análisis, guarda las figuras en `docs/img/` y todas las cifras en `resultados/resultados.json`.

| Código | Datos | Salida |
|---|---|---|
| `ingesta/descargar_y_limpiar.py` y `notebooks/zbe_bilbao.ipynb` | `data/raw/` (crudo, no versionado) y `data/clean/` (limpio) | `docs/img/` y `resultados/resultados.json` |

Para reproducirlo:

```bash
docker compose run --rm sbd-pipeline
docker compose run --rm sbd-notebook
```

## Grafana: usuarios, roles y alertas

Los usuarios, los equipos y la página de inicio de cada equipo se crean al arrancar mediante `grafana/provisioning/access-control/setup-access.sh`.

Por defecto (según [.env](.env) con `INFLUXDB_ADMIN_PASSWORD=admin` y `GRAFANA_DEFAULT_PASSWORD=admin`), las credenciales de acceso son:

| Equipo | Usuario | Contraseña | Rol / Permisos | Página de inicio |
|---|---|---|---|---|
| **Super Admin** | `admin` | `admin` | Admin (Control total) | Principal |
| **IT** | `it_admin1` | `adminit1` | Admin | Principal |
| **IT** | `it_admin2` | `adminit2` | Editor (Crear y editar paneles) | Principal |
| **IT** | `it_admin3` | `adminit3` | Editor (Crear y editar paneles) | Principal |
| **Dirección** | `directora` | `admindir` | Viewer (Solo lectura) | Monitor ZBE en tiempo real (`haizelab-overview`) |
| **Dirección** | `ceo` | `adminceo` | Viewer (Solo lectura) | Monitor ZBE en tiempo real (`haizelab-overview`) |
| **Dirección** | `coo` | `admincoo` | Viewer (Solo lectura) | Monitor ZBE en tiempo real (`haizelab-overview`) |
| **Dirección** | `cfo` | `admincfo` | Viewer (Solo lectura) | Monitor ZBE en tiempo real (`haizelab-overview`) |
| **Análisis** | `analista1` | `admina1` | Viewer (Solo lectura) | Panel de análisis ZBE (`haizelab-analisis`) |
| **Análisis** | `analista2` | `admina2` | Viewer (Solo lectura) | Panel de análisis ZBE (`haizelab-analisis`) |
| **Análisis** | `analista3` | `admina3` | Viewer (Solo lectura) | Panel de análisis ZBE (`haizelab-analisis`) |
| **Análisis** | `analista4` | `admina4` | Viewer (Solo lectura) | Panel de análisis ZBE (`haizelab-analisis`) |
| **Análisis** | `analista5` | `admina5` | Viewer (Solo lectura) | Panel de análisis ZBE (`haizelab-analisis`) |
| **Análisis** | `analista6` | `admina6` | Viewer (Solo lectura) | Panel de análisis ZBE (`haizelab-analisis`) |

> [!IMPORTANT]
> **Resolución de problemas de acceso en Grafana:**
> - Inicia sesión siempre con el **nombre de usuario** (ej. `admin`, `directora`, `it_admin1`, `analista1`), **no** con el correo electrónico.
> - Si falla la contraseña o el usuario en Grafana (`Login failed: Invalid username or password`), ejecuta el siguiente comando en la terminal para restablecer la contraseña a `admin`:
> ```bash
> docker exec -it haizelab_grafana grafana-cli admin reset-admin-password admin
> ```
> *(O bien desde el directorio del proyecto con Docker Compose: `docker compose exec grafana grafana-cli admin reset-admin-password admin`)*.

Las alertas se aprovisionan desde `grafana/provisioning/alerting/alerting.yaml`:

| Alerta | Umbral | Referencia |
|---|---|---|
| NO₂, aviso | Más de 25 µg/m³ | Guía de la OMS de 2021 |
| NO₂, superación | Más de 40 µg/m³ | Límite anual de la UE |
| NO₂, pico horario | Más de 200 µg/m³ | Límite horario de la UE |
| Tráfico, congestión | Ocupación media superior al 35 % | Criterio propio |

## Servidor MCP

El servicio `influx-mcp` expone InfluxDB a clientes compatibles con Model Context Protocol en `http://127.0.0.1:5001/mcp/`, con un token que solo permite leer. Ofrece cuatro herramientas: `test_connection`, `list_buckets`, `list_measurements` y `execute_flux_query`.

La configuración de los clientes OpenCode y Antigravity ya está en `opencode.json` y `.agents/mcp_config.json`. La instalación, la verificación y la resolución de problemas están en [mcp/README.md](mcp/README.md).

## Asistente inteligente (Chatbot)

El servicio `chatbot` (`http://localhost:8000`) proporciona una API en FastAPI diseñada para responder consultas técnicas sobre el estudio de la ZBE de Bilbao, métricas DiD, tráfico, clima y arquitectura.

### Modalidades de funcionamiento:

1. **Modo Offline (Por defecto):**
   * No requiere ninguna clave ni configuración adicional.
   * Responde de forma instantánea y determinista utilizando los datos oficiales de `knowledge_base.json`.
   * Garantiza que el asistente siempre funcione en cualquier equipo sin internet.

2. **Modo Razonamiento con IA en vivo (Opcional):**
   * Si quieres que el asistente genere lenguaje natural dinámico, razone hipótesis (*«¿Por qué el SO₂ no bajó?»*) y argumente los porqués:
     1. Obtén una clave API gratuita en [Google AI Studio](https://aistudio.google.com/) *(se genera en 10 segundos con tu cuenta de Gmail, gratis y sin tarjeta)*.
     2. Añádela a tu archivo `.env`:
        ```env
        GEMINI_API_KEY=AIzaSy_tu_clave_aqui
        ```
     3. Reinicia el contenedor del chatbot:
        ```bash
        docker compose up -d chatbot
        ```

La documentación interactiva de la API está disponible en `http://localhost:8000/docs`.

## Presentación web

La presentación es una aplicación web interactiva que se levanta automáticamente con Docker Compose en el puerto 8080.

Al acceder a **`http://localhost:8080`**, se cargan las diapositivas con:
* Integración en directo del dashboard de **Grafana** (`:3000`).
* Monitorización de **Node-RED** (`:1880`) e **InfluxDB** (`:8086`).
* Widget interactivo del **Chatbot Assistant** (`:8000`).

Todo funciona en red local (`localhost`), de forma 100% autónoma y sin dependencias de túneles externos ni servicios de terceros.

## Estructura del repositorio

| Ruta | Contenido |
|---|---|
| `docker-compose.yml` | Orquestación de los 7 servicios de la plataforma |
| `.env.example` | Plantilla de credenciales y variables de entorno |
| `influxdb/` | Script de inicialización de buckets y tokens de mínimo privilegio |
| `nodered/` | Dockerfile y flujos de ingesta continua (`flows.json`) |
| `grafana/` | Dashboards, alertas, mapa de la ZBE y aprovisionamiento de roles |
| `mcp/` | Servidor MCP para consultas a InfluxDB (requisito PIA) |
| `chatbot/` | Microservicio FastAPI y base de conocimiento local |
| `presentacion/` | Web de diapositivas interactivas servida por Nginx (:8080) |
| `notebooks/` | Notebook oficial del análisis exploratorio y causal (SBD) |
| `ingesta/` | Scripts de ingesta y carga histórica por lotes a InfluxDB |
| `data/` | Datasets limpios del análisis |
| `resultados/` | Cifras del análisis (`resultados.json`), generadas por el notebook |
| `docs/` | Entregables oficiales de SBD, MIA y BDA |

## Documentación

| Documento | Módulo | Contenido |
|---|---|---|
| [Informe para el cliente](docs/informe-cliente-sbd.md) | Sistemas de Big Data | Preguntas de negocio, fuentes, resultados, conclusiones y recomendaciones |
| [Propuesta de modelo de IA](docs/propuesta-modelo-ia.md) | Modelos de IA | Alternativas consideradas, modelo elegido, impacto y riesgos |
| [Infraestructura explicada](docs/infraestructura-explicada.md) | Big Data Aplicado | InfluxDB, Node-RED, Grafana y gestión de tokens |
| [Organigrama de datos](docs/organigrama-datos.md) | Big Data Aplicado | Buckets, measurements, tags y fields |
| [Servidor MCP](mcp/README.md) | Programación de IA | Instalación, clientes y verificación del protocolo MCP |
| [Asistente inteligente](chatbot/README.md) | Programación de IA / Modelos de IA | API FastAPI, base de conocimiento local y modo offline |

El informe para el cliente se genera con `python docs/generar_informe.py` a partir de `resultados/resultados.json`; la versión de referencia es `docs/informe-cliente-sbd.md`. Para crear el `.docx` y el `.pdf` hace falta Windows con Microsoft Word instalado (con `--solo-md` genera solo el Markdown en cualquier sistema).

## Flujo de trabajo

- La rama de integración es `develop`.
- Cada tarea se desarrolla en una rama `feature/nombre-corto`.
- Los cambios llegan a `develop` por pull request revisada por otra persona del equipo.
- Los secretos viven en `.env`, que no se versiona. En el repositorio solo está `.env.example`.

## Equipo

| Persona | Rol | Responsabilidades clave |
|---|---|---|
| Alfred Gabriel | Product Owner | Sistemas de Big Data & Modelado (pipeline 332k filas, econometría DiD, validación) |
| Iñigo Guzmán | Lead Data Engineer | Big Data Aplicado (Docker, InfluxDB buckets/tokens, Node-RED streaming, Grafana RBAC) |
| Kerman Latorre | Scrum Master | Modelos de IA & Protocolos (Servidor MCP, integración de herramientas IA, metodología ágil) |
