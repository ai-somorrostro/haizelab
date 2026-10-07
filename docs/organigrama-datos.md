# Organigrama de Datos — HaizeLab InfluxDB 2

> Esquema completo: **Organización → Buckets → Measurements → Fields + Tags**  
> Organización: `haizenlab`

---

## Diagrama general

```
haizenlab (org)
│
├── aire              ← Histórico NO₂ oficial (retencion: infinita)
│   └── contaminantes
│       ├── tags:   estacion, zona
│       └── fields: no2 (float, µg/m³)
│
├── aire_demo         ← Reproducción acelerada histórico NO₂ (retencion: 7 días)
│   └── contaminantes
│       ├── tags:   estacion, zona
│       └── fields: no2 (float), fecha_original (string)
│
├── meteo             ← Meteorología en tiempo real + histórico (retencion: infinita)
│   └── clima
│       ├── tags:   ubicacion, fuente
│       └── fields: temp_c (float, °C)
│                   viento_kmh (float, km/h)
│                   viento_dir (float, grados)
│                   lluvia_mm (float, mm)
│                   humedad (float, %)
│
└── trafico           ← Tráfico urbano Bilbao Open Data (retencion: 30 días)
    └── estado
        ├── tags:   codigo_seccion
        └── fields: intensidad (int, veh/h)
                    ocupacion  (int, %)
                    velocidad  (int, km/h)
```

---

## Detalle por bucket

### `aire` — Histórico calidad del aire

| Elemento       | Valor                                  |
|----------------|----------------------------------------|
| Retención      | Infinita (datos históricos ZBE)        |
| Fuente         | `ingesta/carga_historica.py` (batch)   |
| Token acceso   | `batch-write` (escritura solo `aire`)  |
| Measurement    | `contaminantes`                        |

| Campo / Tag     | Tipo    | Descripción                              |
|-----------------|---------|------------------------------------------|
| `estacion` (tag)| string  | Nombre de la estación (Mazarredo, Europa…) |
| `zona` (tag)    | string  | `dentro` / `fuera` / `fondo`             |
| `no2`           | float   | Concentración NO₂ en µg/m³               |

**Ejemplo Flux:**
```flux
from(bucket: "aire")
  |> range(start: -30d)
  |> filter(fn: (r) => r["_measurement"] == "contaminantes")
  |> filter(fn: (r) => r["_field"] == "no2")
  |> filter(fn: (r) => r["zona"] == "dentro")
  |> mean()
```

---

### `aire_demo` — Demo acelerada NO₂

| Elemento       | Valor                                        |
|----------------|----------------------------------------------|
| Retención      | 7 días                                       |
| Fuente         | Node-RED `tab_demo` (CSV → InfluxDB, cada 5 s) |
| Token acceso   | `nodered-write` (escritura `aire_demo`)      |
| Measurement    | `contaminantes`                              |

| Campo / Tag          | Tipo    | Descripción                          |
|----------------------|---------|--------------------------------------|
| `estacion` (tag)     | string  | Nombre ASCII de la estación          |
| `zona` (tag)         | string  | `dentro` / `fuera` / `fondo`         |
| `no2`                | float   | Concentración NO₂ en µg/m³           |
| `fecha_original`     | string  | Timestamp del dato histórico (ISO)   |

**Umbrales de alerta configurados:**
- > 25 µg/m³ → ⚠️ Aviso (OMS)
- > 40 µg/m³ → 🔴 Superación límite EU
- > 200 µg/m³ → 🚨 Pico horario crítico

---

### `meteo` — Meteorología

| Elemento       | Valor                                          |
|----------------|------------------------------------------------|
| Retención      | Infinita (preserva histórico 2022-2026 y lecturas RT) |
| Fuente RT      | Node-RED `tab_meteo` (Open-Meteo, cada 15 min) |
| Fuente hist.   | `ingesta/carga_historica.py --bucket meteo`    |
| Token acceso   | `nodered-write` (RT) / `batch-write` (histórico)|
| Measurement    | `clima`                                        |

| Campo / Tag         | Tipo   | Descripción                                          |
|---------------------|--------|------------------------------------------------------|
| `ubicacion` (tag)   | string | Siempre `bilbao`                                     |
| `fuente` (tag)      | string | `open-meteo` (RT) o `historico-open-meteo` (batch)  |
| `temp_c`            | float  | Temperatura en °C                                    |
| `viento_kmh`        | float  | Velocidad del viento en km/h                         |
| `viento_dir`        | float  | Dirección del viento en grados (0-360)               |
| `lluvia_mm`         | float  | Precipitación en mm                                  |
| `humedad`           | float  | Humedad relativa en %                                |

> **Nota**: el CSV histórico tiene `viento_ms` (m/s). El script lo convierte × 3.6 al escribir en InfluxDB para mantener coherencia con los datos de Node-RED.

---

### `trafico` — Tráfico urbano

| Elemento       | Valor                                              |
|----------------|----------------------------------------------------|
| Retención      | 30 días (2.592.000 s)                              |
| Fuente         | Node-RED `tab_trafico` (Bilbao Open Data, cada 5 min) |
| Token acceso   | `nodered-write` (escritura `trafico`)              |
| Measurement    | `estado`                                           |

| Campo / Tag              | Tipo | Descripción                                      |
|--------------------------|------|--------------------------------------------------|
| `codigo_seccion` (tag)   | int  | ID del tramo de Bilbao (1–81 aprox.)             |
| `intensidad`             | int  | Vehículos por hora                               |
| `ocupacion`              | int  | % de ocupación del tramo                         |
| `velocidad`              | int  | Velocidad media en km/h                          |

**Umbral de alerta:** ocupación media > 35% durante 10 min → ⚠️ Congestión alta

---

## Tokens de acceso — Resumen

| Token             | Alcance escritura               | Alcance lectura | Usado por                    |
|-------------------|---------------------------------|-----------------|------------------------------|
| `admin`           | Todos (creación inicial)        | Todos           | Solo setup, nunca en runtime |
| `nodered-write`   | `meteo`, `trafico`, `aire_demo` | —               | Node-RED (runtime)           |
| `batch-write`     | `aire`, `meteo`                 | —               | `carga_historica.py`         |
| `read-all`        | —                               | Los 4 buckets   | Grafana, MCP futuro          |

> Un único token para todo puntúa como **deficiente** en la evaluación del reto.

---

## Control de acceso Grafana

| Grupo              | Nº usuarios | Rol Grafana | Dashboards visibles | Home dashboard     |
|--------------------|-------------|-------------|---------------------|--------------------|
| Cúpula directiva   | ~1          | Viewer      | Todos               | HaizeLab Overview  |
| Equipo Análisis    | 6           | Viewer      | Asignados           | HaizeLab Overview  |
| Equipo IT          | 3           | Admin/Editor| Todos               | HaizeLab Overview  |

---

## Estadísticas Flux disponibles en el dashboard

| Panel                                | Función Flux                              |
|--------------------------------------|-------------------------------------------|
| Media simple (5 min)                 | `aggregateWindow(fn: mean)`               |
| Media móvil 1 h                      | `timedMovingAverage(period: 1h)`          |
| Media móvil 3 h                      | `timedMovingAverage(period: 3h)`          |
| Percentil 90                         | `quantile(q: 0.9)`                        |
| Máximo de sesión                     | `max()`                                   |
| Top 5 tramos congestión              | `sort(desc: true) |> limit(n: 5)`        |
