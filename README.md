# HaizeLab — Análisis Multivariable del Impacto de la ZBE de Bilbao

Estudio integral del impacto de la **Zona de Bajas Emisiones (ZBE) de Bilbao** (aprobada y puesta en vigor el 15 de junio de 2024) combinando tres fuentes de datos:
1. **Calidad del Aire (NO₂)**: Red de estaciones horarias de Open Data Euskadi (2022–2026).
2. **Aforos Oficiales de Tráfico**: Memorias oficiales de tráfico e intensidades medias diarias (IMD) de la Diputación Foral de Bizkaia (2018–2025).
3. **Meteorología y Deweathering**: Estación de Monte Banderas (Bilbao) con velocidad y dirección del viento, temperatura y humedad horaria.

---

## 📊 Principales Hallazgos

### 1. Calidad del Aire (NO₂)
| Zona | Previo (2022–jun 2024) | Fase 1 (jun 2024–jun 2025) | Fase 2 (jun 2025–oct 2026) |
|---|---|---|---|
| **Dentro ZBE** (Mazarredo + Mª Díaz de Haro) | **25.62 µg/m³** | **23.14 µg/m³** | **21.23 µg/m³** |
| **Control fuera ZBE** (18 estaciones Gran Bilbao) | 15.92 µg/m³ | 14.22 µg/m³ | 13.37 µg/m³ |
| **Fondo regional** (Arraiz, Mundaka, Pagoeta...) | 8.25 µg/m³ | 7.72 µg/m³ | 7.29 µg/m³ |

* **Reducción neta Dentro-Fuera**: -1.59 µg/m³ adicionales de caída en el centro respecto a la tendencia metropolitana.

### 2. Aforos de Tráfico (Intensidad Media Diaria en Bilbao)
Tras la entrada en vigor de la ZBE en junio de 2024:
* **Acceso San Mamés** (acceso directo al interior de la ZBE / Ensanche):
  * 2022: 51.386 veh./día
  * 2023: 50.127 veh./día
  * **2024: 45.052 veh./día (-10.12% de desplome en el año de implantación de la ZBE)**.
* **Subtotal Sur** (accesos hacia el centro de la ciudad): **-3.03%** en 2024.
* **Total accesos Bilbao**: **-0.68%** en 2024 (el tráfico periférico aumentó ligeramente hacia las circunvalaciones del norte).

### 3. Control Meteorológico (Monte Banderas)
Para descartar que la caída de NO₂ fuera debida al clima (viento/lluvia), se estratificó por régimen de viento:
* **En condiciones de calma atmosférica (< 2 m/s)**, donde no hay dispersión y la contaminación refleja puramente emisiones locales:
  * Pre-ZBE: **32.32 µg/m³**
  * Post-ZBE: **26.78 µg/m³** (**-17.14% de reducción neta en calma**).
* **En viento moderado (2–5 m/s)**: bajó de 26.55 a 22.62 µg/m³ (**-14.80%**).
* **En viento fuerte (> 5 m/s)**: bajó de 18.63 a 16.21 µg/m³ (**-13.00%**).

---

## 🗂️ Estructura del Proyecto

```
haizelab/
├── analisis.py                 # Pipeline principal: integra NO2, meteo y aforos de tráfico
├── extraer_trafico.py          # Extractor automatizado de tablas de tráfico de los PDFs oficiales
├── visualizar.py               # Genera gráficos temporales y el dashboard de 4 paneles
├── requirements.txt            # Dependencias Python
├── Dockerfile                  # Contenedor reproducible
├── docker-compose.yml          # Orquestación Docker
├── datos/                      # Ficheros de Open Data Euskadi (excluidos por .gitignore)
│   ├── 2022/ … 2026/
└── salida/                     # Resultados generados
    ├── comparacion.csv         # Medias de NO2 por periodo y zona
    ├── inventario.csv          # Cobertura y nulos de cada estación
    ├── meteo_resumen.csv       # Promedios meteorológicos por periodo
    ├── no2_regimen_viento.csv  # NO2 estratificado por viento
    ├── trafico_accesos_bilbao.csv # IMD 2018-2025 por vía de acceso a Bilbao
    ├── trafico_circunvalacion.csv # IMD de las rondas metropolitanas
    ├── no2_mensual.png         # Serie temporal mensual de NO2
    └── informe_multivariable_zbe.png # Dashboard multivariable de 4 paneles
```

---

## 🚀 Cómo reproducir el análisis

### 1. Entorno local

```bash
pip install -r requirements.txt

# 1. Extraer los datos de tráfico de los PDFs de Bizkaia
python extraer_trafico.py

# 2. Ejecutar el análisis integrado (NO2 + Meteo + Tráfico)
python analisis.py

# 3. Generar las visualizaciones y el dashboard completo
python visualizar.py
```

### 2. Con Docker

```bash
docker compose run --rm todo
```

---

## 📚 Fuentes de Datos

* **Calidad del Aire y Meteorología**: Red de Control y Vigilancia de la Calidad del Aire del País Vasco — *Open Data Euskadi* (licencia CC BY 4.0).
* **Tráfico y Aforos**: Informes anuales *"Evolución del tráfico en las carreteras de Bizkaia"* (2018 a 2025) — *Diputación Foral de Bizkaia (Departamento de Infraestructuras y Desarrollo Territorial)*.
* **Perímetro ZBE**: Ayuntamiento de Bilbao (*Ordenanza Reguladora de la Zona de Bajas Emisiones de Bilbao*, BOB núm. 104, 30/05/2024).
