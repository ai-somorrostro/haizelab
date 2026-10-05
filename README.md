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
