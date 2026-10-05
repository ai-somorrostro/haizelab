# Arquitectura de Infraestructura: InfluxDB 2 y Node-RED en HaizeLab

Este documento detalla todas las decisiones técnicas, arquitectónicas y de seguridad adoptadas para la capa de streaming e ingesta en tiempo real del proyecto **HaizeLab**. Está diseñado tanto como registro de ingeniería como material de estudio riguroso para evaluaciones técnicas en administración de sistemas (ASIR), bases de datos de series temporales (TSDB) y pipelines de datos.

---

## 1. Visión General y Diagrama de Arquitectura

El proyecto HaizeLab analiza el impacto causal de la Zona de Bajas Emisiones (ZBE) de Bilbao sobre la concentración de dióxido de nitrógeno ($NO_2$). Para complementar los scripts analíticos por lotes (batch) existentes en `scripts/`, esta infraestructura añade una plataforma de procesamiento continuo basada en contenedores Docker:

1. **Almacenamiento temporal**: Base de datos de series temporales InfluxDB 2.x.
2. **Orquestación de ingesta**: Node-RED con flujos periódicos para meteorología, tráfico y reproducción acelerada de calidad del aire.
3. **Aprovisionamiento automatizado**: Contenedor efímero de inicialización que asegura el despliegue con un solo comando (`docker compose up -d --build`).

```
                              ┌────────────────────────────────────────────────────────┐
                              │                 HOST (127.0.0.1)                       │
                              │                                                        │
                              │  Navegador Web / Cliente HTTP                         │
                              │   ├── http://localhost:8086 (InfluxDB UI)              │
                              │   └── http://localhost:1880 (Node-RED Editor)          │
                              └───────────────┬────────────────────────┬───────────────┘
                                              │ :8086                  │ :1880
                                              ▼                        ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ Docker Network (Bridge interno: haizelab_default)                                      │
│                                                                                        │
│   ┌──────────────────────────┐                      ┌──────────────────────────────┐   │
│   │   haizelab_influxdb      │                      │      haizelab_nodered        │   │
│   │   (influxdb:2.9.1)       │                      │   (haizelab_nodered:latest)  │   │
│   │                          │◀─── Escribe datos ───│                              │   │
│   │   - Bucket: aire         │      (meteo/trafico/ │   - Flujo meteo (15 min)     │   │
│   │   - Bucket: meteo        │       aire_demo)     │   - Flujo trafico (5 min)    │   │
│   │   - Bucket: trafico      │   http://influxdb    │   - Flujo aire_demo (5 s)    │   │
│   │   - Bucket: aire_demo    │        :8086         │                              │   │
│   └─────────────┬────────────┘                      └──────────────▲───────────────┘   │
│                 │                                                  │                   │
│                 │ depends_on: healthy                              │ depends_on:       │
│                 ▼                                                  │ completed         │
│   ┌──────────────────────────┐                                     │                   │
│   │  haizelab_influxdb_setup │                                     │                   │
│   │   (contenedor efímero)   │                                     │                   │
│   │                          │                                     │                   │
│   │   1. Crea buckets        │                                     │                   │
│   │   2. Genera tokens       │                                     │                   │
│   │   3. Escribe tokens.env  ├──────────────┐                      │                   │
│   └──────────────────────────┘              │                      │                   │
│                                             ▼                      │                   │
│                           ┌───────────────────────────────────┐    │                   │
│                           │ Volumen compartido:               │────┘                   │
│                           │ influxdb_tokens (/tokens)         │    Lee tokens en       │
│                           │   └── tokens.env                  │    entrypoint.sh       │
│                           └───────────────────────────────────┘    (solo lectura)      │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. InfluxDB 2: Justificación y Modelado de Series Temporales

### 2.1. Elección de InfluxDB frente a Alternativas

| Tecnología | Evaluación en este contexto | Decisión |
|---|---|---|
| **InfluxDB 2.x** | Diseñada específicamente para series temporales. Soporta retenciones nativas por bucket, consultas en Flux, interfaz gráfica integrada para depuración rápida y bajo consumo de recursos (<200 MB RAM). | **Seleccionada** |
| **InfluxDB 1.8** | Modelo legado basado en bases de datos y usuarios tradicionales. Carece de interfaz web integrada y no permite control granular por tokens modernos basados en organizaciones. | Descartada |
| **InfluxDB 3.x** | Basada en Apache Arrow, DataFusion y formato Parquet. Desde septiembre de 2026 la etiqueta `latest` apunta a InfluxDB 3; sin embargo, no incluye la interfaz web embebida de la versión 2, su modelo de inicialización por variables de entorno difiere notablemente y aún no cuenta con soporte consolidado en todos los nodos comunitarios de Node-RED. | Descartada |
| **TimescaleDB (PostgreSQL)** | Excelente para unificar datos relacionales y series temporales, pero su huella en disco y memoria es significativamente mayor y requiere migraciones de esquema SQL continuas ante cambios en sensores. | Descartada |
| **MongoDB** | Aunque soporta colecciones de series temporales desde la versión 5.0, la gestión de retención automática y el procesamiento temporal por ventanas deslizantes añade complejidad frente a un motor nativo TSDB. | Descartada |

### 2.2. Fijado Estricto de Versión (`influxdb:2.9.1`)

Se utiliza la imagen `influxdb:2.9.1` de forma explícita. Nunca debe emplearse `latest` en entornos productivos ni académicos reproducibles:
- Previene roturas involuntarias por cambios mayores de versión (como el salto a InfluxDB 3).
- Garantiza que cualquier miembro del equipo o evaluador obtenga exactamente el mismo comportamiento, binarios y sintaxis de CLI (`influx bucket`, `influx auth`).

### 2.3. Esquema de Buckets y Políticas de Retención

InfluxDB 2 organiza los datos en **Buckets**, cada uno con su propia política de retención (*Retention Policy*):

| Bucket | Measurement | Retención | Justificación de Retención |
|---|---|---|---|
| `aire` | *(Histórico ZBE)* | **Infinita** (`0s`) | Contiene los datos maestros oficiales de 2022 a 2026. Es la base del estudio científico y del análisis de decisión ejecutiva; su borrado accidental invalidaría el proyecto. |
| `meteo` | `clima` | **90 días** (`7776000s`) | Suficiente para correlacionar episodios de alta contaminación con regímenes de viento recientes y variabilidad estacional sin consumir espacio indefinido. |
| `trafico` | `estado` | **30 días** (`2592000s`) | Con 81 secciones de tráfico emitiendo cada 5 minutos ($81 \times 12 \times 24 = 23.328$ puntos diarios), 30 días acumulan ~700.000 puntos, volumen óptimo para patrones semanales y laborales sin sobrecargar el índice TSM. |
| `aire_demo` | `contaminantes` | **7 días** (`604800s`) | Flujo de demostración en bucle acelerado (1 tick cada 5 segundos). Genera 17.280 puntos diarios destinados a ilustrar el funcionamiento en tiempo real, por lo que una semana es más que suficiente. |

### 2.4. Modelado: Tags frente a Fields (Control de Cardinalidad)

En los motores de series temporales con índice invertido (Time Series Index - TSI), la **cardinalidad** es el producto cartesiano del número de valores únicos de todos los tags. Una cardinalidad descontrolada provoca consumo masivo de memoria RAM (*Out Of Memory*).

- **Tags (Indexados)**: Metadatos con número finito y reducido de valores únicos:
  - `ubicacion` (`bilbao`), `fuente` (`open-meteo`).
  - `codigo_seccion` (81 tramos fijos de la red viaria de Bilbao).
  - `estacion` (4 estaciones fijas: Mazarredo, Mª Díaz de Haro, Europa, Arraiz), `zona` (`dentro`, `fuera`, `fondo`).
- **Fields (No Indexados)**: Valores numéricos continuos medidos en el tiempo:
  - `temp_c`, `viento_kmh`, `viento_dir`, `lluvia_mm`, `humedad`.
  - `intensidad`, `ocupacion`, `velocidad`.
  - `no2`, `fecha_original`.

*Regla crítica aplicada*: Jamás se almacena un valor continuo (como la velocidad o el $NO_2$) como tag. Hacerlo crearía una serie temporal nueva por cada medición, degradando el rendimiento de InfluxDB.

---

## 3. Aprovisionamiento Automatizado e Idempotencia (`influxdb_setup`)

### 3.1. Por qué un Contenedor Efímero de Inicialización

La imagen oficial de InfluxDB en modo `setup` automático mediante variables de entorno (`DOCKER_INFLUXDB_INIT_*`) solo permite definir **un único bucket inicial** y **un único token administrador maestro**. No ofrece mecanismos nativos para:
- Crear múltiples buckets complementarios con diferentes retenciones.
- Generar tokens secundarios con permisos restringidos de solo lectura o escritura segmentada.

Para resolver esto sin intervención manual, se diseñó el servicio `influxdb_setup`:
1. Utiliza la misma imagen `influxdb:2.9.1` con la CLI `influx` ya instalada.
2. Espera mediante `depends_on: condition: service_healthy` a que el motor de InfluxDB responda con código 200 en su endpoint de salud (`influx ping`).
3. Ejecuta `influxdb/init-influxdb.sh` para crear los buckets restantes y los tokens específicos.
4. Finaliza su ejecución (`restart: "no"`).

### 3.2. Idempotencia y Persistencia en Reinicios

Un sistema es **idempotente** si ejecutarlo varias veces produce el mismo estado que ejecutarlo una sola vez.

En `influxdb/init-influxdb.sh`:
```sh
if [ -f "$TOKENS_FILE" ]; then
  echo "[setup] $TOKENS_FILE ya existe, saltando creacion de buckets y tokens."
  exit 0
fi
```
- **Primer arranque (`docker compose up -d --build`)**: El volumen `influxdb_tokens` está vacío. El script crea los buckets si no existen, genera los tokens con permisos mínimos y escribe `/tokens/tokens.env`.
- **Reinicios cotidianos (`docker compose up -d`)**: InfluxDB arranca con los datos intactos en `influxdb_data`. `influxdb_setup` detecta que `tokens.env` ya existe en el volumen y termina de inmediato sin duplicar tokens ni arrojar errores.
- **Limpieza total (`docker compose down -v`)**: Los volúmenes se eliminan y el siguiente arranque vuelve a configurarlo todo de manera transparente.

---

## 4. Seguridad: Mínimo Privilegio y Entrega Segura de Tokens

### 4.1. Separación de Responsabilidades y Tokens

El principio de mínimo privilegio (*Principle of Least Privilege*) exige que cada componente de software posea únicamente las autorizaciones estrictamente indispensables para cumplir su labor.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ InfluxDB Authorization Matrix                                                   │
├────────────────────┬──────────┬───────────┬────────────┬─────────────┬──────────┤
│ Token              │ aire     │ meteo     │ trafico    │ aire_demo   │ Admin    │
├────────────────────┼──────────┼───────────┼────────────┼─────────────┼──────────┤
│ Admin Master       │ Read/Wr  │ Read/Wr   │ Read/Wr    │ Read/Wr     │ SI       │
│ nodered-write      │ DENEGADO │ ESCRITURA │ ESCRITURA  │ ESCRITURA   │ NO       │
│ read-all           │ LECTURA  │ LECTURA   │ LECTURA    │ LECTURA     │ NO       │
└────────────────────┴──────────┴───────────┴────────────┴─────────────┴──────────┘
```

1. **Token Maestro (`INFLUXDB_ADMIN_TOKEN`)**:
   - Definido en `.env`.
   - Utilizado exclusivamente por `influxdb` para el arranque inicial y por `influxdb_setup` para emitir los tokens restringidos.
   - **Nunca se le entrega a Node-RED ni a los dashboards de visualización**.
2. **Token de Escritura de Node-RED (`INFLUXDB_NODERED_WRITE_TOKEN`)**:
   - Generado dinámicamente con permisos de escritura limitados a los IDs de los buckets `meteo`, `trafico` y `aire_demo`.
   - **No tiene permiso de escritura sobre `aire`**: esto garantiza matemáticamente que ningún bug, inyección o fallo en los flujos de Node-RED pueda corromper o sobrescribir los datos maestros del proyecto.
3. **Token de Lectura (`INFLUXDB_READ_TOKEN`)**:
   - Generado con permiso exclusivo de solo lectura sobre los 4 buckets.
   - Pensado para servidores externos de métricas, agentes de IA (protocolo MCP) o paneles de Grafana que solo necesitan realizar consultas analíticas.

### 4.2. Cómo Viaja el Token a Node-RED (Sin Git y Sin Pasos Manuales)

#### Solución implementada: Volumen compartido interno + Script de entrada (`entrypoint.sh`)
1. El contenedor `influxdb_setup` escribe en `/tokens/tokens.env` dentro del volumen nombrado `influxdb_tokens`.
2. El contenedor `nodered` monta dicho volumen en modo solo lectura (`influxdb_tokens:/tokens:ro`).
3. El script `nodered/entrypoint.sh` se ejecuta antes de Node-RED:
   - Espera en bucle hasta que `/tokens/tokens.env` esté disponible (con timeout de seguridad).
   - Exporta `INFLUXDB_NODERED_WRITE_TOKEN` e `INFLUXDB_READ_TOKEN` como variables de entorno del proceso.
   - Ejecuta Node-RED mediante `exec node ...`, heredando dichas variables de forma nativa.
4. En los flujos de Node-RED, los nodos de función inyectan el token dinámicamente mediante `msg.token = env.get('INFLUXDB_NODERED_WRITE_TOKEN')`.

#### Alternativas analizadas y descartadas

| Alternativa | Descripción | Causa del descarte |
|---|---|---|
| **Token estático en `.env`** | Definir el token de Node-RED manualmente en el fichero `.env`. | En InfluxDB 2, los tokens asociados a buckets específicos requieren conocer el ID del bucket, que se genera aleatoriamente durante el primer arranque. Obligaría al usuario a iniciar InfluxDB, obtener los IDs por CLI, generar el token y copiarlo a `.env` a mano, incumpliendo el requisito de despliegue en un solo comando. |
| **Configurar token en la UI de Node-RED** | Arrancar Node-RED y que el usuario pegue el token en el nodo InfluxDB mediante la web. | Proceso manual propenso a errores humanos que rompe la reproducibilidad e infraestructura como código (IaC). |
| **Almacenar token en un fichero versionado en Git** | Guardar los tokens generados en un archivo del repositorio. | **Vulnerabilidad crítica de seguridad**. Nunca se deben comitear credenciales en el control de versiones. |
| **Docker Secrets (Swarm)** | Uso de la directiva `secrets` nativa de Docker Swarm. | Requiere inicializar un cluster Docker Swarm (`docker swarm init`), introduciendo una sobrecarga innecesaria para un entorno de desarrollo local con Docker Compose estándar. |

---

## 5. Diseño y Funcionamiento de los Flujos de Node-RED

### 5.1. Flujo 1: Meteorología (`meteo`)
- **Frecuencia**: Cada 15 minutos (`repeat: 900`).
- **Endpoint**: API pública de Open-Meteo para las coordenadas del centro de Bilbao ($43.263^\circ\text{N}, -2.935^\circ\text{W}$):
  `https://api.open-meteo.com/v1/forecast?latitude=43.263&longitude=-2.935&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,wind_direction_10m&wind_speed_unit=kmh&timezone=Europe%2FMadrid`
- **Modelado en InfluxDB**:
  - Measurement: `clima`
  - Tags: `ubicacion="bilbao"`, `fuente="open-meteo"`
  - Fields: `temp_c`, `viento_kmh`, `viento_dir`, `lluvia_mm`, `humedad`
- **Nota técnica sobre unidades**: El histórico en disco `datos/procesados/meteorologia/meteo_bilbao_horario.csv` registra el viento en **m/s**. En cambio, el API en tiempo real se configuró en **km/h** (`wind_speed_unit=kmh`). Si en el futuro se consolida el histórico en el bucket `meteo`, debe aplicarse la conversión:
  $$\text{velocidad}_{\text{km/h}} = \text{velocidad}_{\text{m/s}} \times 3.6$$

### 5.2. Flujo 2: Tráfico en Tiempo Real (`trafico`)
- **Frecuencia**: Cada 5 minutos (`repeat: 300`).
- **Fuente**: Dataset GeoJSON oficial del Ayuntamiento de Bilbao en tiempo real:
  `https://www.bilbao.eus/aytoonline/srvDatasetTrafico?formato=geojson`
- **Estructura real del dataset**:
  - Contiene 81 tramos (`features`) monitorizados por espiras electromagnéticas.
  - Campos inspeccionados: `CodigoSeccion` (código numérico identificativo de la vía), `Intensidad` (vehículos/hora), `Ocupacion` (porcentaje 0–100%) y `Velocidad` (km/h estimada).
- **Modelado en InfluxDB**:
  - Measurement: `estado`
  - Tag: `codigo_seccion` (identificador único del tramo)
  - Fields: `intensidad` (int), `ocupacion` (int), `velocidad` (int)
- **Frecuencia elegida**: 5 minutos coincide exactamente con el intervalo de cálculo y publicación de las espiras de tráfico del Ayuntamiento, evitando consultas redundantes a la API municipal.

### 5.3. Flujo 3: Simulación Acelerada de Calidad del Aire (`aire_demo`)
- **Frecuencia**: Cada 5 segundos (`repeat: 5`).
- **Origen de datos**: Generado por el script `ingesta/preparar_datos_demo.py` a partir de `datos/procesados/calidad_aire/no2_horario_limpio.zip`.
  - Filtra estrictamente las cuatro estaciones clave del estudio:
    1. **Mazarredo**: Dentro de la ZBE.
    2. **Mª Díaz de Haro**: Dentro de la ZBE (en los datos crudos aparecía con el identificador `M_DIAZ_HARO` sin clasificar; el script de ingesta la clasifica como `dentro` sin alterar el histórico original).
    3. **Europa**: Control urbano fuera de la ZBE.
    4. **Arraiz**: Fondo regional / periurbano.
  - Produce un CSV reducido de 6.5 MB y 158.901 filas ordenadas cronológicamente (2022–2026).
- **Mecanismo de reproducción**:
  - El nodo de función carga el CSV reducido en memoria una sola vez en el arranque (`flow.set('demo_por_ts', ...)`).
  - En cada ciclo de 5 segundos, avanza un puntero temporal (`demo_idx`), extrae los registros de las cuatro estaciones correspondientes a esa hora y los emite en lote (*batch*).
  - Al alcanzar el final de la serie histórica, el puntero se reinicia automáticamente a cero, garantizando una demostración continua ininterrumpida.
- **Modelado en InfluxDB**:
  - Measurement: `contaminantes`
  - Tags: `estacion`, `zona`
  - Fields: `no2` (valor numérico medido), `fecha_original` (timestamp de la fecha real en 2022-2026).
  - Marca de tiempo: La marca temporal del punto en InfluxDB es el instante actual de escritura (`new Date()`), permitiendo que las herramientas de visualización y alertas detecten los datos como eventos en vivo.

### 5.4. Resiliencia y Tolerancia a Fallos de Red
Todos los flujos implementan defensas activas para garantizar que caídas externas no detengan Node-RED ni corrompan la base de datos:
1. **Bloques `try / catch` exhaustivos**: Cualquier error en el parseo de JSON o en la estructura de propiedades es interceptado localmente.
2. **Validación de respuestas HTTP**: Si una API externa devuelve un código de error o un cuerpo vacío, el flujo emite un aviso con `node.warn()`, actualiza el indicador visual del nodo (`node.status({fill:'red', ...})`) y retorna `null`, **impidiendo la escritura de registros nulos o campos vacíos en InfluxDB**.
3. **Nodos `catch` dedicados**: Capturan excepciones no controladas de las llamadas HTTP y de los nodos InfluxDB, redirigiendo la traza a la consola de depuración sin provocar la caída del contenedor.

---

## 6. Configuración de Red y Seguridad Perimetral en Docker

### 6.1. Vinculación Estricta a `127.0.0.1`

En `docker-compose.yml`, los puertos de cara al host se declaran explícitamente:
```yaml
ports:
  - "127.0.0.1:8086:8086"
  - "127.0.0.1:1880:1880"
  - "127.0.0.1:3000:3000"
```

**Justificación técnica**:
Si se utiliza la sintaxis común `8086:8086`, Docker en sistemas Linux manipula directamente las reglas de `iptables` creando reglas de reenvío en la cadena `PREROUTING`. Esto expone el puerto en `0.0.0.0` (todas las interfaces de red), haciendo accesible la base de datos y Node-RED a cualquier equipo conectado a la red local (Wi-Fi de la universidad, red doméstica o internet si el host posee IP pública), eludiendo el firewall del sistema operativo. Al forzar `127.0.0.1`, los servicios solo son accesibles desde el equipo local.

### 6.2. Comunicación Inter-Contenedor vía DNS Interno

Los contenedores se comunican a través de la red puente (*bridge*) creada automáticamente por Docker Compose. Node-RED y Grafana se conectan a InfluxDB mediante el nombre del servicio:
```
http://influxdb:8086
```
- **Nunca `localhost`**: Dentro del contenedor `haizelab_nodered` o `haizelab_grafana`, `localhost` o `127.0.0.1` apunta al propio contenedor, donde InfluxDB no está escuchando.
- El servidor DNS integrado de Docker resuelve automáticamente el nombre de servicio `influxdb` a la dirección IP virtual asignada al contenedor en la red bridge.

---

## 7. Preguntas Clave para Examen Técnico

Esta sección resume conceptos de arquitectura comúnmente evaluados en exámenes de administración de sistemas e infraestructura Big Data:

### P1: ¿Por qué no usar PostgreSQL estándar para registrar datos de sensores cada 5 segundos?
**Respuesta**: Las bases de datos relacionales tradicionales almacenan datos en páginas en disco organizadas por filas y mantienen árboles B (*B-Trees*) para los índices. Con tasas de ingesta elevadas, las inserciones concurrentes fragmentan los árboles B y generan altos costes de I/O en disco. Además, las políticas de borrado (retención) en bases relacionales requieren ejecutar sentencias `DELETE`, que generan sobrecarga de bloqueo y fragmentación de tablas (necesidad de `VACUUM`). Las TSDB como InfluxDB emplean motores estructurados por bloques temporales (*Time-Structured Merge Tree* - TSM): escriben secuencialmente en ficheros inmutables y descartan bloques temporales completos instantáneamente al expirar su retención, sin coste de fragmentación.

### P2: ¿Qué sucede si se almacena el campo `velocidad` o `temp_c` como un Tag en lugar de un Field en InfluxDB?
**Respuesta**: Se produce una **explosión de cardinalidad**. Los tags se almacenan en el índice invertido (TSI) en memoria RAM para permitir filtrados rápidos. Como la velocidad y la temperatura son valores continuos con miles de variaciones posibles, el índice TSI generaría millones de series temporales distintas, agotando rápidamente la memoria RAM del servidor y degradando drásticamente el rendimiento de las consultas.

### P3: ¿Por qué es una mala práctica inyectar el token de administrador en el contenedor de Node-RED o Grafana?
**Respuesta**: Viola el principio de mínimo privilegio. Si Node-RED tuviese el token de administrador y sufriese una vulnerabilidad de ejecución remota de código (RCE) o un flujo mal configurado, el atacante o el script defectuoso podría borrar buckets críticos (como el histórico `aire`), alterar configuraciones de la organización o crear nuevos usuarios. Con un token restringido a escritura en buckets específicos (para Node-RED) o un token de solo lectura `read-all` (para Grafana), el radio de impacto de cualquier incidente queda estrictamente acotado y se impide cualquier mutación accidental o maliciosa de los datos.

### P4: ¿Por qué separar `docker compose down` de `docker compose down -v`?
**Respuesta**: El comando `docker compose down` detiene y elimina los contenedores y la red virtual, pero **mantiene intactos los volúmenes de datos con nombre**. Esto permite reiniciar o actualizar imágenes sin perder el histórico acumulado en InfluxDB. El modificador `-v` (*volumes*) elimina explícitamente los volúmenes, destruyendo toda la base de datos persistida; solo debe emplearse cuando se desee reconstruir el entorno íntegramente desde cero.

### P5: ¿Cómo se logra la reproducibilidad de cuadros de mando e integración de datos sin configuración manual en Grafana?
**Respuesta**: Mediante el mecanismo de **provisioning declarativo** (`/etc/grafana/provisioning/`). En lugar de requerir que el usuario configure manualmente el origen de datos y dibuje los paneles desde el navegador, se definen manifiestos YAML para el datasource (apuntando a `http://influxdb:8086` con token `read-all`) y ficheros JSON para los cuadros de mando (*Dashboards as Code*). Al arrancar el contenedor, Grafana compila automáticamente la infraestructura visual sin intervención humana, garantizando que el entorno sea 100% reproducible en cualquier máquina.
