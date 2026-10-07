# Infraestructura en Tiempo Real: InfluxDB 2, Node-RED y Grafana en HaizeLab

He preparado este documento para explicar paso a paso cómo he montado y conectado toda la infraestructura de datos en tiempo real para el proyecto **HaizeLab**. 

La idea principal era sencilla: queríamos complementar los scripts de análisis histórico que ya teníamos en Python con un sistema que simulara y capturara datos en tiempo real (calidad del aire, el tiempo que hace en Bilbao y el estado del tráfico), todo metido en contenedores Docker para que cualquiera del equipo pueda levantarlo con un único comando sin volverse loco instalando cosas.

---

## 1. ¿Qué he montado exactamente?

He configurado cuatro servicios en Docker Compose que trabajan juntos:

1. **InfluxDB 2 (puerto 8086)**: La base de datos donde guardamos todas las mediciones temporales.
2. **Setup automático de InfluxDB (`influxdb_setup`)**: Un contenedor pequeñito que solo arranca una vez, crea los buckets necesarios y genera las contraseñas/tokens de acceso para que nadie tenga que entrar a la web a configurar nada a mano.
3. **Node-RED (puerto 1880)**: El "cerebro" que va a buscar los datos a internet (APIs de Open-Meteo y del Ayuntamiento de Bilbao) y que también reproduce los datos históricos de NO₂ como si estuvieran ocurriendo ahora mismo.
4. **Grafana (puerto 3000)**: La pantalla visual donde he dejado montado un cuadro de mando con gráficas y semáforos para ver cómo afecta el tráfico y el clima a la contaminación dentro y fuera de la ZBE de Bilbao.

### El esquema de cómo se conectan:
```
  [ Navegador en mi PC: http://localhost ]
       │                │               │
       │ :8086          │ :1880         │ :3000
       ▼                ▼               ▼
 ┌───────────┐    ┌───────────┐   ┌───────────┐
 │ InfluxDB  │◀───│ Node-RED  │   │  Grafana  │
 │ (BD TSDB) │    │ (Flujos)  │   │ (Paneles) │
 └───────────┘    └───────────┘   └───────────┘
       ▲                                │
       │       Lee con token read-all   │
       └────────────────────────────────┘
```

Todo se ejecuta en una red interna privada de Docker (`haizelab_default`) y solo abro al exterior (`127.0.0.1`) los puertos necesarios en local para no dejar la base de datos abierta a toda la red del instituto o de casa.

---

## 2. InfluxDB 2: ¿Por qué no usar MySQL o PostgreSQL normal?

Cuando empezamos a plantear esto, la primera duda era: ¿por qué no meter todo en una tabla de MySQL o Postgres que ya conocemos de ASIR?

La razón es práctica:
- En este proyecto estamos metiendo datos de 4 estaciones cada 5 segundos para la demo, más decenas de tramos de tráfico cada 5 minutos.
- Una base de datos relacional tradicional guarda filas y tiene que actualizar índices B-Tree en cada inserción. Con tantas escrituras seguidas se acaba saturando el disco y bloqueando tablas.
- Además, si queremos borrar datos viejos (por ejemplo, guardar solo 30 días de tráfico), en SQL hay que hacer `DELETE FROM ...` que fragmenta el disco. En InfluxDB le dices la retención al crear el bucket (ej. 30 días) y el motor va tirando bloques viejos enteros de golpe sin despeinarse.

### Cómo he organizado los datos (Buckets):

He creado 4 buckets separados para no mezclar churras con merinas:

1. **`aire`**: Aquí guardaremos los datos históricos oficiales consolidados de la ZBE (retención infinita).
2. **`meteo`**: Datos meteorológicos de Bilbao (temperatura, lluvia, viento, humedad). Retención de 90 días.
3. **`trafico`**: Estado de los 81 tramos de tráfico de Bilbao (intensidad de coches, ocupación y velocidad media). Retención de 30 días.
4. **`aire_demo`**: El banco de pruebas para la demo en clase. Lee datos históricos reales y los emite cada 5 segundos para ver cómo se mueven las gráficas en directo. Retención de 7 días.

---

## 3. Seguridad y Tokens: No meter contraseñas en Git

Uno de los mayores fallos cuando se empieza con Docker es meter tokens de administrador en los ficheros que luego subes a GitHub. Para evitar eso y seguir buenas prácticas de seguridad:

1. **Token de Administrador**: Solo se usa durante la instalación inicial en local.
2. **Token de Node-RED (`nodered-write`)**: Solo tiene permiso para **escribir** en `meteo`, `trafico` y `aire_demo`. Si alguien consiguiera hackear el Node-RED, **no podría borrar ni modificar** el histórico oficial de `aire` porque InfluxDB le rechaza con un error 403 Forbidden.
3. **Token de Grafana (`read-all`)**: Solo tiene permiso para **leer**. Aunque toques algo en Grafana, es imposible que borre o altere ninguna medición.

### ¿Cómo se pasan estos tokens entre contenedores sin subirlos a Git?
He usado un volumen compartido (`influxdb_tokens`):
- El contenedor `influxdb_setup` genera los tokens aleatorios dentro de InfluxDB.
- Guarda un fichero `tokens.env` en ese volumen compartido (que solo existe dentro de Docker en mi máquina).
- Al arrancar Node-RED y Grafana, sus scripts de inicio leen ese archivo y se configuran solos. Cero contraseñas en Git.

---

## 4. Los flujos de Node-RED (paso a paso)

En Node-RED he organizado el trabajo en tres pestañas limpias y alineadas para que cualquiera que abra la interfaz entienda qué hace cada nodo:

### 1. Pestaña `meteo` (cada 15 minutos)
- Un nodo **Inject** dispara la consulta cada 15 min.
- Hace un `GET` a la API gratuita de Open-Meteo con las coordenadas de Bilbao (43.263, -2.935).
- Una función en JavaScript extrae la temperatura, velocidad del viento, dirección, humedad y lluvia.
- Lo escribe en InfluxDB en el measurement `clima`.
- Si internet se cae o la API falla, un nodo **Catch** captura el error, avisa por consola y no tira el flujo abajo.

### 2. Pestaña `trafico` (cada 5 minutos)
- Consulta el servicio GeoJSON oficial del Ayuntamiento de Bilbao (`srvDatasetTrafico`).
- Nos devuelve los datos de los 81 tramos de la ciudad en tiempo real.
- Filtramos y guardamos:
  - `intensidad`: coches por hora.
  - `ocupacion`: porcentaje de calle ocupada (0-100%).
  - `velocidad`: velocidad media en km/h.
- Se guarda en el bucket `trafico` con el tag del tramo (`codigo_seccion`).

### 3. Pestaña `aire_demo` (cada 5 segundos)
- Para no depender de si las estaciones de aire emiten justo cuando estamos en clase, preparé un dataset representativo (`ingesta/no2_demo_reducido.csv`) con datos reales de 2022 a 2026 de 4 estaciones clave:
  - **Mazarredo**: Dentro de la ZBE.
  - **Mª Díaz de Haro**: Dentro de la ZBE (corrigiendo el nombre que venía en sucio como `M_DIAZ_HARO`).
  - **Europa**: Fuera de la ZBE (control urbano).
  - **Arraiz**: Fondo natural.
- El flujo carga ese CSV en memoria al arrancar el contenedor.
- Cada 5 segundos, coge los datos de una hora real y los escribe en InfluxDB con la fecha y hora de este momento, de modo que parece que las estaciones están emitiendo en riguroso directo. Cuando llega al final del dataset, vuelve a empezar en bucle.

---

## 5. Grafana: Visualización sencilla sin tocar nada a mano

Para ver los datos no quería tener que crear paneles a mano cada vez que se reiniciara el contenedor. Así que he usado la función de **provisioning** de Grafana:

- He configurado un archivo YAML para que Grafana añada InfluxDB como origen de datos automáticamente al arrancar.
- El cuadro de mando (`grafana/dashboards/haizelab-overview.json`) define de forma declarativa todos los paneles:
  - **Calidad del aire**: Unos relojes con colores tipo semáforo (verde < 25, amarillo 25-40, rojo > 40 µg/m³ según las normas europeas) y la gráfica temporal comparando dentro vs fuera de la ZBE.
  - **Clima**: Gráfica de temperatura y humedad, y otra de viento y lluvia.
  - **Tráfico**: Cuántos coches se mueven por Bilbao y a qué velocidad media van.
- He dejado el acceso directo activado en `localhost:3000`: entras con el navegador y ya tienes el panel en pantalla sin tener que loguearte.

---

## 6. Problemas reales con los que me he pegado y cómo los he resuelto

No todo fue coser y cantar a la primera; estos fueron los problemas principales que salieron durante las pruebas y cómo los solucioné:

1. **Docker Compose daba error al construir (`already exists`)**:
   - Varios servicios batch antiguos (`extraer`, `analisis`, `visualizar`) compartían la misma etiqueta `image: haizelab:latest`. Al hacer `build` en paralelo, Docker BuildKit se quejaba de colisión.
   - *Solución*: Les puse el perfil `profiles: ["pipeline"]` en `docker-compose.yml` para que al hacer `docker compose up -d` solo levante los servicios de la infraestructura en tiempo real, sin pisar los scripts de análisis.
2. **Node-RED aparecía con los nodos amontonados en la esquina**:
   - Al generar los flujos por código, se me olvidó poner las propiedades `x` e `y`. Node-RED por defecto los apilaba todos en la posición (0, 0).
   - *Solución*: Añadí coordenadas automáticas con separación limpia de 220 píxeles horizontales y la fila de errores debajo.
3. **El triángulo rojo en el nodo de InfluxDB en Node-RED**:
   - Node-RED mostraba una advertencia de validación en el nodo de salida porque la librería esperaba obligatoriamente los campos `protocol: http` y un nombre de base de datos por defecto. Se los configuré en el JSON y la advertencia desapareció.
4. **Error en InfluxDB `unsupported input type for mean aggregate: string`**:
   - Al mirar en el Data Explorer de InfluxDB, salía este fallo. La razón es que InfluxDB intenta calcular la media (`mean()`) de los campos seleccionados, y habíamos marcado el campo `fecha_original` (que es texto, ej. "2022-01-01"). Al desmarcar ese y marcar `no2` (que sí es un número flotante), la gráfica funcionó perfecta.
5. **Permisos y shells en Linux/Windows**:
   - En Windows los ficheros a veces se guardaban con saltos de línea CRLF, lo que rompía los scripts bash dentro de Alpine (`/bin/sh^M: not found`). Lo dejé blindado con `.gitattributes` para que siempre se guarden en formato LF de Linux.

---

## 7. Preguntas típicas que nos pueden hacer en clase o en un examen

### P1: ¿Por qué no usar PostgreSQL para registrar datos cada pocos segundos?
Porque las bases de datos relacionales tradicionales sufren mucho con escrituras masivas continuas: tienen que reordenar árboles de índices (B-Trees) en disco y borrar datos viejos requiere sentencias `DELETE` pesadas que fragmentan las tablas. Las TSDB como InfluxDB escriben en ficheros secuenciales ordenados por tiempo (TSM) y descartan bloques enteros cuando expira la retención, sin coste de rendimiento.

### P2: ¿Por qué en InfluxDB la velocidad o la temperatura van en Fields y no en Tags?
Porque si pones una variable continua (como temperatura o velocidad, que tienen miles de decimales o valores distintos) como Tag, provocas una **explosión de cardinalidad**. Los Tags se indexan en memoria RAM; si creas millones de combinaciones de tags, te quedas sin memoria en el servidor en un par de horas.

### P3: ¿Por qué darle a Node-RED un token con permisos justos y no el de administrador?
Por el principio de mínimo privilegio. Si alguien consiguiera explotar una vulnerabilidad en Node-RED o en alguna librería npm que hayamos instalado, solo podría escribir en los buckets de prueba y meteo. No podría borrar la base de datos histórica `aire` ni robarnos el control del servidor InfluxDB.

### P4: ¿Cuál es la diferencia entre `docker compose down` y `docker compose down -v`?
El primero apaga y borra los contenedores, pero **mantiene guardados los datos** en los volúmenes de Docker (no pierdes las mediciones). Si le añades el `-v`, borras también los volúmenes y la base de datos se borra por completo, obligando a reconstruir todo desde cero.
