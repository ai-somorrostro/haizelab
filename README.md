# HaizeLab: Monitorización y Análisis Multivariable de la ZBE de Bilbao

> **Evaluación de impacto de la Zona de Bajas Emisiones (ZBE) en la calidad del aire de Bilbao (2022-2026).**  
> Reto 0 ("HERE WE GO") — Centro de Formación Somorrostro | Especialización en Inteligencia Artificial y Big Data.  
> **Equipo Haizen Lab:** Alfred Gabriel (PO / PIA), Iñigo Guzman (Lead Data Engineer / BDA), Kerman Irusta (SM / MIA).

---

## 🚀 Despliegue en Vivo y Demostración Interactiva

Para la defensa del proyecto y evaluación, todos los componentes se encuentran desplegados y configurados para acceso interactivo inmediato:

| Entorno / Servicio | Acceso / URL | Credenciales / Token | Finalidad y Estado |
|---|---|---|---|
| **Presentación Web Oficial** | [haizelab-presentacion.vercel.app](https://haizelab-presentacion.vercel.app) | Libre (Acceso público global) | Despliegue en producción (Vercel). Presentación interactiva del proyecto con diapositivas, arquitectura y cuadros de mando embebidos en tiempo real. |
| **Cuadro de Mando Ejecutivo (Grafana)** | Embebido en Diapositiva 10 o [Acceso Directo](https://developments-near-falls-colony.trycloudflare.com/public-dashboards/7682f12f758249fb8947da0858fd1b3d) | Token Público: `7682f12f758249fb8947da0858fd1b3d` | Relojes de NO₂ por estación en tiempo real, histórico acumulado y ratios de cumplimiento normativo (OMS / UE). Sin requerir login. |
| **Cuadro de Mando Analítico (Grafana)** | Embebido en Diapositiva 10 o [Acceso Directo](https://developments-near-falls-colony.trycloudflare.com/public-dashboards/2ce28d0a8bd5455ab30ce40353b34b8b) | Token Público: `2ce28d0a8bd5455ab30ce40353b34b8b` | Análisis multivariable: contraste dentro vs. fuera de la ZBE, aforos de tráfico y correlación meteorológica. |
| **InfluxDB 2.9 (En Vivo / Interactivo)** | Embebido en Diapositiva 11 o [Acceso Directo](https://most-filling-sorry-county.trycloudflare.com) | Usuario `admin` (Credenciales protegidas en `.env`) | Data Explorer, consultas Flux en tiempo real a los 4 buckets y gestión de series temporales. |
| **Node-RED 5.0 (En Vivo / Interactivo)** | Embebido en Diapositiva 11 o [Acceso Directo](https://oclc-abc-gibraltar-store.trycloudflare.com) | Autenticación `adminAuth` (Hash bcrypt protegido) | Editor de flujos de streaming en tiempo real (`meteo`, `trafico`, `aire_demo`). Requiere credenciales de administrador para evitar alteraciones no autorizadas. |
| **Túneles Seguros Cloudflare** | `*.trycloudflare.com` | Cifrado TLS / QUIC sin puertos NAT expuestos | Exposición segura de Grafana, InfluxDB, Node-RED y Chatbot hacia la web en Vercel resolviendo *Mixed Content*. |
| **Grafana Corporativo (Local)** | `http://localhost:3000` | RBAC: `directora`, `analista1-6`, `it_admin1-3` (Clave en `.env`) | Panel completo con control de acceso por roles (Viewer, Editor, Admin), alertas y datasource InfluxDB. |
| **Node-RED (Local)** | `http://localhost:1880` | Acceso directo local | Gestión y monitorización local de flujos de ingesta. |
| **InfluxDB 2.9 (Local)** | `http://localhost:8086` | Usuario `admin` (Clave en `.env`) | Motor de series temporales local. |
| **Servidor MCP de Contexto** | `http://localhost:5001` | Token `mcp-read-only` | Servidor Model Context Protocol para consulta de series temporales por agentes de IA. |
| **HaizeLab Chatbot Assistant (RAG Local)** | `http://localhost:8000` | Libre (CORS habilitado) | Asistente inteligente RAG integrado en la presentación web; responde con datos reales del Reto 0 sin APIs de pago. |

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

## 4. Infraestructura Híbrida: Despliegue en Vercel, Túneles Cloudflare y Visualización Embebida

Para la defensa oficial del proyecto ante el tribunal y evaluación institucional, la arquitectura combina un frontend público global con una pila analítica pesada ejecutada en local:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        WEB PÚBLICA (Vercel)                            │
│  https://haizelab-presentacion.vercel.app (HTTPS / SSL Global)         │
│  - Diapositivas interactivas en HTML5 / CSS3 / JS Vanilla              │
│  - Widget de Chatbot flotante (Estilo Claude Anthropic con RAG local) │
│  - Diapositiva 10: Iframe interactivo de Grafana                       │
│  - Diapositiva 11: Iframes interactivos de InfluxDB y Node-RED         │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
              Peticiones HTTPS     │ Tráfico seguro cifrado (TLS / QUIC)
              (Túneles inversos)   │ [Resuelve bloqueo de Mixed Content]
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   RED PERIMETRAL CLOUDFLARE EDGE                       │
│  *.trycloudflare.com (Certificados SSL oficiales automáticos)          │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │ Conexión saliente QUIC
                                   │ (Sin abrir puertos en el router)
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     STACK LOCAL (Docker Compose)                       │
│  - Grafana 11.2       ──► localhost:3000                               │
│  - InfluxDB 2.9       ──► localhost:8086                               │
│  - Node-RED 5.0       ──► localhost:1880                               │
│  - FastAPI Chatbot    ──► localhost:8000                               │
└────────────────────────────────────────────────────────────────────────┘
```

### ¿Por qué se utilizan Túneles de Cloudflare (`cloudflared`)?
1. **Resolución del bloqueo por *Mixed Content*:** La presentación web está alojada en Vercel bajo `https://` con cifrado SSL. Si un navegador intenta incrustar mediante un `<iframe>` un recurso local HTTP (`http://localhost:3000` o `http://127.0.0.1:1880`), las directivas de seguridad de los navegadores modernos (W3C Mixed Content Specification) **bloquean la conexión inmediatamente** por considerarla insegura. Al usar Cloudflare, los servicios locales reciben una URL pública segura con `https://` y certificado válido, permitiendo su visualización transparente en los iframes.
2. **Exposición remota sin vulnerar la red (Zero Open Ports):** Exponer servicios abriendo puertos en el router de casa o del centro (NAT / Port Forwarding) presenta riesgos severos: expone la IP pública real a escaneos automatizados, ataques de denegación de servicio (DDoS) o intentos de intrusión por fuerza bruta, además de fallar si la conexión utiliza CGNAT. Con `cloudflared`, es la propia máquina local la que inicia una conexión **saliente** cifrada hacia los servidores Anycast de Cloudflare, sin necesidad de abrir ningún puerto entrante en el router ni configurar DNS dinámico.

### Cómo levantar los túneles paso a paso (Windows, Linux, macOS)
El binario oficial de Cloudflare (`cloudflared`) es gratuito y no requiere tarjeta de crédito ni cuenta de pago:

#### 1. Instalación de `cloudflared`
* **Windows (PowerShell con Winget):**
  ```powershell
  winget install --id Cloudflare.cloudflared
  ```
* **Linux (Ubuntu / Debian):**
  ```bash
  curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
  sudo dpkg -i cloudflared.deb
  ```
* **macOS (Homebrew):**
  ```bash
  brew install cloudflared
  ```

#### 2. Comandos para exponer cada servicio
En terminales separadas (o en segundo plano), ejecutar el comando según el servicio que se desee visualizar en la web:

```bash
# Túnel para Grafana (puerto 3000)
cloudflared tunnel --url http://localhost:3000

# Túnel para InfluxDB (puerto 8086)
cloudflared tunnel --url http://localhost:8086

# Túnel para Node-RED (puerto 1880)
cloudflared tunnel --url http://localhost:1880

# Túnel para el Chatbot FastAPI (puerto 8000)
cloudflared tunnel --url http://localhost:8000
```
Cada comando imprimirá en consola una URL efímera segura del tipo:  
`https://<palabras-aleatorias>.trycloudflare.com`

#### 3. Vinculación con la Presentación Web en Vercel
La presentación en Vercel está preparada para enlazar los túneles mediante parámetros en la URL o a través de la interfaz:
* **Para Grafana en Diapositiva 10:**  
  `https://haizelab-presentacion.vercel.app/?grafana=https://<tunel-grafana>.trycloudflare.com#10`
* **Para InfluxDB y Node-RED en Diapositiva 11:**  
  La diapositiva 11 dispone de pestañas interactivas con selector de modo:
  * **Modo Live:** Carga el iframe interactivo en vivo a través del túnel seguro.
  * **Modo Captura (Mockup):** Si el evaluador no tiene el stack local levantado o el túnel está inactivo, la interfaz muestra capturas de alta definición con el esquema y los flujos reales para que cualquier persona en el mundo pueda auditar la arquitectura sin requerir servicios corriendo en su máquina.
  * **Botón Pantalla Completa:** Permite expandir el iframe ocupando el 100% del monitor (pulsar botón cerrar o tecla `Esc` para regresar).

---

## 5. Capa de Seguridad Perimetral, Autenticación y Hardening Defensivo

Al exponer servicios e interactuar con datos en entornos híbridos y de producción, la seguridad se ha diseñado bajo el principio de **Defensa en Profundidad (Defense in Depth)** y **Mínimo Privilegio**. El sistema cuenta con defensas multicapa activas contra accesos no autorizados, ataques de denegación de servicio (DoS), escalada de privilegios y fuga de información:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   CAPA 1: RED PERIMETRAL Y SUPERFICIE                  │
│  - Zero Open Ports: Conexión saliente QUIC mediante Cloudflare Tunnel  │
│  - Reducción de superficie: Puertos de backend (Node-RED :1880 e       │
│    InfluxDB :8086/8085) cerrados a internet; aislados en red Docker.   │
│  - Solo expuestos los servicios de presentación requeridos:            │
│    Grafana (:3000 con RBAC) y Chatbot (:8000 con Rate Limiting).       │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼─────────────────────────────────────┐
│                 CAPA 2: PROTECCIÓN DE LA API DEL CHATBOT               │
│  - Rate Limiting defensivo: Ventana deslizante (máx. 25 req/min por IP)│
│    Corte inmediato con HTTP 429 para prevenir saturación DoS de GPU/CPU│
│  - Validación de entrada: Payload 'message' limitado a máx. 500 chars  │
│    Historial limitado a 10 turnos (Rechazo con HTTP 422 si excede).    │
│  - Guardrail de seguridad: Rechazo automático de temas no afines y     │
│    mitigación de Prompt Injection / Jailbreaks en <0.05s.              │
│  - CORS defensivo: Sin comodín abierto; whitelist estricta Vercel.     │
│  - Ofuscación de red: /info sanitizado sin exponer host.docker.internal│
│  - Manejo seguro de errores: Trazas internas y stack traces ofuscados. │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼─────────────────────────────────────┐
│               CAPA 3: BLINDAJE DE BASES DE DATOS Y PROXY               │
│  - Influx Proxy endurecido: Métodos destructivos (DELETE, PUT, PATCH)  │
│    bloqueados estrictamente con HTTP 403 Forbidden.                    │
│  - Rutas críticas denegadas: Bloqueo de /api/v2/setup, /api/v2/delete,  │
│    /api/v2/authorizations, /api/v2/users y /api/v2/buckets.            │
│  - Prohibición de escalada: Supresión total de auto-inyección de token │
│    o sesión de superadministrador.                                     │
│  - Sin secretos en plano: Contraseñas hardcodeadas eliminadas de raíz. │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼─────────────────────────────────────┐
│              CAPA 4: GESTIÓN DE ACCESO, IDENTIDAD Y TOKENS             │
│  - Segregación estricta de tokens InfluxDB (4 tokens de rol mínimo):   │
│    * nodered-write  ──► Solo escritura en meteo, trafico y aire_demo   │
│    * batch-write    ──► Solo escritura en aire y meteo (ETL batch)     │
│    * grafana-read   ──► Solo lectura en los 4 buckets                  │
│    * mcp-read-only  ──► Solo lectura para servidor MCP                 │
│  - Aislamiento en Grafana entrypoint.sh: Carga única y exclusiva de    │
│    INFLUXDB_READ_TOKEN, sin contaminar el entorno con tokens write.    │
│  - Node-RED adminAuth: Hashing bcrypt reforzado a 12 rondas y secreto  │
│    criptográfico de 32 bytes (openssl rand -hex 32).                   │
│  - Grafana RBAC: Public Dashboards desacoplados del panel de admin     │
│    (GF_AUTH_ANONYMOUS_ENABLED=false) y perfiles diferenciados.         │
└────────────────────────────────────────────────────────────────────────┘
```

### Detalle de las Protecciones Implementadas

#### 1. Protección contra DoS e Inyecciones en la API del Chatbot
* **Prevención de agotamiento de recursos (DoS):** Dado que el asistente realiza inferencia local mediante Ollama (`qwen2.5:1.5b`), un atacante podría saturar la CPU y GPU del host mediante ráfagas masivas. Se ha incorporado un middleware de **Rate Limiting en memoria por IP** configurado a un umbral de 25 peticiones por minuto. Cualquier exceso se corta en seco con un código `HTTP 429 Too Many Requests`.
* **Validación estricta de esquema Pydantic:** Se exige que el mensaje contenga un máximo de 500 caracteres y un historial de no más de 10 mensajes. Entradas que excedan estos límites son rechazadas inmediatamente por el validador con `HTTP 422 Unprocessable Entity` antes de alcanzar el motor RAG.
* **Guardrail de dominio y mitigación de Prompt Injection:** El motor RAG incorpora un filtro previo que analiza la consulta; si se detectan temáticas no relacionadas con el Reto 0 o patrones de manipulación de instrucciones, el asistente declina la respuesta de forma segura en menos de 0.05 segundos sin invocar al modelo pesado.
* **Ofuscación de topología:** El endpoint `/info` no expone URLs de red internas (`host.docker.internal`), y el controlador global de excepciones captura errores devolviendo respuestas genéricas sin filtrar stack traces ni nombres de archivos.

#### 2. Blindaje de Influx Proxy y Prevención de Escalada de Privilegios
* **Bloqueo de operaciones destructivas:** El proxy inverso de InfluxDB intercepta y bloquea cualquier intento de ejecutar llamadas `DELETE`, `PUT` o `PATCH` con un `HTTP 403 Forbidden`.
* **Protección de rutas de administración:** Endpoints críticos de la API de InfluxDB v2 (`/api/v2/setup`, `/api/v2/delete`, `/api/v2/authorizations`, `/api/v2/users`, `/api/v2/buckets`) están explícitamente bloqueados.
* **Eliminación de auto-login admin:** Se ha suprimido la inyección automática de tokens root (`adminToken`) o cookies de superadministrador. Para consultas legítimas de visualización, el proxy utiliza exclusivamente el token de solo lectura (`INFLUXDB_READ_TOKEN`).
* **Higiene de código:** Se han eliminado todas las cadenas de contraseñas por defecto en el código fuente versionado.

#### 3. Control de Acceso y Cifrado en Node-RED
* **Bcrypt de 12 rondas:** La autenticación administrativa `adminAuth` en [`nodered/settings.js`](nodered/settings.js) aplica un coste de computación reforzado de 12 rondas de hashing sobre la contraseña.
* **Cifrado de credenciales en disco:** La directiva `credentialSecret` utiliza una clave pseudoaleatoria criptográficamente segura de 256 bits generada en `.env`, asegurando que los nodos de conexión a InfluxDB almacenados en disco estén cifrados.
* **Eliminación de fallbacks débiles:** `docker-compose.yml` ya no incluye contraseñas por defecto; el servicio exige explícitamente que las variables de entorno existan en el fichero `.env`.

#### 4. Principio de Mínimo Privilegio en Grafana
* **Aislamiento en `entrypoint.sh`:** Grafana monta el volumen de tokens para conectarse a InfluxDB. Para cumplir con el principio de mínimo privilegio, el script de arranque extrae exclusivamente `INFLUXDB_READ_TOKEN`, evitando que las variables de escritura (`INFLUXDB_NODERED_WRITE_TOKEN`, `INFLUXDB_BATCH_WRITE_TOKEN`) queden expuestas en las variables de entorno del contenedor de Grafana.
* **Public Dashboards desacoplados:** Los dashboards embebidos en Vercel utilizan URLs públicas de solo visualización (`/public-dashboards/<uuid>`). El acceso administrativo anónimo está estrictamente desactivado (`GF_AUTH_ANONYMOUS_ENABLED=false`).

---

### Verificación y Auditoría de Seguridad Automatizada

Todas las contramedidas defensivas han sido validadas mediante tests automatizados en el entorno de ejecución:

| Prueba de Seguridad | Vector Auditado | Resultado Obtenido | Estado Defensivo |
|---|---|---|---|
| **Intento de Desbordamiento de Payload** | Envío de mensaje de 501 caracteres al Chatbot | `HTTP 422 Unprocessable Entity` | ✅ **Bloqueado** (Validación Pydantic) |
| **Ataque de Inundación Concurrente (DoS)** | 30 peticiones consecutivas al Chatbot en <3s | `HTTP 429 Too Many Requests` (petición #27) | ✅ **Mitigado** (Rate Limiter activo) |
| **Fuga de Topología de Red** | Consulta de metadatos al endpoint `/info` | `ollama_url` ausente de la respuesta | ✅ **Oculto** (Sin fuga de red interna) |
| **Intento de Borrado de Bucket InfluxDB** | Petición `DELETE /api/v2/buckets/1234` al Proxy | `HTTP 403 Forbidden` | ✅ **Bloqueado** (Verbo destructivo denegado) |
| **Intento de Reconfiguración de Instancia** | Petición `POST /api/v2/setup` al Proxy | `HTTP 403 Forbidden` | ✅ **Bloqueado** (Ruta administrativa protegida) |
| **Intento de Purga de Registros** | Petición `POST /api/v2/delete` al Proxy | `HTTP 403 Forbidden` | ✅ **Bloqueado** (Ruta de borrado denegada) |
| **Verificación de Inyección de Superadmin** | Acceso anónimo a la raíz del Proxy | `Set-Cookie: influxdb-oss-session` Ausente | ✅ **Superado** (Sin auto-escalada de privilegios) |

---

## 6. Guía de Despliegue Universal (Paso a Paso para Cualquier Usuario)

Cualquier evaluador, docente o desarrollador puede clonar y ejecutar este proyecto de forma limpia en su propio equipo (Windows, Linux o Mac) siguiendo estos sencillos pasos:

### Requisitos previos
* **Git** instalado.
* **Docker Engine 24+** y **Docker Compose v2+** (por ejemplo, Docker Desktop en Windows/Mac o docker-ce en Linux).
* *(Opcional)* Python 3.10+ y Ollama si se desea probar el chatbot o ejecutar cuadernos analíticos localmente sin Docker.

### Paso 1: Clonar el repositorio y situarse en la rama de trabajo
```bash
git clone https://github.com/ai-somorrostro/haizelab.git
cd haizelab
git checkout develop
```

### Paso 2: Configurar las variables de entorno
Copiar la plantilla de configuración segura:
```bash
# En Windows (PowerShell) o Linux/macOS (Bash):
cp .env.example .env
```
*La plantilla `.env.example` contiene valores seguros predeterminados para desarrollo local. No es necesario modificar ningún parámetro para una ejecución de prueba inmediata.*

### Paso 3: Levantar la infraestructura completa con Docker Compose
```bash
docker compose up -d --build
```
*Este comando compilará y arrancará en segundo plano los servicios de InfluxDB, Node-RED, Grafana con sus dashboards preconfigurados y el conector MCP.*

### Paso 4: Comprobar que todos los servicios están listos
Tras esperar unos 25-35 segundos para que los scripts de aprovisionamiento finalicen, ejecutar:
```bash
docker compose ps
```
**Salida esperada:**
* `haizelab_influxdb`: Estado `Up (healthy)` en `127.0.0.1:8086`.
* `haizelab_influxdb_setup`: Estado `Exited (0)` (inicialización completada con éxito).
* `haizelab_nodered`: Estado `Up (healthy)` en `127.0.0.1:1880`.
* `haizelab_grafana`: Estado `Up (healthy)` en `127.0.0.1:3000`.
* `haizelab_influx_mcp`: Estado `Up` en `127.0.0.1:5001`.

### Paso 5: Abrir y probar los servicios en el navegador
* **Grafana:** Abrir `http://localhost:3000` (Usuarios de prueba: `directora`, `analista1`, `it_admin1` con contraseñas indicadas en la sección RBAC).
* **Node-RED:** Abrir `http://localhost:1880` (Editor de flujos de streaming continuo).
* **InfluxDB:** Abrir `http://localhost:8086` (Explorador de series temporales y lenguaje Flux).
* **Presentación Web Oficial:** Acceder a [https://haizelab-presentacion.vercel.app](https://haizelab-presentacion.vercel.app) para consultar las diapositivas del proyecto y la defensa técnica.

---

---

## 7. Control de Acceso por Roles (RBAC) en Grafana

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

## 8. Arquitectura de Series Temporales (InfluxDB 2.9)

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

## 9. Ingesta Continua (Node-RED) y Pipeline ETL (Pandas)

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

## 10. Modelos de Inteligencia Artificial (Módulo MIA)

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

## 11. Resultados Econométricos y Veredicto Institucional

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

## 12. Pipeline de Ejecución Analítica del Módulo SBD

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

## 13. Asistente Chatbot RAG Inteligente (HaizeLab Assistant)

Para complementar la defensa del Reto 0 y permitir consultas técnicas interactivas durante la presentación, se ha desarrollado **HaizeLab Assistant**, un asistente conversacional embebido en la esquina inferior derecha de la presentación web ([haizelab-presentacion.vercel.app](https://haizelab-presentacion.vercel.app)).

```
┌────────────────────────────────────────────────────────────────────────┐
│             INTERFAZ DE USUARIO (Inspirada en PcComponentes)           │
│  - Encabezado Índigo Corporativo (#1b054c) con estado en vivo          │
│  - Tipografía equilibrada y legible (13.5px) con respuestas concisas   │
│  - Burbujas de usuario en melocotón suave (#fde5d9)                    │
│  - Respuestas del asistente en fondo blanco con enlaces clicables      │
│  - Botón de reinicio rápido de conversación (#ea580c)                  │
│  - Barra deslizante (slider) para ajustar el tamaño de la ventana      │
│  - Input con foco azul (#0070f3) y aislamiento ergonómico de teclado   │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │ HTTP POST /chat (JSON)
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                BACKEND LIGERO EN FASTAPI (chatbot/main.py)              │
│  - Microservicio Python asíncrono en puerto 8000 con CORS habilitado   │
│  - Endpoints REST: /chat, /health, /info                               │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
         ┌─────────────────────────┴─────────────────────────┐
         │                                                   │
         ▼                                                   ▼
┌──────────────────────────────────┐ ┌──────────────────────────────────┐
│   BASE DE CONOCIMIENTO LOCAL     │ │    MOTOR GENERATIVO LOCAL        │
│   (chatbot/knowledge_base.json)  │ │    (Ollama con Qwen 2.5:1.5b)    │
│  - Cifras exactas del Reto 0     │ │  - Razonamiento conversacional   │
│  - Extracción directa con Pandas │ │  - Respuestas rápidas y fluidas  │
│  - Cero alucinaciones de IA      │ │  - Fallback determinista local   │
└──────────────────────────────────┘ └──────────────────────────────────┘
```

### ¿Cómo se ha hecho el Chatbot de manera sencilla?
La arquitectura se divide en 4 componentes fáciles de entender y mantener:

1. **Frontend Integrado (UI Estilo PcComponentes):**
   * El widget reside directamente en el código de la presentación (`haizelab-presentacion/index.html`).
   * **Tipografía optimizada:** Se redujo el tamaño de fuente a `13.5px` con interlineado natural (`line-height: 1.55`), eliminando los textos gigantescos para que las respuestas sean limpias, proporcionadas y fáciles de leer.
   * **Paleta visual moderna:** Cabecera morada índigo (`#1b054c`), burbujas del usuario en tono melocotón suave (`#fde5d9`), respuestas del asistente sobre blanco puro con enlaces directos en azul subrayado.
   * **Controles ergonómicos:** Botón cuadrado de reinicio con icono de recarga naranja (`#ea580c`), control deslizante para ajustar el ancho y alto del chat según el tamaño del monitor (almacenado automáticamente en `localStorage`), y aislamiento estricto de eventos de teclado (`keydown.stopPropagation()`) para que escribir consultas no active atajos ni cambie de diapositiva.
2. **Backend Ligero (FastAPI en Python):**
   * Ubicado en [`chatbot/main.py`](chatbot/main.py). Es un microservicio de menos de 100 líneas de código que expone el endpoint `/chat`. Recibe la consulta del usuario, recupera el contexto relevante y devuelve la respuesta en formato JSON en cuestión de milisegundos.
3. **Base de Conocimiento RAG (Cero Alucinaciones):**
   * Para evitar que un modelo de lenguaje "invente" datos, el script [`chatbot/precomputar_conocimiento.py`](chatbot/precomputar_conocimiento.py) utiliza Pandas para leer directamente los datasets limpios y precalcular las métricas oficiales en [`chatbot/knowledge_base.json`](chatbot/knowledge_base.json).
   * Contiene los valores exactos: reducción neta de **-1,63 µg/m³** (-6,4%), **41.700 horas** analizadas, variación del tráfico en San Mamés (**-3,16%** neto), estaciones meteorológicas y la autoría oficial del proyecto (**Alfred Gabriel, Iñigo Guzman y Kerman Irusta** con enlace al [repositorio en GitHub](https://github.com/ai-somorrostro/haizelab)).
4. **Razonamiento Local con Ollama (100% Gratuito y Privado):**
   * Si el equipo dispone de **Ollama** con el modelo ligero `qwen2.5:1.5b` (o similar), el backend le inyecta el contexto oficial y el modelo razona la respuesta en lenguaje natural de forma ultrarrápida.
   * Si Ollama no está instalado o no se dispone de tarjeta gráfica, el backend activa automáticamente su **motor determinista de contingencia**: responde de inmediato con las métricas del JSON sin requerir GPUs ni conexión a internet.

### Arranque en un Solo Comando
Cualquiera puede iniciar el chatbot en su propia máquina de dos formas:

#### Opción 1: Con Docker Compose (Recomendada)
```bash
# Levantar el microservicio del chatbot en el puerto 8000
docker compose up -d chatbot

# Comprobar salud del servicio
curl http://127.0.0.1:8000/health
```

#### Opción 2: Con Python local
```bash
cd chatbot
pip install -r requirements.txt
python main.py
```

### Batería de Pruebas Automatizadas (18/18 Superadas)
Para verificar la exactitud de las respuestas y el bloqueo de preguntas ajenas al proyecto, se incluye una suite de pruebas automatizadas:
```bash
python chatbot/test_preguntas.py
```
* **Resultados:** 18 de 18 pruebas superadas (100%), verificando cero discrepancias numéricas en las métricas de NO₂, tráfico y fechas de la ZBE.

---

## 14. Autores, Metodología Scrum y Entregables Oficiales

Proyecto desarrollado por el equipo **Haizen Lab** para el Reto 0 ("HERE WE GO") del Centro de Formación Somorrostro:

* **Alfred Gabriel** (Product Owner / PIA): Diseño y orquestación del stack Docker Compose, desarrollo del servicio Model Context Protocol (MCP), orquestación de red y gestión de calidad y ramas en Git.
* **Iñigo Guzman** (Lead Data Engineer / BDA): Flujos de streaming continuo en Node-RED 5.0, diseño del modelo de series temporales en InfluxDB 2.9 (buckets, retenciones y 4 tokens de seguridad), diseño de cuadros de mando y RBAC en Grafana 11.2 con mapas geoespaciales.
* **Kerman Irusta** (Scrum Master / MIA): Diseño econométrico y causal del modelo de Machine Learning (HistGradientBoosting / Diff-in-Diff), tests de robustez y control placebo, memoria técnica MIA y coordinación ágil.

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
  * Chatbot Asistente RAG Local: [`chatbot/`](chatbot/) (microservicio FastAPI, motor RAG, dataset precalculado y tests).
* **Presentación Web Interactiva**:
  * Código fuente completo de diapositivas y chatbot embebido: [`presentacion/`](presentacion/) (listo para editar y desplegar localmente o en Vercel).
  * Despliegue en producción: [haizelab-presentacion.vercel.app](https://haizelab-presentacion.vercel.app).

---

## 15. Flujo de Trabajo en Git (Feature Branching y Versionado)

Para asegurar la calidad del código, la trazabilidad de los cambios y evitar conflictos entre los tres integrantes del equipo, el proyecto sigue una disciplina estricta de **Feature Branching**:

```
[main]          ───●──────────────────────────────────────────────●───► (Versión de Entrega y Producción)
                   │                                              ▲
                   │                                              │ merge
[develop]       ───●───────────●──────────────────●───────────────●───► (Integración Continua)
                               ▲                  ▲
                      merge    │         merge    │
[feature/...]   ───────────────●                  │
                                                  │
[docs/...]      ──────────────────────────────────●
```

* **Rama `main`:** Rama protegida que contiene únicamente versiones estables y entregas oficiales.
* **Rama `develop`:** Rama principal de integración continua donde convergen las características validadas antes de la release final.
* **Ramas de funcionalidad (`feature/...` y `docs/...`):** Cada tarea o requisito se desarrolla en una rama aislada creada a partir de `develop`. Una vez finalizada y verificada mediante pruebas locales, se integra en `develop` garantizando commits atómicos y mensajes semánticos convencionales (`feat:`, `fix:`, `docs:`, `perf:`).
