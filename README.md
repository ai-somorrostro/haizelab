# HaizeLab: Monitorizacion y Analisis Multivariable de la ZBE de Bilbao

> Evaluacion de impacto de la Zona de Bajas Emisiones (ZBE) en la calidad del aire de Bilbao (2022-2026).
> Proyecto desarrollado por el equipo Haizen Lab (Alfred, Inigo y Kerman) para el Reto 0 (SBD, MIA, BDA y PIA).

---

## 1. Resumen y objetivos del proyecto

La Zona de Bajas Emisiones (ZBE) de Bilbao comenzo a operar en el distrito de Abando el 15 de junio de 2024 (Fase 1: restriccion a vehiculos sin distintivo ambiental de la DGT) y el 16 de junio de 2025 (Fase 2: restriccion a vehiculos con distintivo B para no residentes), en horario de lunes a viernes de 7:00 a 20:00.

El objetivo del proyecto es responder con rigor analitico a la pregunta del Ayuntamiento de Bilbao: ¿ha reducido la ZBE los niveles de dioxido de nitrogeno (NO2) en el centro de la ciudad de forma atribuible a las restricciones de trafico?

Para resolver este problema, el repositorio integra dos componentes complementarios:
1. **Infraestructura de datos en tiempo real (BDA)**: Ingesta de fuentes publicas mediante Node-RED, almacenamiento en series temporales con InfluxDB 2.9 y cuadros de mando interactivos con control de acceso por roles en Grafana 11.2.
2. **Pipeline de analisis analitico y econometrico (SBD)**: Control por meteorologia (Open-Meteo), modelo cuasiexperimental de Diferencias en Diferencias (Diff-in-Diff) frente a estaciones de control metropolitano y contraste con aforos de trafico de accesos y circunvalacion.

---

## 2. Arquitectura del sistema

```
                  +----------------------------------------------+
                  |                   FUENTES                    |
                  +-------+--------------+--------------+--------+
                          |              |              |
                    Open-Meteo API   Bilbao Open Data  Historico NO2
                    (cada 15 min)     (cada 5 min)     (Demo acelerada)
                          |              |              |
                          v              v              v
                  +----------------------------------------------+
                  |                   Node-RED                   |
                  |             (http://localhost:1880)          |
                  |   Flujos: meteo | trafico | aire_demo        |
                  +----------------------+-----------------------+
                                         | Token: nodered-write
                                         v
                  +----------------------------------------------+
                  |                  InfluxDB 2                  |
                  |             (http://localhost:8086)          |
                  |   Buckets: aire, meteo, trafico, aire_demo   |
                  +----------------------+-----------------------+
                                         | Token: read-all
                                         v
                  +----------------------------------------------+
                  |                   Grafana                    |
                  |             (http://localhost:3000)          |
                  |   Dashboards, alertas y control de acceso    |
                  +----------------------------------------------+
```

![Arquitectura en Tiempo Real](docs/img/arquitectura_tiempo_real.png)

---

## 3. Estructura del repositorio

```
haizelab/
|-- data/                              # Directorio de trabajo del modulo SBD
|   |-- raw/                           # Datos brutos descargados de fuentes abiertas
|   `-- clean/                         # Datasets limpios e integrados para el notebook
|       |-- calendario_zbe_limpio.csv  # Calendario laboral, horario y festivos de Bilbao
|       |-- calidad_aire_limpio.csv    # Serie horaria saneada de NO2 y contaminantes
|       |-- meteorologia_limpia.csv    # Serie meteorologica horaria de Bilbao
|       `-- dataset_integrado_zbe.csv  # Dataset maestro unificado tras operaciones de JOIN
|
|-- datos/                             # Datos historicos organizados por tematica
|   |-- crudo/                         # Copias de trabajo locales
|   `-- procesados/                    # Datasets particionados y comprimidos para Git
|       |-- calidad_aire/              # Inventario y serie comprimida no2_horario_limpio.zip
|       |-- meteorologia/              # Resumenes y serie horaria de Bilbao
|       |-- trafico/                   # Series de aforos de accesos y circunvalacion
|       `-- unificados/                # Tablas de sintesis ejecutiva y regresiones
|
|-- docs/                              # Documentacion tecnica e informes
|   |-- img/                           # Graficas analiticas y capturas de servicios
|   |-- informe-cliente-sbd.md         # Informe ejecutivo para el cliente (maximo 4 paginas)
|   |-- infraestructura-explicada.md   # Justificacion tecnica de InfluxDB, Node-RED y Grafana
|   `-- organigrama-datos.md           # Esquema org, buckets, measurements, fields y tags
|
|-- grafana/                           # Servicio de cuadros de mando y alertas
|   |-- dashboards/
|   |   `-- haizelab-overview.json     # Dashboard auto-provisionado de la ZBE
|   |-- provisioning/
|   |   |-- access-control/setup-access.sh # Configuracion de equipos y usuarios por API
|   |   |-- alerting/alerting.yaml     # Reglas de alerta oficiales OMS y UE
|   |   `-- dashboards/dashboards.yaml # Proveedor automatico de dashboards
|   `-- entrypoint.sh                  # Inyeccion de token read-all en arranque
|
|-- influxdb/                          # Base de datos de series temporales
|   `-- init-influxdb.sh               # Creacion automatica de buckets y tokens
|
|-- ingesta/                           # Modulos de adquisicion y carga
|   |-- carga_historica.py             # Carga masiva a InfluxDB mediante Line Protocol
|   |-- descargar_y_limpiar.py         # Pipeline reproducible de ETL del modulo SBD
|   `-- no2_demo_reducido.csv          # Muestra historica para reproduccion acelerada
|
|-- notebooks/                         # Analisis interactivo reproducible
|   `-- zbe_bilbao.ipynb               # Cuaderno Jupyter con EDA, Diff-in-Diff y conclusiones
|
|-- salida/                            # Graficos exportados de alta resolucion
|   |-- dashboard_decision_zbe.png     # Panel de decision ejecutiva (4 cuadrantes)
|   `-- evolucion_mensual_no2.png      # Comparativa mensual dentro vs. fuera de la ZBE
|
|-- scripts/                           # Scripts modulares de soporte analitico
|   |-- 01_extraer_calidad_aire.py     # ETL de calidad de aire
|   |-- 02_extraer_meteorologia.py     # ETL de meteorologia
|   |-- 03_extraer_trafico.py          # ETL de aforos de trafico
|   |-- 04_unificar_datos.py           # Cruce y alineamiento espaciotemporal
|   |-- 05_analisis_impacto_zbe.py     # Estimacion del modelo Diff-in-Diff
|   |-- 06_visualizar_decision.py      # Generacion de graficas ejecutivas
|   `-- generar_informe_docx.py        # Generador del informe Word en Arial 11 (4 paginas)
|
|-- .env.example                       # Plantilla de variables de entorno segura
|-- Dockerfile                         # Entorno de ejecucion reproducible Python 3.11
|-- docker-compose.yml                 # Orquestacion multicontenedor completa
`-- requirements.txt                   # Dependencias de Python
```

---

## 4. Guia de puesta en marcha

### Paso 1: Clonar el repositorio y situarse en la rama de trabajo
```bash
git clone https://github.com/ai-somorrostro/haizelab.git
cd haizelab
git checkout develop
```

### Paso 2: Configurar las variables de entorno
Copiar el fichero de ejemplo:
```bash
cp .env.example .env
```
Los valores por defecto permiten arrancar directamente en local de forma segura.

### Paso 3: Arrancar los contenedores
Construir y levantar los servicios en segundo plano:
```bash
docker compose up -d --build
```

### Paso 4: Comprobar el estado de los servicios
Esperar entre 25 y 40 segundos a que InfluxDB y Grafana completen sus comprobaciones de salud:
```bash
docker compose ps
```
Los cuatro servicios deben encontrarse en estado saludable (`Up` o `healthy`):
* `haizelab_influxdb`: puerto `8086`
* `haizelab_influxdb_setup`: finalizado correctamente con codigo `0`
* `haizelab_nodered`: puerto `1880`
* `haizelab_grafana`: puerto `3000`

---

## 5. Acceso a los servicios y credenciales

Todos los puertos quedan expuestos exclusivamente en `127.0.0.1`:

| Servicio | URL Local | Usuario | Clave | Descripcion |
|---|---|---|---|---|
| Grafana | http://localhost:3000 | Usuarios de equipo | Ver tabla de roles | Cuadro de mando y alertas |
| Node-RED | http://localhost:1880 | Libre en local | - | Gestion de flujos de ingesta |
| InfluxDB | http://localhost:8086 | admin | Segun `INFLUXDB_ADMIN_PASSWORD` | Explorador de datos y tokens |

---

## 6. Control de acceso y roles en Grafana

Para dar respuesta a los requerimientos departamentales solicitados por la direccion, se aprovisionan tres equipos diferenciados:

| Equipo | Usuarios de prueba | Clave | Rol en Grafana | Permisos asignados |
|---|---|---|---|---|
| Cupula Directiva | `directora` | `haize2024dir` | Viewer | Visualiza todos los paneles, sin permisos de modificacion |
| Equipo Analisis | `analista1` a `analista6` | `haize2024a1` .. `a6` | Viewer | Acceso de visualizacion a sus paneles asignados |
| Equipo IT | `it_admin1` (Admin), `it_admin2`, `it_admin3` (Editor) | `haize2024it1` .. `it3` | Admin / Editor | Permiso total para editar paneles, datasources y alertas |

---

## 7. Flujos de ingesta en Node-RED

En http://localhost:1880 se encuentran tres flujos automatizados:
1. **meteo (cada 15 minutos)**: Consulta la API de Open-Meteo (Bilbao), procesa variables ambientales y escribe en el bucket `meteo`.
2. **trafico (cada 5 minutos)**: Consulta el servicio GeoJSON de Bilbao Open Data (81 tramos), filtra valores anomalos y escribe en el bucket `trafico`.
3. **aire_demo (cada 5 segundos)**: Emite en streaming acelerado los datos horarios de cuatro estaciones estrategicas (Mazarredo, Maria Diaz de Haro, Europa y Arraiz) para demostraciones en vivo.

---

## 8. InfluxDB 2: Buckets y tokens de acceso

El contenedor inicial `influxdb_setup` genera los buckets con sus politicas de retencion y los tokens de minimo privilegio:

| Bucket | Retencion | Descripcion | Measurement |
|---|---|---|---|
| `aire` | Infinita | Serie historica oficial de contaminantes (2022-2026) | `contaminantes` |
| `meteo` | Infinita | Meteorologia historica y datos en tiempo real | `clima` |
| `trafico` | 30 dias | Intensidad, ocupacion y velocidad de 81 tramos | `estado` |
| `aire_demo` | 7 dias | Datos acelerados para la prueba en vivo | `contaminantes` |

### Tokens segregados:
* `nodered-write`: Escritura permitida exclusivamente en `meteo`, `trafico` y `aire_demo`. No tiene permisos en `aire`.
* `batch-write`: Escritura para scripts de carga masiva en `aire` y `meteo`.
* `read-all`: Lectura sobre los 4 buckets para cuadros de mando y consumidores externos.
* `admin`: Restringido exclusivamente al aprovisionamiento interno del sistema.

---

## 9. Pipeline de analisis del modulo SBD

### Opcion A: Ejecucion dentro de Docker (Recomendada)
```bash
# Descarga, control de calidad e integracion de datos
docker compose run --rm sbd-pipeline

# Ejecucion automatica del notebook completo
docker compose run --rm sbd-notebook
```

### Opcion B: Ejecucion en entorno local
Instalacion de librerias:
```bash
pip install -r requirements.txt
```

Ejecucion del pipeline:
```bash
# 1. Ingesta, limpieza y construccion del dataset integrado
python ingesta/descargar_y_limpiar.py

# 2. Carga historica en InfluxDB (opcional)
python ingesta/carga_historica.py --bucket all

# 3. Generacion del informe impreso en Word (4 paginas en Arial 11)
python scripts/generar_informe_docx.py
```

---

## 10. Resultados principales de la evaluacion de la ZBE

El analisis econometrico realizado en el notebook y sintetizado en el informe ejecutivo muestra los siguientes hallazgos:
1. **Reduccion media observada de NO2**:
   * Dentro de la ZBE (Mazarredo y Maria Diaz de Haro): paso de 25,6 ug/m3 a 21,2 ug/m3 (-17%).
   * En estaciones de control exterior (Gran Bilbao): paso de 15,9 ug/m3 a 13,4 ug/m3 (-16%).
   * Efecto neto del modelo Diff-in-Diff: reduccion neta atribuible a la ZBE de **-1,28 ug/m3** (intervalo de confianza del 95%: +-1,29 ug/m3).
2. **Control meteorologico por regimen de viento**:
   * En situaciones de calma atmosferica (< 2 m/s), donde no hay dispersion y predominan las emisiones del centro, el NO2 interior experimento una reduccion del **-20,5%** (de 30,6 a 24,3 ug/m3).
3. **Contraste con volumenes de trafico**:
   * El acceso principal a la ZBE por San Mames registro un descenso del **-10,12%** (-5.075 vehiculos/dia) tras la entrada en vigor de las restricciones de la Fase 1.

---

## 11. Autores y reparto del proyecto

Proyecto realizado por los alumnos del Centro de Formacion Somorrostro:
* **Alfred Gabriel**: Ingenieria de datos, modelado econometrico y cuaderno analitico SBD.
* **Inigo**: Redaccion del informe ejecutivo para el cliente, diseno de visualizaciones y control de calidad de datos.
* **Kerman**: Despliegue de infraestructura Docker, flujos Node-RED, InfluxDB y configuracion de Grafana.
