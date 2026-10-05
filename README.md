# HaizeLab — Análisis Multivariable del Impacto de la ZBE de Bilbao

Estudio integral de evaluación del impacto de la **Zona de Bajas Emisiones (ZBE) de Bilbao** (aprobada el 15 de junio de 2024), estructurado en una arquitectura modular que combina:
1. **Calidad del Aire (NO₂)**: Red de control continuo de Open Data Euskadi (2022–2026).
2. **Meteorología y Deweathering**: Estación oficial de Monte Banderas (Bilbao).
3. **Aforos Oficiales de Tráfico**: Memorias de intensidad media diaria (IMD) de la Diputación Foral de Bizkaia (2018–2025).

---

## 🧭 Estructura del Proyecto

El proyecto está organizado en capas separadas para garantizar la trazabilidad entre datos crudos, datos limpios, scripts modulares y visualizaciones:

```
haizelab/
├── datos/
│   ├── crudo/                         # Datos brutos originales (sin modificar)
│   │   ├── calidad_aire/              # CSVs originales de Open Data Euskadi (2022–2026)
│   │   ├── meteorologia/              # Ficheros meteorológicos originales (Banderas, Feria...)
│   │   └── trafico/                   # Memorias oficiales en PDF de la Diputación (2022–2025)
│   │
│   └── procesados/                    # Datos limpios y estructurados
│       ├── calidad_aire/              # no2_horario_limpio.csv, inventario_estaciones.csv
│       ├── meteorologia/              # meteo_bilbao_horario.csv, resumen_meteo_periodos.csv
│       ├── trafico/                   # trafico_accesos_bilbao.csv, trafico_circunvalacion.csv
│       └── unificados/                # dataset_unificado_horario.csv, sintesis_ejecutiva_zbe.csv
│
├── docs/                              # Documentación técnica y arquitectura
│   └── infraestructura-explicada.md   # Justificación y decisiones técnicas de InfluxDB y Node-RED
│
├── influxdb/                          # Configuración y provisión de InfluxDB 2
│   └── init-influxdb.sh               # Provisión de buckets y tokens de mínimo privilegio
│
├── ingesta/                           # Pipelines de preparación para ingesta continua
│   ├── preparar_datos_demo.py         # Extracción de subconjunto de demo de NO2
│   └── no2_demo_reducido.csv          # Dataset local para demo (ignorado en git)
│
├── nodered/                           # Servicio de flujos Node-RED
│   ├── Dockerfile                     # Imagen personalizada con node-red-contrib-influxdb
│   ├── entrypoint.sh                  # Inyección segura de tokens sin persistencia en git
│   ├── flows.json                     # Flujos declarativos (meteo, tráfico, aire_demo)
│   └── settings.js                    # Configuración de runtime y módulos externos
│
├── grafana/                           # Servicio de visualización y dashboards
│   ├── entrypoint.sh                  # Inyección automática del token read-all en datasource
│   ├── generate_dashboard.py          # Script generador del cuadro de mando en JSON
│   ├── dashboards/                    # Manifiesto del dashboard ZBE Bilbao
│   └── provisioning/                  # Configuración de auto-aprovisionamiento
│
├── scripts/                           # Scripts modulares y descriptivos
│   ├── 01_extraer_calidad_aire.py     # Limpia y clasifica NO2 horario (Dentro / Fuera / Fondo)
│   ├── 02_extraer_meteorologia.py     # Estandariza fechas y variables climáticas de Bilbao
│   ├── 03_extraer_trafico.py          # Extrae con PyMuPDF las tablas de aforos de los PDFs
│   ├── 04_unificar_datos.py           # Cruza calidad del aire + meteo + tráfico por hora
│   ├── 05_analisis_impacto_zbe.py     # Modelo Diff-in-Diff y control estratificado por viento
│   └── 06_visualizar_decision.py      # Genera el dashboard de decisión ejecutiva y gráficos
│
├── salida/                            # Informes gráficos para toma de decisión
│   ├── dashboard_decision_zbe.png     # Dashboard integral de 4 paneles para decisión
│   └── evolucion_mensual_no2.png      # Gráfico de serie temporal mensual de NO2
│
├── ejecutar_todo.py                   # Orquestador para correr todo el pipeline en 1 comando
├── Dockerfile                         # Contenedor reproducible (Python 3.11-slim)
├── docker-compose.yml                 # Orquestación de servicios Docker
├── requirements.txt                   # Dependencias Python
└── .gitignore                         # Excluye datos crudos y ficheros pesados
```

---

## 🎯 Panel para la Toma de Decisión: ¿Avanzamos con el Proyecto?

El script `scripts/06_visualizar_decision.py` genera el dashboard `salida/dashboard_decision_zbe.png` estructurado en **4 pruebas empíricas**:

### 1. Prueba de Calidad del Aire (NO₂)
* **Dentro ZBE** (Mazarredo + Mª Díaz de Haro): cayó de **25.62 µg/m³** a **21.89 µg/m³** (**-14.6%**).
* **Control Urbano Fuera ZBE** (18 estaciones Gran Bilbao): cayó de 15.92 µg/m³ a 13.71 µg/m³ (-13.9%).
* **Efecto Neto Dentro vs Fuera (Diff-in-Diff)**: **-1.59 µg/m³** de reducción adicional en el interior de la ZBE.

### 2. Prueba Causal de Tráfico (Accesos Oficiales a Bilbao)
* **Acceso San Mamés** (principal vía de acceso hacia la ZBE / Ensanche):
  * 2022: 51.386 veh./día
  * 2023: 50.127 veh./día
  * **2024: 45.052 veh./día (-10.12% de desplome en el año de implantación de la ZBE)**.
* Los accesos de circunvalación norte (ej. Deusto-Enekuri) subieron un +3.01%, demostrando desvío de tráfico hacia las rondas.

### 3. Prueba de Control Climático (Monte Banderas)
Al estratificar el NO₂ por régimen de viento en Bilbao para aislar el factor meteorológico:
* **En calma atmosférica (< 2 m/s)** (cuando el viento no dispersa y dominan las emisiones locales):
  * Pre-ZBE: **32.32 µg/m³**
  * Post-ZBE: **26.78 µg/m³** (**-17.14% de reducción neta en calma**).
* La velocidad del viento post-ZBE fue ligeramente menor (4.12 m/s frente a 4.29 m/s previo), descartando que el aire se limpiara por causas meteorológicas.

> **VEREDICTO**: **PROYECTO VIABLE Y JUSTIFICADO**.
> Existe coherencia causal completa: la restricción ZBE provocó un descenso real de tráfico (-10% en San Mamés) que redujo el NO₂ en el centro (-17% en calma atmosférica), superando el efecto de la tendencia metropolitana.

---

## 🚀 Cómo Ejecutar el Pipeline

### Opción 1: Pipeline Completo en 1 Comando
```bash
python ejecutar_todo.py
```

### Opción 2: Ejecutar Módulos Individuales
```bash
# 1. Extraer Calidad del Aire
python scripts/01_extraer_calidad_aire.py

# 2. Extraer Meteorología
python scripts/02_extraer_meteorologia.py

# 3. Extraer Tráfico desde los PDFs
python scripts/03_extraer_trafico.py

# 4. Unificar Datasets
python scripts/04_unificar_datos.py

# 5. Análisis Estadístico y Diff-in-Diff
python scripts/05_analisis_impacto_zbe.py

# 6. Generar Gráficos y Dashboard de Decisión
python scripts/06_visualizar_decision.py
```

### Opción 3: Con Docker (sin instalar dependencias)
```bash
# Todo el pipeline en un solo contenedor
docker compose run --rm todo

# O un servicio específico
docker compose run --rm extraer
docker compose run --rm analisis
docker compose run --rm visualizar
```

---

## 📦 Dependencias

Instalación rápida en local:
```bash
pip install -r requirements.txt
```
Librerías principales: `pandas>=2.0`, `numpy>=1.24`, `matplotlib>=3.7`, `scipy>=1.11`, `pymupdf>=1.24`, `openpyxl>=3.1`.


---

## 🐳 Infraestructura: InfluxDB, Node-RED y Grafana

En esta sección explico cómo funciona la capa de datos en tiempo real que he añadido al proyecto.
Permite consultar y visualizar métricas de calidad del aire, meteorología y tráfico en directo.

### Requisitos previos

- Docker >= 24 con Docker Compose v2 (incluido en Docker Desktop)
- 2 GB de RAM libres para los contenedores
- Puertos 8086, 1880 y 3000 disponibles en localhost (`127.0.0.1`)

### Primer arranque (desde cero)

```bash
# 1. Copiar el fichero de variables de entorno y editar con credenciales reales
cp .env.example .env
# Editar .env con un editor de texto

# 2. Generar el CSV reducido para la demo de NO2 (solo la primera vez)
python ingesta/preparar_datos_demo.py

# 3. Arrancar todos los servicios
docker compose up -d --build

# 4. Comprobar estado (esperar ~60 s al primer arranque)
docker compose ps
```

### Reinicio (sin borrar datos)

```bash
docker compose up -d
```

### Borrar todo (incluidos datos de InfluxDB)

```bash
docker compose down -v
```

### Variables de entorno (.env)

| Variable | Descripcion | Ejemplo |
|---|---|---|
| `INFLUXDB_ORG` | Nombre de la organizacion en InfluxDB | `haizenlab` |
| `INFLUXDB_BUCKET_PRINCIPAL` | Bucket principal (datos historicos ZBE) | `aire` |
| `INFLUXDB_ADMIN_USER` | Usuario administrador de InfluxDB | `admin` |
| `INFLUXDB_ADMIN_PASSWORD` | Contrasena del administrador | *(segura)* |
| `INFLUXDB_ADMIN_TOKEN` | Token maestro de InfluxDB | *(aleatorio largo)* |
| `INFLUXDB_RETENTION_METEO` | Retencion bucket meteo (segundos) | `7776000` (90 dias) |
| `INFLUXDB_RETENTION_TRAFICO` | Retencion bucket trafico (segundos) | `2592000` (30 dias) |
| `INFLUXDB_RETENTION_AIRE_DEMO` | Retencion bucket aire_demo (segundos) | `604800` (7 dias) |

Los tokens `INFLUXDB_NODERED_WRITE_TOKEN` e `INFLUXDB_READ_TOKEN` se generan
automaticamente en el primer arranque y se almacenan en el volumen `influxdb_tokens`
(nunca en git).

### Buckets de InfluxDB

| Bucket | Measurement | Tags | Fields | Retencion |
|---|---|---|---|---|
| `aire` | *(datos historicos ZBE)* | — | — | Infinita |
| `meteo` | `clima` | `ubicacion`, `fuente` | `temp_c`, `viento_kmh`, `viento_dir`, `lluvia_mm`, `humedad` | 90 dias |
| `trafico` | `estado` | `codigo_seccion` | `intensidad`, `ocupacion`, `velocidad` | 30 dias |
| `aire_demo` | `contaminantes` | `estacion`, `zona` | `no2`, `fecha_original` | 7 dias |

> **Nota sobre el viento**: El historico `datos/procesados/meteorologia/meteo_bilbao_horario.csv`
> guarda el viento en **m/s**. El flujo `meteo` solicita a Open-Meteo los datos en **km/h**
> (`wind_speed_unit=kmh`). Si en el futuro se carga el historico en InfluxDB,
> multiplicar la columna de viento por 3.6 antes de ingresarla.

### Tokens y permisos

| Token | Permisos | Usado por |
|---|---|---|
| Admin (`INFLUXDB_ADMIN_TOKEN`) | Todo | Solo docker-compose (setup inicial) |
| nodered-write | Escritura en `meteo`, `trafico`, `aire_demo` (no en `aire`) | Node-RED |
| read-all | Lectura en los 4 buckets | Grafana (puerto 3000), MCP (futuro) |

### Visualización en Grafana (Puerto 3000)

Grafana 11.2.0 está integrado en Docker Compose con auto-provisionamiento completo:
- **URL:** [http://localhost:3000](http://localhost:3000)
- **Acceso:** Acceso directo habilitado (o usuario `admin` con la contraseña configurada en `.env`).
- **Datasource:** `InfluxDB-HaizeLab` (Flux, organización `haizenlab`, token de lectura `read-all` inyectado dinámicamente).
- **Dashboard:** `HaizeLab — Monitor ZBE Bilbao en Tiempo Real` cargado por defecto:
  - **Calidad del Aire (ZBE):** Indicadores y calibradores (*gauges*) con umbrales de alerta y evolución temporal de NO₂ comparando dentro vs fuera de la ZBE.
  - **Meteorología:** Series temporales de temperatura, humedad, viento y lluvia en Bilbao.
  - **Tráfico:** Intensidad vehicular media, ocupación de vías y velocidad.

### Flujos de Node-RED

| Flujo | Frecuencia | Fuente | Destino |
|---|---|---|---|
| **meteo** | Cada 15 min | [Open-Meteo API](https://api.open-meteo.com) (Bilbao 43.263,-2.935) | `meteo` → `clima` |
| **trafico** | Cada 5 min | [Bilbao Open Data](https://www.bilbao.eus/aytoonline/srvDatasetTrafico?formato=geojson) (81 tramos) | `trafico` → `estado` |
| **aire_demo** | Cada 5 s | `ingesta/no2_demo_reducido.csv` (4 estaciones, 2022-2026) | `aire_demo` → `contaminantes` |

**Campos del API de trafico Bilbao** (verificados 2026-10-05):
- `CodigoSeccion`: identificador unico del tramo (81 valores)
- `Intensidad`: vehiculos/hora (integer)
- `Ocupacion`: porcentaje de ocupacion de la via 0-100 (integer)
- `Velocidad`: velocidad media km/h (integer)
- `FechaHora`: timestamp de la ultima medicion del sensor

**Estaciones flujo aire_demo**:
- `Mazarredo` (zona: dentro ZBE)
- `MDiazDeHaro` (zona: dentro ZBE — reclasificacion de M_DIAZ_HARO)
- `Europa` (zona: fuera ZBE)
- `Arraiz` (zona: fondo regional)

### Como comprobar que llegan datos

```bash
# Ver estado de los contenedores
docker compose ps

# Logs en tiempo real
docker compose logs -f nodered
docker compose logs -f influxdb

# Consultar datos con la CLI de InfluxDB (dentro del contenedor)
docker exec haizelab_influxdb influx query \
  --org haizenlab \
  --token <INFLUXDB_ADMIN_TOKEN> \
  'from(bucket:"meteo") |> range(start:-1h) |> limit(n:5)'

# Interfaz web de InfluxDB
# Abrir http://localhost:8086 en el navegador
# Usuario: admin, Contrasena: la de .env

# Editor de flujos de Node-RED
# Abrir http://localhost:1880 en el navegador
```
