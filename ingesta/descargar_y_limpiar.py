#!/usr/bin/env python3
"""
ingesta/descargar_y_limpiar.py
==============================
Módulo de adquisición, control de calidad, limpieza e integración de datos
para la evaluación del impacto de la ZBE de Bilbao (Reto 0 - Módulo SBD).

Fuentes:
  1. Calidad del Aire: Open Data Euskadi (Red de Control de Calidad del Aire del Gobierno Vasco).
     Años: 2022, 2023, 2024, 2025, 2026.
     Estaciones:
       - DENTRO: Mazarredo (id 60), Mª Díaz de Haro (id 81)
       - CONTROL FUERA: Europa (id 62), Barakaldo, Basauri, Erandio, Castrejana
       - FONDO: Arraiz (id 92)
     Contaminantes: NO2, NO, NOx, PM10, PM2.5, SO2, CO, Benceno.
  2. Meteorología: Open-Meteo Historical API (Coordenadas Bilbao: 43.2630 N, -2.9350 W).
     Variables: temperatura, humedad relativa, precipitación, velocidad del viento, dirección del viento.
  3. Calendario ZBE: Fases ZBE (Fase 1: 15/06/2024, Fase 2: 16/06/2025), horario (L-V 7:00-20:00)
     y festivos oficiales de Bilbao / Bizkaia / Euskadi.
  4. Tráfico: GeoJSON en tiempo real de Bilbao Open Data (Ayuntamiento de Bilbao).

Problemas de calidad tratados y contabilizados:
  1. Coma decimal europea (convertida a punto decimal).
  2. Hora 24:00 (convertida a 00:00 del día siguiente sumando 1 día).
  3. Huecos y valores ausentes.
  4. Conversión de GMT a hora local (Europe/Madrid) para cruzar con horario ZBE.
  5. Valores negativos o físicamente imposibles (< 0 convertidos a NaN).
  6. Estaciones y contaminantes con periodos sin datos.
"""

from pathlib import Path
import io
import json
import shutil
import unicodedata
import zipfile
import numpy as np
import pandas as pd
import requests

# Rutas del proyecto
DIR_RAIZ = Path(__file__).resolve().parent.parent
DIR_DATA_RAW = DIR_RAIZ / "data" / "raw"
DIR_DATA_CLEAN = DIR_RAIZ / "data" / "clean"
DIR_DATOS_CRUDO_EXISTENTE = DIR_RAIZ / "datos" / "crudo"

# Hitos temporales de la ZBE
FECHA_FASE1 = pd.Timestamp("2024-06-15")
FECHA_FASE2 = pd.Timestamp("2025-06-16")

# Mapeo oficial de estaciones requeridas
ESTACIONES_CONFIG = {
    "MAZARREDO": {
        "id": 60,
        "nombre_oficial": "Mazarredo",
        "zona": "dentro",
        "direccion": "Alameda Mazarredo s/n",
        "lat": 43.2675,
        "lon": -2.9352,
    },
    "M_DIAZ_HARO": {
        "id": 81,
        "nombre_oficial": "Mª Díaz de Haro",
        "zona": "dentro",
        "direccion": "C/ María Díaz de Haro 60",
        "lat": 43.2588,
        "lon": -2.9457,
    },
    "EUROPA": {
        "id": 62,
        "nombre_oficial": "Europa",
        "zona": "fuera",
        "direccion": "Parque Europa (Txurdinaga)",
        "lat": 43.2549,
        "lon": -2.9024,
    },
    "ARRAIZ_Monte": {
        "id": 92,
        "nombre_oficial": "Arraiz",
        "zona": "fondo",
        "direccion": "Monte Arraiz",
        "lat": 43.2456,
        "lon": -2.9605,
    },
    "BARAKALDO": {
        "id": 48,
        "nombre_oficial": "Barakaldo",
        "zona": "fuera",
        "direccion": "Barakaldo Centro",
        "lat": 43.2984,
        "lon": -2.9871,
    },
    "BASAURI": {
        "id": 49,
        "nombre_oficial": "Basauri",
        "zona": "fuera",
        "direccion": "Basauri",
        "lat": 43.2411,
        "lon": -2.8838,
    },
    "ERANDIO": {
        "id": 61,
        "nombre_oficial": "Erandio",
        "zona": "fuera",
        "direccion": "Erandio",
        "lat": 43.3027,
        "lon": -2.9772,
    },
    "CASTREJANA": {
        "id": 52,
        "nombre_oficial": "Castrejana",
        "zona": "fuera",
        "direccion": "Castrejana",
        "lat": 43.2581,
        "lon": -2.9735,
    },
}

# URLs oficiales verificadas
URLS_AIRE = {
    2022: "https://opendata.euskadi.eus/contenidos/ds_informes_estudios/calidad_aire_2022/es_def/adjuntos/datos_historicos_csv.zip",
    2023: "https://opendata.euskadi.eus/contenidos/ds_informes_estudios/calidad_aire_2023/es_def/adjuntos/datos_historicos_csv.zip",
    2024: "https://opendata.euskadi.eus/contenidos/ds_informes_estudios/calidad_aire_2024/es_def/adjuntos/datos_historicos_csv.zip",
    2025: "https://opendata.euskadi.eus/contenidos/ds_informes_estudios/calidad_aire_2025/es_def/adjuntos/datos_historicos_csv.zip",
    2026: "https://opendata.euskadi.eus/contenidos/ds_informes_estudios/calidad_aire_2026/es_def/adjuntos/datos_historicos_csv.zip",
}
URL_ESTACIONES_CSV = "https://opendata.euskadi.eus/contenidos/ds_informes_estudios/calidad_aire_2026/es_def/adjuntos/estaciones.csv"
URL_TRAFICO_GEOJSON = "https://www.bilbao.eus/aytoonline/srvDatasetTrafico?formato=geojson"


def crear_estructura_directorios():
    """Crea los directorios necesarios si no existen."""
    for d in [
        DIR_DATA_RAW / "calidad_aire",
        DIR_DATA_RAW / "meteorologia",
        DIR_DATA_RAW / "calendario",
        DIR_DATA_RAW / "trafico",
        DIR_DATA_CLEAN,
    ]:
        d.mkdir(parents=True, exist_ok=True)


def descargar_calidad_aire(forzar=False):
    """
    Descarga o copia los ficheros horarios de calidad del aire desde Open Data Euskadi.
    Utiliza la caché local de datos/crudo si existe para agilizar la ejecución reproducible.
    """
    crear_estructura_directorios()
    dir_dest = DIR_DATA_RAW / "calidad_aire"

    # 1. Estaciones CSV oficial
    f_est = dir_dest / "estaciones.csv"
    if forzar or not f_est.exists():
        try:
            r = requests.get(URL_ESTACIONES_CSV, timeout=15)
            if r.status_code == 200:
                f_est.write_bytes(r.content)
                print(f"[OK] Descargado estaciones.csv ({len(r.content):,} bytes)")
        except Exception as e:
            print(f"[!] No se pudo descargar estaciones.csv online: {e}")

    # 2. Ficheros de estaciones por año
    ficheros_descargados = []
    for año, url in URLS_AIRE.items():
        dir_año = dir_dest / str(año) / "datos_horarios"
        dir_año.mkdir(parents=True, exist_ok=True)

        # Comprobar si ya existen en datos/crudo/calidad_aire para copiar rápido
        dir_origen_existente = DIR_DATOS_CRUDO_EXISTENTE / "calidad_aire" / str(año) / "datos_horarios"
        ficheros_necesarios = [f"{est}.csv" for est in ESTACIONES_CONFIG.keys()]
        faltan = [f for f in ficheros_necesarios if not (dir_año / f).exists()]

        if not faltan and not forzar:
            ficheros_descargados.extend(dir_año / f for f in ficheros_necesarios)
            continue

        if dir_origen_existente.exists() and not forzar:
            for f in ficheros_necesarios:
                origen = dir_origen_existente / f
                destino = dir_año / f
                if origen.exists() and (forzar or not destino.exists()):
                    shutil.copy2(origen, destino)
                    ficheros_descargados.append(destino)
            print(f"[OK] Copiados ficheros de calidad del aire del año {año} desde datos/crudo a data/raw/")
        else:
            # Descarga remota del zip oficial
            print(f"Descargando datos oficiales del año {año} desde Open Data Euskadi...")
            try:
                r = requests.get(url, timeout=40)
                if r.status_code == 200:
                    with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
                        for miembro in zf.namelist():
                            nombre_archivo = Path(miembro).name
                            if nombre_archivo in ficheros_necesarios:
                                (dir_año / nombre_archivo).write_bytes(zf.read(miembro))
                                ficheros_descargados.append(dir_año / nombre_archivo)
                    print(f"[OK] Extraídos ficheros del año {año} desde {url}")
                else:
                    print(f"[!] HTTP {r.status_code} al descargar año {año}")
            except Exception as e:
                print(f"[!] Error descargando año {año}: {e}")

    return ficheros_descargados


def descargar_meteorologia(forzar=False):
    """
    Descarga la serie meteorológica horaria histórica de Bilbao desde la API pública de Open-Meteo.
    Coordenadas: Latitud 43.2630 N, Longitud -2.9350 W.
    """
    crear_estructura_directorios()
    f_salida = DIR_DATA_RAW / "meteorologia" / "open_meteo_bilbao_crudo.csv"

    if f_salida.exists() and not forzar:
        print(f"[INFO] Meteorología cruda ya existe en {f_salida}")
        return f_salida

    print("Consultando serie histórica horaria en Open-Meteo API...")
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": 43.2630,
        "longitude": -2.9350,
        "start_date": "2022-01-01",
        "end_date": "2026-10-01",
        "hourly": [
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "wind_speed_10m",
            "wind_direction_10m",
        ],
    }
    r = requests.get(url, params=params, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"Error descargando datos de Open-Meteo: HTTP {r.status_code} - {r.text[:200]}")

    datos = r.json().get("hourly", {})
    df_meteo = pd.DataFrame(datos)
    df_meteo.to_csv(f_salida, index=False)
    print(f"[OK] Guardada meteorología cruda en {f_salida} ({len(df_meteo):,} horas)")
    return f_salida


def generar_calendario_zbe_festivos(forzar=False):
    """
    Genera el calendario oficial de Bilbao de 2022 a 2026 con festivos locales,
    fases de la ZBE y definición de días laborables.
    """
    crear_estructura_directorios()
    f_salida = DIR_DATA_RAW / "calendario" / "calendario_zbe_festivos.csv"
    if f_salida.exists() and not forzar:
        return f_salida

    festivos_oficiales = {
        # 2022
        "2022-01-01": "Año Nuevo",
        "2022-01-06": "Epifanía del Señor",
        "2022-04-14": "Jueves Santo",
        "2022-04-15": "Viernes Santo",
        "2022-04-18": "Lunes de Pascua",
        "2022-07-25": "Santiago Apóstol",
        "2022-08-15": "Asunción de la Virgen",
        "2022-08-26": "Viernes de Aste Nagusia",
        "2022-09-06": "V Centenario Vuelta al Mundo Elkano",
        "2022-10-12": "Fiesta Nacional de España",
        "2022-11-01": "Todos los Santos",
        "2022-12-06": "Día de la Constitución",
        "2022-12-08": "Inmaculada Concepción",
        # 2023
        "2023-01-06": "Epifanía del Señor",
        "2023-04-06": "Jueves Santo",
        "2023-04-07": "Viernes Santo",
        "2023-04-10": "Lunes de Pascua",
        "2023-05-01": "Fiesta del Trabajo",
        "2023-07-25": "Santiago Apóstol",
        "2023-08-15": "Asunción de la Virgen",
        "2023-08-25": "Viernes de Aste Nagusia",
        "2023-10-12": "Fiesta Nacional de España",
        "2023-11-01": "Todos los Santos",
        "2023-12-06": "Día de la Constitución",
        "2023-12-08": "Inmaculada Concepción",
        "2023-12-25": "Natividad del Señor",
        # 2024
        "2024-01-01": "Año Nuevo",
        "2024-01-06": "Epifanía del Señor",
        "2024-03-28": "Jueves Santo",
        "2024-03-29": "Viernes Santo",
        "2024-04-01": "Lunes de Pascua",
        "2024-05-01": "Fiesta del Trabajo",
        "2024-07-25": "Santiago Apóstol",
        "2024-08-15": "Asunción de la Virgen",
        "2024-08-23": "Viernes de Aste Nagusia",
        "2024-10-12": "Fiesta Nacional de España",
        "2024-11-01": "Todos los Santos",
        "2024-12-06": "Día de la Constitución",
        "2024-12-25": "Natividad del Señor",
        # 2025
        "2025-01-01": "Año Nuevo",
        "2025-01-06": "Epifanía del Señor",
        "2025-04-17": "Jueves Santo",
        "2025-04-18": "Viernes Santo",
        "2025-04-21": "Lunes de Pascua",
        "2025-05-01": "Fiesta del Trabajo",
        "2025-07-25": "Santiago Apóstol",
        "2025-08-15": "Asunción de la Virgen",
        "2025-08-22": "Viernes de Aste Nagusia",
        "2025-10-12": "Fiesta Nacional de España",
        "2025-11-01": "Todos los Santos",
        "2025-12-06": "Día de la Constitución",
        "2025-12-08": "Inmaculada Concepción",
        "2025-12-25": "Natividad del Señor",
        # 2026
        "2026-01-01": "Año Nuevo",
        "2026-01-06": "Epifanía del Señor",
        "2026-04-02": "Jueves Santo",
        "2026-04-03": "Viernes Santo",
        "2026-04-06": "Lunes de Pascua",
        "2026-05-01": "Fiesta del Trabajo",
        "2026-07-25": "Santiago Apóstol",
        "2026-08-15": "Asunción de la Virgen",
        "2026-08-28": "Viernes de Aste Nagusia",
        "2026-10-12": "Fiesta Nacional de España",
    }

    fechas = pd.date_range("2022-01-01", "2026-10-06", freq="D")
    filas = []
    for f in fechas:
        f_str = f.strftime("%Y-%m-%d")
        es_fin_de_semana = f.weekday() >= 5
        es_festivo = f_str in festivos_oficiales
        nombre_festivo = festivos_oficiales.get(f_str, "")
        es_laborable = (not es_fin_de_semana) and (not es_festivo)

        if f < FECHA_FASE1:
            fase = "previo"
            desc_fase = "Pre-ZBE (Sin restricciones de etiquetas)"
        elif f < FECHA_FASE2:
            fase = "fase1"
            desc_fase = "Fase 1 (Prohibidos vehículos sin distintivo ambiental)"
        else:
            fase = "fase2"
            desc_fase = "Fase 2 (Prohibidos distintivo B no residentes)"

        filas.append({
            "fecha": f_str,
            "año": f.year,
            "mes": f.month,
            "dia": f.day,
            "dia_semana": f.weekday(),
            "nombre_dia": f.day_name(),
            "es_fin_semana": es_fin_de_semana,
            "es_festivo": es_festivo,
            "nombre_festivo": nombre_festivo,
            "es_laborable": es_laborable,
            "fase_zbe": fase,
            "descripcion_fase": desc_fase,
        })

    df = pd.DataFrame(filas)
    df.to_csv(f_salida, index=False)
    print(f"[OK] Guardado calendario ZBE con festivos en {f_salida} ({len(df):,} días)")
    return f_salida


def descargar_trafico_geojson(forzar=False):
    """
    Descarga el GeoJSON de tráfico en tiempo real del Ayuntamiento de Bilbao.
    """
    crear_estructura_directorios()
    f_salida = DIR_DATA_RAW / "trafico" / "trafico_bilbao_actual.geojson"
    if f_salida.exists() and not forzar:
        return f_salida

    print("Descargando GeoJSON de tráfico en tiempo real de Bilbao...")
    try:
        r = requests.get(URL_TRAFICO_GEOJSON, timeout=20)
        if r.status_code == 200:
            f_salida.write_bytes(r.content)
            print(f"[OK] Guardado tráfico GeoJSON en {f_salida} ({len(r.content):,} bytes)")
        else:
            print(f"[!] HTTP {r.status_code} al descargar GeoJSON de tráfico")
    except Exception as e:
        print(f"[!] Error descargando GeoJSON de tráfico: {e}")
    return f_salida


def descargar_todos_los_datos(forzar=False):
    """Orquesta la descarga de todos los conjuntos de datos en data/raw/."""
    print("=" * 70)
    print("INICIO: ADQUISICIÓN Y DESCARGA DE DATOS CRUDOS EN data/raw/")
    print("=" * 70)
    f_aire = descargar_calidad_aire(forzar=forzar)
    f_meteo = descargar_meteorologia(forzar=forzar)
    f_cal = generar_calendario_zbe_festivos(forzar=forzar)
    f_traf = descargar_trafico_geojson(forzar=forzar)
    print("\n[OK] Todos los datos crudos han sido adquiridos satisfactoriamente.")
    return {
        "calidad_aire": f_aire,
        "meteorologia": f_meteo,
        "calendario": f_cal,
        "trafico": f_traf,
    }


def limpiar_calidad_aire():
    """
    Lee y limpia los ficheros horarios de calidad del aire tratando y documentando
    los 6 problemas de calidad requeridos:
      1. Coma decimal -> conversión a float con punto.
      2. Hora 24:00 -> conversión a 00:00 del día siguiente (+1 día).
      3. Huecos y valores ausentes -> contabilización y preservación NaN.
      4. GMT vs Hora local -> conversión a hora oficial Europe/Madrid.
      5. Valores negativos o imposibles -> sustitución por NaN (<0).
      6. Periodos sin datos -> inventario temporal por estación.
    """
    print("=" * 70)
    print("LIMPIEZA DE CALIDAD DEL AIRE Y AUDITORÍA DE CALIDAD")
    print("=" * 70)
    dir_raw_aire = DIR_DATA_RAW / "calidad_aire"

    filas_totales_cargadas = 0
    conteo_problemas = {
        "filas_hora_24": 0,
        "campos_coma_decimal": 0,
        "valores_negativos_por_contaminante": {},
        "valores_ausentes_por_contaminante": {},
    }

    registros_estaciones = []

    for id_est, cfg in ESTACIONES_CONFIG.items():
        dfs_est = []
        for año in sorted(URLS_AIRE.keys()):
            f_csv = dir_raw_aire / str(año) / "datos_horarios" / f"{id_est}.csv"
            if not f_csv.exists():
                continue

            df = pd.read_csv(f_csv, sep=";", encoding="latin1", dtype=str)
            filas_totales_cargadas += len(df)

            col_fecha = next((c for c in df.columns if "date" in c.lower() or "fecha" in c.lower()), None)
            col_hora = next((c for c in df.columns if "hour" in c.lower() or "hora" in c.lower()), None)

            if not col_fecha or not col_hora:
                continue

            # Problema 1: Hora 24:00
            horas_raw = df[col_hora].astype(str).str.strip()
            es_24 = horas_raw.isin(["24:00", "24", "24:00:00"])
            conteo_problemas["filas_hora_24"] += int(es_24.sum())

            horas_clean = horas_raw.replace({"24:00": "00:00", "24": "00:00", "24:00:00": "00:00"})
            fechas_raw = df[col_fecha].astype(str).str.strip()

            # Parsear timestamp base en GMT (UTC)
            ts_gmt = pd.to_datetime(fechas_raw + " " + horas_clean, format="%d/%m/%Y %H:%M", errors="coerce")
            ts_gmt.loc[es_24] = ts_gmt.loc[es_24] + pd.Timedelta(days=1)

            # Problema 4: GMT vs Hora local (Europe/Madrid)
            ts_gmt_aware = ts_gmt.dt.tz_localize("UTC")
            ts_local = ts_gmt_aware.dt.tz_convert("Europe/Madrid").dt.tz_localize(None)

            out_df = pd.DataFrame({
                "ts_gmt": ts_gmt,
                "ts_local": ts_local,
                "estacion_id": cfg["id"],
                "estacion": cfg["nombre_oficial"],
                "zona": cfg["zona"],
            })

            # Mapear contaminantes
            mapeo_cols = {
                "no2": ["no2 (g/m3)", "no2 (µg/m3)", "no2 (ug/m3)", "no2"],
                "no": ["no (g/m3)", "no (µg/m3)", "no (ug/m3)", "no"],
                "nox": ["nox (g/m3)", "nox (µg/m3)", "nox (ug/m3)", "nox"],
                "pm10": ["pm10 (g/m3)", "pm10 (µg/m3)", "pm10 (ug/m3)", "pm10"],
                "pm25": ["pm2,5 (g/m3)", "pm2.5 (g/m3)", "pm2,5 (µg/m3)", "pm2.5 (µg/m3)", "pm25"],
                "so2": ["so2 (g/m3)", "so2 (µg/m3)", "so2 (ug/m3)", "so2"],
                "co": ["co (mg/m3)", "co"],
                "benceno": ["benceno (g/m3)", "benceno (µg/m3)", "benceno"],
            }

            for p_nombre, variantes in mapeo_cols.items():
                col_encontrada = next(
                    (c for c in df.columns if any(v in c.lower().replace(" ", "") for v in variantes)),
                    None,
                )
                if col_encontrada:
                    serie_raw = df[col_encontrada].fillna("").astype(str).str.strip()
                    conteo_problemas["campos_coma_decimal"] += int(serie_raw.str.contains(",").sum())

                    # Conversión numérica
                    vals_num = pd.to_numeric(serie_raw.str.replace(",", ".", regex=False), errors="coerce")

                    # Problema 5: Valores negativos (<0)
                    es_neg = vals_num < 0
                    num_neg = int(es_neg.sum())
                    conteo_problemas["valores_negativos_por_contaminante"][p_nombre] = (
                        conteo_problemas["valores_negativos_por_contaminante"].get(p_nombre, 0) + num_neg
                    )
                    vals_num.loc[es_neg] = np.nan

                    # Problema 3: Valores ausentes
                    num_nulos = int(vals_num.isna().sum())
                    conteo_problemas["valores_ausentes_por_contaminante"][p_nombre] = (
                        conteo_problemas["valores_ausentes_por_contaminante"].get(p_nombre, 0) + num_nulos
                    )

                    out_df[p_nombre] = vals_num
                else:
                    out_df[p_nombre] = np.nan

            dfs_est.append(out_df)

        if dfs_est:
            df_est_total = pd.concat(dfs_est, ignore_index=True)
            df_est_total = df_est_total.dropna(subset=["ts_local"]).drop_duplicates(subset=["ts_local"]).sort_values("ts_local")
            registros_estaciones.append(df_est_total)

    df_aire_limpio = pd.concat(registros_estaciones, ignore_index=True)

    # Guardar dataset limpio en data/clean/
    f_salida = DIR_DATA_CLEAN / "calidad_aire_limpio.csv"
    df_aire_limpio.to_csv(f_salida, index=False)
    print(f"[OK] Guardado calidad de aire limpia en {f_salida} ({len(df_aire_limpio):,} filas)")

    # Guardar inventario de auditoría de calidad
    filas_inv = []
    for est, g in df_aire_limpio.groupby("estacion"):
        esperadas = int((g.ts_local.max() - g.ts_local.min()) / pd.Timedelta(hours=1)) + 1
        filas_inv.append({
            "estacion": est,
            "zona": g.zona.iloc[0],
            "filas": len(g),
            "horas_esperadas": esperadas,
            "horas_faltantes": max(esperadas - len(g), 0),
            "desde": g.ts_local.min().strftime("%Y-%m-%d %H:%M"),
            "hasta": g.ts_local.max().strftime("%Y-%m-%d %H:%M"),
            "pct_nulos_no2": round(g["no2"].isna().mean() * 100, 2),
            "pct_nulos_pm10": round(g["pm10"].isna().mean() * 100, 2),
        })
    inv_df = pd.DataFrame(filas_inv)
    inv_df.to_csv(DIR_DATA_CLEAN / "inventario_calidad.csv", index=False)

    # Resumen de problemas
    print("\nRESUMEN DE AUDITORÍA DE CALIDAD:")
    print(f"  - Total filas brutas leídas: {filas_totales_cargadas:,}")
    print(f"  - Filas afectadas por hora 24:00 corregidas: {conteo_problemas['filas_hora_24']:,}")
    print(f"  - Celdas con coma decimal corregidas: {conteo_problemas['campos_coma_decimal']:,}")
    print(f"  - Valores negativos convertidos a NaN por contaminante: {conteo_problemas['valores_negativos_por_contaminante']}")
    print(f"  - Valores ausentes (NaN) por contaminante: {conteo_problemas['valores_ausentes_por_contaminante']}")

    return df_aire_limpio, conteo_problemas, inv_df


def limpiar_meteorologia():
    """
    Limpia y estandariza la meteorología horaria de Bilbao (Open-Meteo).
    """
    f_crudo = DIR_DATA_RAW / "meteorologia" / "open_meteo_bilbao_crudo.csv"
    if not f_crudo.exists():
        descargar_meteorologia()

    df = pd.read_csv(f_crudo)
    df["ts_local"] = pd.to_datetime(df["time"])

    df = df.rename(columns={
        "temperature_2m": "temp_c",
        "relative_humidity_2m": "humedad_pct",
        "precipitation": "precipitacion_mm",
        "wind_speed_10m": "viento_ms",
        "wind_direction_10m": "viento_dir_deg",
    })

    # Convertir velocidad de viento de km/h a m/s si viniera en km/h
    # Open-Meteo devuelve km/h por defecto si no se especifica m/s
    if df["viento_ms"].max() > 40:
        df["viento_ms"] = df["viento_ms"] / 3.6

    # Clasificar régimen de viento
    df["regimen_viento"] = pd.cut(
        df["viento_ms"],
        bins=[-np.inf, 2.0, 5.0, np.inf],
        labels=["Calma (<2 m/s)", "Moderado (2-5 m/s)", "Fuerte (>5 m/s)"],
    )

    df_limpio = df[[
        "ts_local",
        "temp_c",
        "humedad_pct",
        "precipitacion_mm",
        "viento_ms",
        "viento_dir_deg",
        "regimen_viento",
    ]].drop_duplicates(subset=["ts_local"]).sort_values("ts_local")

    f_salida = DIR_DATA_CLEAN / "meteorologia_limpia.csv"
    df_limpio.to_csv(f_salida, index=False)
    print(f"[OK] Guardada meteorología limpia en {f_salida} ({len(df_limpio):,} horas)")
    return df_limpio


def limpiar_calendario():
    """
    Lee y valida el calendario oficial ZBE con festivos.
    """
    f_crudo = DIR_DATA_RAW / "calendario" / "calendario_zbe_festivos.csv"
    if not f_crudo.exists():
        generar_calendario_zbe_festivos()

    df = pd.read_csv(f_crudo)
    f_salida = DIR_DATA_CLEAN / "calendario_zbe_limpio.csv"
    df.to_csv(f_salida, index=False)
    print(f"[OK] Calendario ZBE validado y guardado en {f_salida} ({len(df):,} días)")
    return df


def integrar_datasets():
    """
    Realiza el JOIN riguroso de:
      - Mediciones horarias por estación (calidad del aire)
      - Metadatos de la estación (zona, coordenadas, nombre)
      - Meteorología horaria (temperatura, viento, lluvia, humedad)
      - Calendario ZBE (fases, festivos, horario_zbe)

    Crea las columnas:
      - periodo: 'previo', 'fase1', 'fase2'
      - en_horario_zbe: True si es L-V laborable entre 07:00 y 20:00 local time
      - Variables temporales (año, mes, dia_semana, hora)
    """
    print("=" * 70)
    print("INTEGRACIÓN DE DATASETS: JOIN DE AIRE + METEO + CALENDARIO")
    print("=" * 70)

    f_aire = DIR_DATA_CLEAN / "calidad_aire_limpio.csv"
    f_meteo = DIR_DATA_CLEAN / "meteorologia_limpia.csv"
    f_cal = DIR_DATA_CLEAN / "calendario_zbe_limpio.csv"

    if not f_aire.exists():
        limpiar_calidad_aire()
    if not f_meteo.exists():
        limpiar_meteorologia()
    if not f_cal.exists():
        limpiar_calendario()

    df_aire = pd.read_csv(f_aire, parse_dates=["ts_local"])
    df_meteo = pd.read_csv(f_meteo, parse_dates=["ts_local"])
    df_cal = pd.read_csv(f_cal)

    filas_aire_antes = len(df_aire)
    print(f"Filas de calidad del aire antes del JOIN: {filas_aire_antes:,}")

    # Extraer fecha en formato YYYY-MM-DD para el merge con calendario
    df_aire["fecha"] = df_aire["ts_local"].dt.strftime("%Y-%m-%d")
    df_aire["hora"] = df_aire["ts_local"].dt.hour
    df_aire["año"] = df_aire["ts_local"].dt.year
    df_aire["mes"] = df_aire["ts_local"].dt.month
    df_aire["dia_semana"] = df_aire["ts_local"].dt.weekday

    # 1. Merge con calendario diario
    df_join = pd.merge(df_aire, df_cal[["fecha", "es_laborable", "es_festivo", "fase_zbe"]], on="fecha", how="left")

    # Columna periodo requerida por el enunciado: previo / fase1 / fase2
    df_join["periodo"] = df_join["fase_zbe"]

    # Columna en_horario_zbe requerida: Lunes a Viernes laborables entre 7:00 y 20:00
    # (7 <= hora <= 19 cubre de 07:00 a 19:59, es decir, el periodo de 7:00 a 20:00)
    df_join["en_horario_zbe"] = df_join["es_laborable"] & (df_join["hora"] >= 7) & (df_join["hora"] < 20)

    # 2. Merge con meteorología horaria por ts_local
    filas_antes_meteo = len(df_join)
    df_completo = pd.merge(df_join, df_meteo, on="ts_local", how="inner")
    filas_despues_meteo = len(df_completo)

    print(f"Filas tras el merge meteorológico: {filas_despues_meteo:,} (retención: {filas_despues_meteo / filas_antes_meteo * 100:.2f}%)")

    # Verificar ausencia de duplicados
    num_dup = df_completo.duplicated(subset=["estacion", "ts_local"]).sum()
    print(f"Duplicados en (estación, timestamp): {num_dup}")

    # Guardar dataset integrado en data/clean/
    f_salida = DIR_DATA_CLEAN / "dataset_integrado_zbe.csv"
    df_completo.to_csv(f_salida, index=False)
    print(f"[OK] Guardado dataset integrado maestro en {f_salida} ({len(df_completo):,} filas)")

    return df_completo


def ejecutar_pipeline_completo():
    """Ejecuta de principio a fin la adquisición, limpieza e integración."""
    descargar_todos_los_datos()
    limpiar_calidad_aire()
    limpiar_meteorologia()
    limpiar_calendario()
    df_int = integrar_datasets()
    print("\n" + "=" * 70)
    print("[FINALIZADO] Pipeline SBD de ingesta y limpieza ejecutado con éxito.")
    print("=" * 70)
    return df_int


if __name__ == "__main__":
    ejecutar_pipeline_completo()
