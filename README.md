# HaizeLab — Análisis del impacto de la ZBE de Bilbao en la calidad del aire

Análisis exploratorio del efecto de la **Zona de Bajas Emisiones (ZBE) de Bilbao** sobre los niveles de NO₂, usando datos horarios de la red de calidad del aire del Gobierno Vasco (Open Data Euskadi).

## Estructura del proyecto

```
haizelab/
├── analisis.py        # Pipeline principal: lee CSVs, limpia, clasifica y exporta
├── visualizar.py      # Genera gráfico mensual NO₂ por zona (2022–2026)
├── requirements.txt   # Dependencias Python
├── datos/             # CSVs de Open Data Euskadi (NO incluidos en el repo)
│   ├── 2022/
│   │   ├── datos_diarios/
│   │   └── datos_horarios/
│   ├── 2023/ … 2026/
├── salida/            # Resultados generados (solo los ligeros están en el repo)
│   ├── comparacion.csv
│   ├── inventario.csv
│   └── no2_mensual.png
```

## Cómo reproducir el análisis

### 1. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2. Descargar los datos
Los datos brutos pesan ~200 MB y no están en el repositorio.
Descárgalos de **Open Data Euskadi → Calidad del Aire**:
- URL: https://opendata.euskadi.eus/catalogo/-/calidad-del-aire-en-la-capv/
- Descarga los ZIPs anuales de datos horarios CSV (un ZIP por año)
- Extrae cada ZIP en `datos/YYYY/` (ej: `datos/2022/datos_horarios/*.csv`)

### 3. Ejecutar
```bash
python analisis.py     # genera salida/
python visualizar.py   # genera salida/no2_mensual_2022_2026.png
```

## Resultados preliminares (sin corrección meteorológica)

| Zona | Previo (2022–jun 2024) | Fase 1 (jun 2024–jun 2025) | Fase 2 (jun 2025–oct 2026) |
|---|---|---|---|
| **Dentro ZBE** (Mazarredo + Mª Díaz de Haro) | 25.6 µg/m³ | 23.1 µg/m³ | 21.2 µg/m³ |
| **Fuera** (18 estaciones área metropolitana) | 15.9 µg/m³ | 14.2 µg/m³ | 13.4 µg/m³ |
| **Fondo regional** (rural/marino) | 8.3 µg/m³ | 7.7 µg/m³ | 7.3 µg/m³ |

**Diferencia dentro−fuera**: +9.8 µg/m³ antes → +8.2 µg/m³ después = **−1.6 µg/m³**
(IC 95% ≈ ±1.19 — señal positiva, pendiente de corrección meteorológica)

## Estaciones clasificadas

| Zona | Estaciones |
|---|---|
| `dentro` | Mazarredo, Mª Díaz de Haro |
| `fuera` | Europa, Erandio, Barakaldo, Basauri, Sestao, Muskiz, Zierbena, Santurce, Abanto, Castrejana, Zalla, Lemona, Larrabetzu, Ategorrieta, Easo, Anorga, Hernani, Lasarte-Oria, Andoain, Durango, Llodio |
| `fondo` | Arraiz, Montorra, Pagoeta, Urkiola, Valderejo, Elciego, Mundaka, Serantes, Sangroniz |

## Limitaciones

- Sin corrección meteorológica (temperatura, viento, lluvia)
- Sin datos de tráfico para verificar reducción de vehículos
- Solo 2 estaciones dentro de la ZBE
- El IC95% ignora autocorrelación temporal

## Próximos pasos

- [ ] Corrección meteorológica (deweathering) con `BOROA.csv` y `BANDERAS_meteo.csv`
- [ ] Datos de aforo de tráfico (Open Data Bilbao / Diputación Bizkaia)
- [ ] Modelo diferencias-en-diferencias con tendencia temporal

## Fuente de datos

Gobierno Vasco — Red de Control de Calidad del Aire de la CAPV  
https://www.euskadi.eus/calidad-del-aire/  
Licencia: Open Data (CC BY 4.0)
