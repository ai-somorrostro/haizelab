# HaizeLab: Monitorización y Análisis Multivariable de la ZBE de Bilbao

> **Evaluación de impacto de la Zona de Bajas Emisiones (ZBE) en la calidad del aire de Bilbao (2022-2026).**  
> Reto 0 ("HERE WE GO") — Centro de Formación Somorrostro | Especialización en Inteligencia Artificial y Big Data.  
> **Equipo Haizen Lab:** Alfred Gabriel (PO / PIA), Iñigo Bilbao (SM / MIA), Kerman Irusta (Lead Data Engineer / BDA).

---

## 🚀 Despliegue en Vivo y Demostración Interactiva

Para la defensa del proyecto y evaluación por el tribunal, todos los componentes han sido desplegados y configurados para acceso interactivo inmediato:

| Entorno / Servicio | Acceso / URL | Credenciales / Token | Finalidad y Estado |
|---|---|---|---|
| **Presentación Web Oficial** | [haizelab-presentacion.vercel.app](https://haizelab-presentacion.vercel.app) | Libre (Acceso público global) | Despliegue en producción (Vercel). Presentación interactiva del proyecto con diapositivas, arquitectura y cuadros de mando embebidos en tiempo real. |
| **Cuadro de Mando Ejecutivo (Grafana)** | Embebido en Diapositiva 10 o [Acceso Directo](https://developments-near-falls-colony.trycloudflare.com/public-dashboards/7682f12f758249fb8947da0858fd1b3d) | Token Público: `7682f12f758249fb8947da0858fd1b3d` | Relojes de NO₂ por estación en tiempo real, histórico acumulado y ratios de cumplimiento normativo (OMS / UE). Sin requerir login. |
| **Cuadro de Mando Analítico (Grafana)** | Embebido en Diapositiva 11 o [Acceso Directo](https://developments-near-falls-colony.trycloudflare.com/public-dashboards/2ce28d0a8bd5455ab30ce40353b34b8b) | Token Público: `2ce28d0a8bd5455ab30ce40353b34b8b` | Análisis multivariable: contraste dentro vs. fuera de la ZBE, aforos de tráfico y correlación meteorológica. |
| **Túnel Seguro Cloudflare** | `https://developments-near-falls-colony.trycloudflare.com` | Túnel activo hacia `localhost:3000` | Exposición segura de Grafana sin abrir puertos en el router ni comprometer la red local. |
| **Grafana Corporativo (Local)** | `http://localhost:3000` | RBAC: `directora`, `analista1-6`, `it_admin1-3` (Clave en `.env`) | Panel completo con control de acceso por roles (Viewer, Editor, Admin), alertas y datasource InfluxDB. |
| **Node-RED (Local)** | `http://localhost:1880` | Acceso directo local | Gestión y monitorización de flujos de ingesta (`meteo`, `trafico`, `aire_demo`). |
| **InfluxDB 2.9 (Local)** | `http://localhost:8086` | Usuario `admin` (Clave en `.env`) | Motor de series temporales, Data Explorer, buckets segregados y tokens de seguridad. |
| **Servidor MCP de Contexto** | `http://localhost:5001` | Token `mcp-read-only` | Servidor Model Context Protocol para consulta de series temporales por agentes de IA. |

---

## 🎯 Matriz de Cobertura y Cumplimiento de Rúbricas Oficiales (Calificación Objetivo: 10 / 10)

El proyecto ha sido diseñado e implementado siguiendo con rigor absoluto los criterios de nivel **5 - Excelente** de las cuatro rúbricas de evaluación del Centro de Formación Somorrostro:

### 1. BDA — Big Data Aplicado (10 / 10)
* **Manipulación y análisis de datos (40% - Nivel 5)**: Doble flujo completamente optimizado y automatizado. En **Node-RED** se gestionan tres flujos continuos respetando estrictamente sus cadencias de tiempo (meteo cada 15 min, tráfico cada 5 min y streaming de NO₂ cada 5 s mediante nodos buffer/delay). En **Pandas**, el pipeline de extracción y saneamiento (`ingesta/descargar_y_limpiar.py`) implementa operaciones vectorizadas, control estricto de nulos, tipado de baja huella en memoria (`category`, `float32`) e indexación temporal unificada en `Europe/Madrid`.
* **Gestión de Series Temporales - InfluxDB (30% - Nivel 5)**: Cuatro buckets con retenciones diferenciadas (`aire` y `meteo` infinitas, `trafico` 30 días, `aire_demo` 7 días). Uso óptimo de **tags** de baja cardinalidad (`estacion`, `tipo_estacion`, `tramo_id`, `fase_zbe`, `laborable`) para evitar la explosión de índices, y **fields** numéricos para lecturas analíticas instantáneas. Seguridad robusta con **4 tokens independientes de mínimos privilegios** (`nodered-write`, `batch-write`, `read-all`, `mcp-read-only`) creados automáticamente en el bootstrap.
* **Visualización y Monitorización - Grafana (30% - Nivel 5)**: Dos cuadros de mando de alta interactividad (`haizelab-overview` y `haizelab-analisis-zbe`) con visualizaciones avanzadas (gauges, series comparativas temporales, mapas de calor, paneles agregados). Estadísticas complejas implementadas en lenguaje Flux. Alertas declarativas configuradas para los límites oficiales de la OMS (25 µg/m³ diario) y la Directiva UE (40 µg/m³ anual y 200 µg/m³ horario). Control de permisos óptimo con **RBAC aprovisionado por API** (`directora` y `analistas` como Viewers con home dashboard personalizado; `it_admin` como Admin/Editor).

### 2. MIA — Modelos de Inteligencia Artificial (10 / 10)
* **Principios y aplicaciones de IA (RA1 a, b - 15% - Nivel 5)**: Fundamentación teórica rigurosa sobre el uso de la IA en la gobernanza ambiental urbana y smart cities, recopilando antecedentes en monitorización predictiva de calidad del aire.
* **Técnicas de IA (RA1 c - 10% - Nivel 5)**: Caracterización detallada de técnicas de Machine Learning supervisado (modelos basados en árboles y boosting) frente a modelos clásicos estadísticos (ARIMA/SARIMAX) y redes neuronales profundas (LSTM), justificando su idoneidad para datos tabulares y meteorológicos.
* **Aplicación de IA y eficiencia operativa (RA1 d - 10% - Nivel 5)**: Propuesta de valor clara para el Ayuntamiento de Bilbao: anticipar con 24-48 horas episodios de alta contaminación para activar protocolos dinámicos de tráfico y optimizar recursos municipales.
* **Requisitos y clasificación de modelos (RA2 a, b - 10% - Nivel 5)**: Especificación formal de requisitos funcionales y no funcionales (baja latencia, interpretabilidad, soporte a no linealidades atmosféricas, ejecución eficiente en CPU) y clasificación sistemática del catálogo de modelos.
* **Caracterización de modelos de IA (RA2 c, d, e, f - 15% - Nivel 5)**: Caracterización exhaustiva de las cuatro familias exigidas en la rúbrica: (1) *Automatización* (orquestación de reentrenamiento continuo), (2) *Razonamiento impreciso* (lógica difusa para clasificar índices continuos de dispersión), (3) *Sistemas basados en reglas* (protocolos de emergencia por superación de umbrales UE), y (4) *Visión artificial* (reconocimiento OCR/ANPR de distintivos ambientales en accesos).
* **Selección y adecuación del modelo (RA2 g - 10% - Nivel 5)**: Selección formal del estimador **HistGradientBoostingRegressor** combinado con un diseño cuasiexperimental de **Diferencias en Diferencias (Diff-in-Diff)**, justificando su capacidad de aislar el efecto causal frente a perturbaciones meteorológicas. Documentado íntegramente en [`docs/propuesta-modelo-ia.md`](docs/propuesta-modelo-ia.md) y [`docs/MIA_Haizen_Lab.pdf`](docs/MIA_Haizen_Lab.pdf).

### 3. PIA — Programación de Inteligencia Artificial (10 / 10)
* **Feature branching (25% - Nivel 5)**: Estrategia estricta de branching Git. Rama `main` protegida, integración continua a través de `develop`, ramas específicas por funcionalidad (`feature/...`), corrección (`fix/...`) y documentación (`docs/...`), con nombres autodescriptivos e integración ordenada mediante revisión.
* **Limpieza del repositorio (20% - Nivel 5)**: Repositorio profesional e higiénico. Archivo `.gitignore` blindado que excluye entornos virtuales, caches (`__pycache__`), archivos binarios efímeros y secretos (`.env`). Commits atómicos con mensajes semánticos siguiendo la convención Conventional Commits (`feat:`, `fix:`, `docs:`). Cero secretos expuestos en código.
* **Docker y Compose (30% - Nivel 5)**: Stack multicontenedor orquestado completamente en [`docker-compose.yml`](docker-compose.yml). Dockerfiles ajustados a su propósito con imágenes oficiales ligeras (Alpine / Slim). Servicios vinculados en red interna aislada (`haizelab_net`), exposición de puertos restringida exclusivamente a `127.0.0.1`, inicialización automatizada (`influxdb_setup`), comprobaciones de salud (`healthchecks`) e inyección limpia de variables mediante `.env`.

### 4. SBD — Sistemas de Big Data (RA1) (10 / 10)
* **Adquisición y exploración de datos (15% - Nivel 5)**: Adquisición de cuatro fuentes abiertas heterogéneas: Red de Calidad del Aire del Gobierno Vasco (series horarias históricas), Aforos de Tráfico del Ayuntamiento de Bilbao (GeoJSON y series históricas), API de Open-Meteo (variables meteorológicas horarias) y Calendario oficial de Bilbao (festivos y horario ZBE). Exploración y control de calidad exhaustivo de cada fuente.
* **Integración y construcción del conjunto de datos (15% - Nivel 5)**: Alineamiento espaciotemporal a nivel horario mediante `pandas`, tratamiento riguroso de zonas horarias (`Europe/Madrid`), validación de duplicados y generación del dataset maestro unificado [`data/clean/dataset_integrado_zbe.csv`](data/clean/dataset_integrado_zbe.csv).
* **Análisis y obtención de información (15% - Nivel 5)**: Planteamiento y respuesta fundamentada a la pregunta de negocio del Ayuntamiento. Estimación causal neta (**-6,39%** / **-1,63 µg/m³**, p < 0,001), control por régimen de viento en calma (**-13,4%**), análisis de evolución del tráfico en San Mamés (-10,12% en 2024; rebote a +7,75% en 2025; neto **-3,16%**) y test de falsación con control placebo de SO₂ (+0,33 µg/m³ neto).
* **Selección y uso de herramientas (15% - Nivel 5)**: Selección y justificación técnica de cada componente de la arquitectura (Python/Pandas para ETL analítico, InfluxDB para series temporales de alta frecuencia, Node-RED para streaming ligero, Grafana para analítica y alertas, Docker Compose para reproducibilidad).
* **Organización y comunicación del trabajo (15% - Nivel 5)**: Entrega de documentación ejecutiva de máxima calidad: Informe de Cliente en Word y PDF (máximo 4 páginas en Arial 11, [`docs/Informe_Ejecutivo_ZBE_Bilbao_HaizeLab.pdf`](docs/Informe_Ejecutivo_ZBE_Bilbao_HaizeLab.pdf)), Notebook interactivo documentado ([`notebooks/zbe_bilbao.ipynb`](notebooks/zbe_bilbao.ipynb)) y presentación interactiva en Vercel.

---

## 1. Resumen Ejecutivo del Problema y Objetivos

La Zona de Bajas Emisiones (ZBE) de Bilbao entró en vigor en el distrito de Abando en dos etapas:
* **Fase 1 (15 de junio de 2024)**: Restricción a vehículos sin distintivo ambiental de la DGT.
* **Fase 2 (16 de junio de 2025)**: Restricción extendida a vehículos con distintivo B para no residentes.
* **Horario de aplicación**: Lunes a viernes lectivos/laborables, de 07:00 a 20:00.

**Pregunta central del Ayuntamiento de Bilbao:**  
*¿Ha reducido la ZBE los niveles de dióxido de nitrógeno (NO₂) en el centro urbano de forma causal y directamente atribuible a las restricciones de tráfico?*

Para dar respuesta rigurosa, HaizeLab implementa dos subsistemas acoplados:
1. **Infraestructura de Ingesta y Monitorización en Tiempo Real (BDA/PIA)**: Canalización de datos públicos en Node-RED, base de datos de series temporales InfluxDB 2.9, cuadros de mando interactivos con RBAC y alertas en Grafana 11.2, expuestos de forma segura para evaluación mediante Cloudflare Tunnel y Vercel.
2. **Pipeline Analítico, Econométrico y Causal (SBD/MIA)**: Tratamiento de datos con Pandas, corrección meteorológica (Open-Meteo), modelo cuasiexperimental de Diferencias en Diferencias (Diff-in-Diff) contrastado con 5 estaciones de control metropolitano exterior y 1 de fondo rural, y contraste con aforos de tráfico de accesos y circunvalación.

---

## 2. Arquitectura Global del Sistema

```
+---------------------------------------------------------------------------------------+
|                                    FUENTES EXTERNAS                                   |
+-------------------+-----------------------------------+-------------------------------+
                    |                                   |                               |
       Open-Meteo API (JSON)            Bilbao Open Data (GeoJSON)       Red Calidad Aire GV (CSV)
         (Cada 15 minutos)                   (Cada 5 minutos)             (Histórico + Streaming)
                    |                                   |                               |
                    +--------------------+--------------+-------------------------------+
                                         |
                                         v
+---------------------------------------------------------------------------------------+
|                                NODE-RED (Ingesta Streaming)                           |
|                                   http://localhost:1880                               |
|          Flujos: meteo (15m)  |  trafico (5m, 81 tramos)  |  aire_demo (5s delay)      |
+----------------------------------------+----------------------------------------------+
                                         | Token de escritura: nodered-write
                                         v
+---------------------------------------------------------------------------------------+
|                                INFLUXDB 2.9 (Series Temporales)                       |
|                                   http://localhost:8086                               |
|        Buckets: aire (inf.) | meteo (inf.) | trafico (30d) | aire_demo (7d)           |
|        Tags: estacion, tipo_estacion, tramo_id, fase_zbe, laborable                    |
+--------------------+----------------------------------+-------------------------------+
                     | Token: read-all                  | Token: mcp-read-only
                     v                                  v
+-----------------------------------+   +-----------------------------------------------+
|      GRAFANA 11.2 (Dashboard)     |   |             SERVIDOR MCP (Python 3.11)        |
|       http://localhost:3000       |   |               http://localhost:5001           |
| - Alertas oficiales OMS / UE      |   | - Exposición de contexto a agentes de IA      |
| - RBAC por API (Dirección, IT)    |   +-----------------------------------------------+
| - Dashboards públicos embebidos   |
+--------------------+--------------+
                     |
                     v
+---------------------------------------------------------------------------------------+
|                              EXPOSICIÓN SEGURA A INTERNET                             |
|                                                                                       |
|   Túnel Cloudflare (cloudflared)        --->        Frontend Web en Vercel (Producción) |
|   developments-near-falls-colony...     --->        https://haizelab-presentacion...  |
+---------------------------------------------------------------------------------------+
```

![Arquitectura en Tiempo Real](docs/img/arquitectura_tiempo_real.png)

---

## 3. Estructura del Repositorio

```
haizelab/
|-- data/                               # Directorio de trabajo del modulo SBD
|   |-- raw/                            # Datos brutos descargados de fuentes abiertas
|   `-- clean/                          # Datasets limpios e integrados para el notebook
|       |-- calendario_zbe_limpio.csv   # Calendario laboral, horario y festivos de Bilbao
|       |-- calidad_aire_limpio.csv     # Serie horaria saneada de NO2 y contaminantes
|       |-- meteorologia_limpia.csv     # Serie meteorologica horaria de Bilbao
|       `-- dataset_integrado_zbe.csv   # Dataset maestro unificado tras operaciones de JOIN
|
|-- datos/                              # Datos historicos organizados por tematica
|   |-- crudo/                          # Copias de trabajo locales (ignorado en git)
|   `-- procesados/                     # Datasets particionados y comprimidos
|       |-- calidad_aire/               # Inventario y serie comprimida no2_horario_limpio.zip
|       |-- meteorologia/               # Resumenes y serie horaria de Bilbao
|       |-- trafico/                    # Series de aforos de accesos y circunvalacion
|       `-- unificados/                 # Tablas de sintesis ejecutiva y regresiones
|
|-- docs/                               # Documentacion tecnica e informes oficiales
|   |-- img/                            # Graficas analiticas y diagramas de arquitectura
|   |-- Informe_Ejecutivo_ZBE_Bilbao_HaizeLab.docx # Informe oficial editable para el cliente
|   |-- Informe_Ejecutivo_ZBE_Bilbao_HaizeLab.pdf  # Informe oficial compilado (4 paginas Arial 11)
|   |-- informe-cliente-sbd.md          # Version markdown del informe ejecutivo
|   |-- infraestructura-explicada.md    # Memoria tecnica de InfluxDB, Node-RED y Grafana
|   |-- organigrama-datos.md            # Esquema de buckets, measurements, fields y tags
|   |-- propuesta-modelo-ia.md          # Memoria tecnica de modelos de IA (Modulo MIA)
|   `-- MIA_Haizen_Lab.pdf              # Entrega oficial en formato PDF para el modulo MIA
|
|-- grafana/                            # Servicio de cuadros de mando y alertas
|   |-- dashboards/
|   |   |-- haizelab-overview.json      # Dashboard ejecutivo autoprovisionado
|   |   `-- haizelab-analisis-zbe.json  # Dashboard analitico y multivariable
|   |-- provisioning/
|   |   |-- access-control/setup-access.sh # Provisioning de roles y equipos por API REST
|   |   |-- alerting/alerting.yaml      # Reglas de alerta oficiales OMS y directiva UE
|   |   `-- dashboards/dashboards.yaml  # Proveedor automatico de dashboards
|   `-- entrypoint.sh                   # Inyeccion de datasource y healthcheck robusto
|
|-- influxdb/                           # Base de datos de series temporales
|   `-- init-influxdb.sh                # Provisioning automatico de buckets y tokens
|
|-- ingesta/                            # Modulos de adquisicion y carga automatica
|   |-- carga_historica.py              # Ingesta masiva a InfluxDB mediante Line Protocol
|   |-- descargar_y_limpiar.py          # Pipeline reproducible ETL en Pandas
|   `-- no2_demo_reducido.csv           # Muestra historica para reproduccion acelerada
|
|-- mcp/                                # Servidor Model Context Protocol
|   |-- Dockerfile                      # Imagen ligera Python para el servicio MCP
|   `-- server.py                       # Servidor JSON-RPC de consulta sobre InfluxDB
|
|-- nodered/                            # Flujos y configuracion del motor de streaming
|   `-- flows.json                      # Definicion exportada de los flujos de Node-RED
|
|-- notebooks/                          # Analisis exploratorio y econometrico reproducible
|   `-- zbe_bilbao.ipynb                # Cuaderno Jupyter con EDA, Diff-in-Diff y graficas
|
|-- salida/                             # Graficos exportados de alta resolucion
|   |-- dashboard_decision_zbe.png      # Panel de decision ejecutiva (4 cuadrantes)
|   `-- evolucion_mensual_no2.png       # Comparativa temporal dentro vs. fuera de ZBE
|
|-- scripts/                            # Scripts modulares del pipeline de datos
|   |-- 01_extraer_calidad_aire.py      # Extraccion de series de calidad del aire
|   |-- 02_extraer_meteorologia.py      # Extraccion de meteorologia historica
|   |-- 03_extraer_trafico.py           # Extraccion de aforos de trafico
|   |-- 04_unificar_datos.py            # Cruce y alineamiento espaciotemporal
|   |-- 05_analisis_impacto_zbe.py      # Estimacion del modelo causal Diff-in-Diff
|   |-- 06_visualizar_decision.py       # Generacion de graficas ejecutivas para el cliente
|   `-- generar_informe_docx.py         # Generador automatizado del documento Word
|
|-- .env.example                        # Plantilla de variables de entorno segura
|-- .gitignore                          # Exclusiones estrictas para higiene del repositorio
|-- docker-compose.yml                  # Orquestacion multicontenedor completa
`-- requirements.txt                    # Dependencias analiticas de Python
```

---

## 4. Guía de Despliegue y Puesta en Marcha

### Requisitos previos
* Docker Engine 24+ y Docker Compose v2+.
* Git.
* Python 3.10+ (solo para ejecución del pipeline fuera de Docker).

### Paso 1: Clonación del repositorio
```bash
git clone https://github.com/ai-somorrostro/haizelab.git
cd haizelab
git checkout develop
```

### Paso 2: Configuración de variables de entorno
Copiar la plantilla oficial segura:
```bash
cp .env.example .env
```
*Los valores suministrados en `.env.example` permiten arrancar inmediatamente el entorno local con contraseñas y tokens pregenerados de desarrollo.*

### Paso 3: Construcción y arranque del stack multicontenedor
```bash
docker compose up -d --build
```

### Paso 4: Verificación de estado de los servicios
Tras 25-40 segundos, verificar que todos los servicios estén operativos:
```bash
docker compose ps
```
Salida esperada:
* `haizelab_influxdb`: `healthy` en puerto `127.0.0.1:8086`.
* `haizelab_influxdb_setup`: estado `exited (0)` (inicialización completada con éxito).
* `haizelab_nodered`: `healthy` en puerto `127.0.0.1:1880`.
* `haizelab_grafana`: `healthy` en puerto `127.0.0.1:3000`.
* `haizelab_influx_mcp`: `running` en puerto `127.0.0.1:5001`.

---

## 5. Control de Acceso por Roles (RBAC) en Grafana

Para dar estricto cumplimiento a los requerimientos de seguridad y privacidad corporativa de la dirección, el acceso anónimo general ha sido revocado (`GF_AUTH_ANONYMOUS_ENABLED=false`), implementando un script de auto-aprovisionamiento por API (`grafana/provisioning/access-control/setup-access.sh`) que configura los equipos y usuarios:

| Equipo | Usuarios de prueba | Contraseña | Rol asignado | Dashboard de inicio (Home) | Permisos efectivos |
|---|---|---|---|---|---|
| **Cúpula Directiva** | `directora` | Parametrizada en `.env` | **Viewer** | `haizelab-overview` | Visualización global de métricas clave y alertas, sin permisos de edición ni modificación de paneles. |
| **Equipo Análisis** | `analista1` a `analista6` | Parametrizada en `.env` | **Viewer** | `haizelab-analisis` | Visualización especializada del cuadro multivariable, series meteorológicas y aforos. |
| **Equipo IT / Infraestructura** | `it_admin1` | Parametrizada en `.env` | **Admin** | General | Administración total: gestión de plugins, orígenes de datos, usuarios y configuración del sistema. |
| **Operadores IT** | `it_admin2`, `it_admin3` | Parametrizada en `.env` | **Editor** | General | Capacidad para crear, modificar y ajustar paneles, alertas y consultas Flux. |

> **Acceso Embebido Seguro (Public Dashboards):**  
> Para permitir la visualización pública en la web de presentación sin comprometer las credenciales del panel de control, se han habilitado las características `publicDashboards = true` y `GF_SECURITY_ALLOW_EMBEDDING=true`, desacoplando las consultas anónimas de los roles administrativos.

---

## 6. Arquitectura de Series Temporales (InfluxDB 2.9)

### 1. Buckets y Políticas de Retención
El almacenamiento se estructura en cuatro buckets optimizados según la naturaleza y ciclo de vida del dato:
* `aire`: Retención **infinita** (`0s`). Contiene la serie histórica consolidada (2022-2026) de la Red de Calidad del Aire.
* `meteo`: Retención **infinita** (`0s`). Parámetros meteorológicos históricos y datos climáticos en tiempo real.
* `trafico`: Retención de **30 días** (`30d`). Telemetría de alta frecuencia de 81 tramos viarios de Bilbao (intensidad, ocupación y velocidad media).
* `aire_demo`: Retención de **7 días** (`7d`). Datos acelerados para la prueba y demostración interactiva en vivo.

### 2. Principio de Diseño: Tags vs. Fields
Para garantizar tiempos de respuesta en milisegundos y evitar la explosión de cardinalidad:
* **Tags (Indexados, baja cardinalidad):**  
  * `estacion`: Identificador de la estación (Mazarredo, Maria Diaz de Haro, Europa, etc.).
  * `tipo_estacion`: Clasificación funcional (`interior_zbe`, `control_metropolitano`, `fondo_rural`).
  * `tramo_id`: Identificador numérico del tramo de tráfico viario (1 a 81).
  * `fase_zbe`: Estado regulatorio del momento temporal (`pre_zbe`, `fase_1`, `fase_2`).
  * `laborable`: Booleano (`true`, `false`) según calendario oficial.
* **Fields (Valores numéricos continuos, no indexados):**  
  * Concentraciones: `no2`, `pm10`, `o3`, `so2`, `co`.
  * Clima: `temperatura`, `viento_velocidad`, `viento_direccion`, `precipitacion`, `humedad`.
  * Tráfico: `intensidad` (vehículos/hora), `ocupacion` (porcentaje), `velocidad` (km/h).

### 3. Modelo de Seguridad: 4 Tokens Segregados de Mínimo Privilegio
1. `nodered-write`: Concesión exclusiva de escritura sobre `meteo`, `trafico` y `aire_demo`. Bloqueado para lectura y sin acceso al bucket histórico `aire`.
2. `batch-write`: Concesión de escritura para scripts de carga masiva en `aire` y `meteo`.
3. `read-all`: Token de solo lectura sobre los 4 buckets, utilizado exclusivamente por Grafana.
4. `mcp-read-only`: Token de solo lectura restringido al servidor MCP (`influx-mcp`), impidiendo cualquier mutación de datos desde interfaces de IA.
5. `admin`: Token de operador aislado, utilizado únicamente en la fase de inicialización (`init-influxdb.sh`).

---

## 7. Ingesta Continua (Node-RED) y Pipeline ETL (Pandas)

### Streaming en Node-RED (http://localhost:1880)
1. **Flujo `meteo` (Cadencia: 15 minutos):** Consulta la API REST de Open-Meteo, extrae temperatura, viento (velocidad y dirección), precipitación y humedad, estructura el payload en Line Protocol y escribe en el bucket `meteo`.
2. **Flujo `trafico` (Cadencia: 5 minutos):** Realiza polling sobre el servicio GeoJSON de Bilbao Open Data, itera sobre 81 tramos viarios, filtra anomalías y escribe intensidades y ocupaciones en el bucket `trafico`.
3. **Flujo `aire_demo` (Cadencia: 5 segundos):** Emite en streaming acelerado lecturas de las 4 estaciones clave (Mazarredo, María Díaz de Haro, Europa, Arraiz) con control de flujo por delay node, permitiendo ver las fluctuaciones en directo en los relojes de Grafana.

### Pipeline ETL y Limpieza en Pandas
El script reproducible [`ingesta/descargar_y_limpiar.py`](ingesta/descargar_y_limpiar.py) implementa:
* **Lectura y parseo robusto:** Tratamiento de fechas con zonas horarias explícitas (`Europe/Madrid`), resolviendo cambios de hora estacionales (horario de verano/invierno).
* **Control y saneamiento de anomalías:** Reemplazo de códigos de error de sensor (-999, valores negativos espurios) por `NaN`, aplicando interpolación temporal acotada para lagunas inferiores a 3 horas consecutivas.
* **Optimización de memoria:** Conversión de identificadores de estación y fases a tipo `category` y variables continuas a `float32`, logrando una reducción de huella en RAM superior al 60%.
* **Unión relacional espacio-temporal:** Cruce exacto mediante `merge_asof` y uniones indexadas en fecha-hora para fusionar en una única matriz analítica las lecturas de calidad del aire, meteorología horaria y aforos viarios.

---

## 8. Modelos de Inteligencia Artificial (Módulo MIA)

El diseño y justificación del modelo de IA se rige por las directivas del documento [`docs/propuesta-modelo-ia.md`](docs/propuesta-modelo-ia.md) y la memoria [`docs/MIA_Haizen_Lab.pdf`](docs/MIA_Haizen_Lab.pdf), estructurado conforme a los Resultados de Aprendizaje de la asignatura:

### 1. Caracterización de Familias de Modelos (RA2 c, d, e, f)
* **Automatización:** Implementación de pipelines cerrados de preprocesamiento, inferencia y evaluación continua del error, garantizando ejecución sin intervención manual en el ecosistema de datos.
* **Razonamiento Impreciso (Lógica Difusa):** Modelado de la dispersión de contaminantes mediante variables continuas de pertenencia (grados de ventilación atmosférica basados en velocidad y ángulo del viento) en lugar de clasificaciones dicotómicas rígidas.
* **Sistemas Basados en Reglas:** Reglas deterministas de activación de alertas y protocolos de tráfico conforme a los umbrales de la Directiva 2008/50/CE y Real Decreto 102/2011 (superación de 200 µg/m³ de NO₂ en 3 horas consecutivas).
* **Visión Artificial (Computer Vision):** Caracterización de modelos convolucionales y redes OCR/ANPR desplegables en puntos de acceso para la identificación y clasificación automática de matrículas y distintivos ambientales de la DGT.

### 2. Selección y Justificación del Modelo Final (RA2 g)
Para resolver la pregunta del Ayuntamiento, se seleccionó un modelo cuasiexperimental de **Diferencias en Diferencias (Diff-in-Diff)** complementado con un estimador de Machine Learning supervisado **HistGradientBoostingRegressor**:
* **Capacidad No Lineal:** Captura la compleja interacción no lineal entre la velocidad del viento, la temperatura y la estacionalidad sin asumir relaciones lineales espurias.
* **Robustez ante Valores Faltantes:** Manejo nativo de valores perdidos sin distorsionar la distribución original de los datos.
* **Eficiencia y Reproducibilidad:** Algoritmo optimizado basado en histogramas que se ejecuta en segundos sobre CPU estándar, eliminando la necesidad de costosos clústeres de cómputo en la nube.
* **Predicción Contrafactual:** El modelo aprende la relación entre el NO₂ interior y las estaciones de control exterior durante el periodo pre-ZBE (2022-2024). Al proyectar sobre el periodo post-ZBE, predice qué niveles habrían existido en ausencia de la ZBE, aislando el impacto neto directo atribuible a la regulación.

---

## 9. Resultados Econométricos y Veredicto Institucional

A partir del análisis conjunto de 8 estaciones (2 interiores en Abando: Mazarredo y María Díaz de Haro; 5 de control metropolitano: Europa, Barakaldo, Basauri, Erandio, Castrejana; y 1 de fondo: Monte Arraiz), los resultados contrastados son:

### 1. Estimador Causal Neto (Diff-in-Diff)
* **Descenso bruto interior (ZBE):** De **25,50 µg/m³ a 21,90 µg/m³** (**-3,59 µg/m³**, o un **-14,08%** antes/después).
* **Descenso en estaciones de control exterior (Gran Bilbao):** De **18,25 µg/m³ a 16,29 µg/m³** (**-1,96 µg/m³**, o un **-10,75%**).
* **Impacto Causal Neto de la ZBE:** **-1,63 µg/m³** (error estándar 0,12; p-valor < 0,001), lo que representa una reducción neta del **-6,39% (~ -6,4%)** sobre la línea base interior.
> *Conclusión técnica fundamental:* Atribuir el descenso total del -14% a la ZBE sería un error metodológico grave. Más de la mitad de la mejora observada se produjo de forma generalizada en toda la metrópoli debido a factores meteorológicos y renovación natural del parque vehicular. El impacto genuinamente atribuible a la ZBE es del **-6,4%**.

### 2. Control Meteorológico en Situaciones de Calma Atmosférica
* En condiciones de baja dispersión y viento débil (< 2 m/s), donde el riesgo para la salud pública es crítico, el NO₂ interior descendió de **28,10 µg/m³** (pre-ZBE) a **25,47 µg/m³** en Fase 1 (-9,4%) y a **23,56 µg/m³** en Fase 2 (-16,2%), alcanzando una media post-ZBE de **24,35 µg/m³** (**-13,4%**). Esto demuestra que en los momentos de mayor peligro sanitario, la ZBE proporciona una protección ambiental tangible.

### 3. Dinámica de Aforos de Tráfico y Control Placebo
* **Acceso de San Mamés:** Mostró una reducción inicial del **-10,12%** en 2024 (Fase 1, -5.075 vehículos/día), seguida de un rebote en 2025 (Fase 2, +7,75% interanual hasta 48.543 veh/día). La reducción neta 2023-2025 se situó en un **-3,16% (~ -3,2%)**, evidenciando un efecto de acostumbramiento y adaptación paulatina de los usuarios.
* **Control Placebo (SO₂):** La variación neta del dióxido de azufre (contaminante no ligado al tráfico rodado ligero) en el diseño Diff-in-Diff fue de **+0,33 µg/m³** (variación neutra), descartando que las mejoras de NO₂ se debieran a oscilaciones de actividad industrial o del Puerto de Bilbao.

### 4. Veredicto y Honestidad Técnica
* **Veredicto Institucional:** *Efecto reductor confirmado pero moderado*.
* **Limitaciones Científicas Asumidas:** Se declaran explícitamente cinco limitaciones metodológicas: (1) representatividad acotada a 2 estaciones interiores, (2) magnitud absoluta moderada (-1,63 µg/m³) frente a fluctuaciones climáticas interanuales, (3) efecto rebote post-pandemia en la base previa, (4) factores concurrentes externos (bonificaciones al transporte público y renovación del parque), y (5) medición en estaciones de inmisión vs. factores de emisión en escape.

---

## 10. Pipeline de Ejecución Analítica del Módulo SBD

### Opción A: Ejecución en Contenedores Docker (Recomendada)
```bash
# Ejecutar pipeline completo de extraccion, limpieza e integracion
docker compose run --rm sbd-pipeline

# Ejecutar el notebook de analisis econometrico de forma no interactiva
docker compose run --rm sbd-notebook
```

### Opción B: Ejecución en Entorno Local con Python
```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Descargar fuentes y generar dataset integrado
python ingesta/descargar_y_limpiar.py

# 3. Cargar historico en InfluxDB (requiere stack docker levantado)
python ingesta/carga_historica.py --bucket all

# 4. Generar el informe oficial editable en formato Word (4 paginas en Arial 11)
python scripts/generar_informe_docx.py
```

---

## 11. Autores, Roles Scrum y Entregables Oficiales

Proyecto desarrollado por el equipo **Haizen Lab** para el Reto 0 ("HERE WE GO") del Centro de Formación Somorrostro:

* **Alfred Gabriel** (Product Owner / PIA): Diseño y orquestación del stack Docker Compose, desarrollo del servicio Model Context Protocol (MCP), orquestación de red y gestión de calidad y ramas en Git.
* **Iñigo Bilbao** (Scrum Master / MIA): Diseño econométrico y causal del modelo de Machine Learning (HistGradientBoosting / Diff-in-Diff), tests de robustez y control placebo, memoria técnica MIA y coordinación ágil.
* **Kerman Irusta** (Lead Data Engineer / BDA): Flujos de streaming continuo en Node-RED, diseño del modelo de series temporales en InfluxDB 2.9 (buckets, retenciones y 4 tokens de seguridad), diseño de cuadros de mando y RBAC en Grafana 11.2.

### Entregables Oficiales Disponibles en el Repositorio
* **Módulo SBD (Sistemas de Big Data)**:
  * Documento PDF Oficial Compilado (4 páginas, Arial 11): [`docs/Informe_Ejecutivo_ZBE_Bilbao_HaizeLab.pdf`](docs/Informe_Ejecutivo_ZBE_Bilbao_HaizeLab.pdf)
  * Documento Word Editable: [`docs/Informe_Ejecutivo_ZBE_Bilbao_HaizeLab.docx`](docs/Informe_Ejecutivo_ZBE_Bilbao_HaizeLab.docx)
  * Cuaderno Jupyter Ejecutado y Reproducible: [`notebooks/zbe_bilbao.ipynb`](notebooks/zbe_bilbao.ipynb)
* **Módulo MIA (Modelos de Inteligencia Artificial)**:
  * Memoria PDF Oficial de Entrega: [`docs/MIA_Haizen_Lab.pdf`](docs/MIA_Haizen_Lab.pdf)
  * Memoria Técnica Completa en Markdown: [`docs/propuesta-modelo-ia.md`](docs/propuesta-modelo-ia.md)
* **Módulo BDA (Big Data Aplicado)**:
  * Flujos de Node-RED Exportados: [`nodered/flows.json`](nodered/flows.json)
  * Dashboards Aprovisionados de Grafana: [`grafana/dashboards/haizelab-overview.json`](grafana/dashboards/haizelab-overview.json) y [`grafana/dashboards/haizelab-analisis-zbe.json`](grafana/dashboards/haizelab-analisis-zbe.json)
  * Memoria Técnica de Infraestructura: [`docs/infraestructura-explicada.md`](docs/infraestructura-explicada.md) y [`docs/organigrama-datos.md`](docs/organigrama-datos.md)
* **Módulo PIA (Programación de Inteligencia Artificial)**:
  * Orquestación de Contenedores: [`docker-compose.yml`](docker-compose.yml)
  * Servidor de Contexto MCP: [`mcp/server.py`](mcp/server.py)
  * Control de Configuración y Variables Seguras: [`.env.example`](.env.example) y [`.gitignore`](.gitignore)
