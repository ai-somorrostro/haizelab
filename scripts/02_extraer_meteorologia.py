#!/usr/bin/env python3
"""
scripts/02_extraer_meteorologia.py
==================================

OBJETIVO:
  Extraer, limpiar y estandarizar las series temporales horarias de meteorología
  de la estación de Monte Banderas (Bilbao) y Feria de Muestras (BEC).

ENTRADA:
  - datos/crudo/meteorologia/**/BANDERAS_meteo.csv (2022-2026)

VARIABLES EXTRAÍDAS:
  - ts: Timestamp horario estandarizado (YYYY-MM-DD HH:MM:SS)
  - temp_c: Temperatura ambiente (°C)
  - viento_ms: Velocidad del viento (m/s)
  - viento_dir: Dirección del viento (0-360 grados)
  - humedad: Humedad relativa (%)

SALIDA:
  - datos/procesados/meteorologia/meteo_bilbao_horario.csv:
      Serie horaria completa y continua para Bilbao.
  - datos/procesados/meteorologia/resumen_meteo_periodos.csv:
      Comparativa de condiciones meteorológicas antes y después de la ZBE.
"""

from pathlib import Path
import sys
import pandas as pd
import numpy as np

# Rutas del proyecto
DIR_BASE = Path(__file__).resolve().parent.parent
DIR_CRUDO = DIR_BASE / "datos" / "crudo" / "meteorologia"
DIR_PROCESADOS = DIR_BASE / "datos" / "procesados" / "meteorologia"

FECHA_FASE1 = pd.Timestamp("2024-06-15")


def procesar_fichero_banderas(ruta: Path) -> pd.DataFrame:
    """Lee y limpia un fichero de meteorología de Monte Banderas."""
    try:
        df = pd.read_csv(ruta, sep=";", encoding="latin1")
    except Exception as e:
        print(f"[!] Error leyendo {ruta}: {e}")
        return None

    df.columns = [c.strip() for c in df.columns]

    # Columnas esperadas: Date, Hour  (GMT), D.vien (grados), H (%), Tº (ºC), V.vien (m/s)
    col_fecha = next((c for c in df.columns if "date" in c.lower() or "fecha" in c.lower()), None)
    col_hora = next((c for c in df.columns if "hour" in c.lower() or "hora" in c.lower()), None)
    col_temp = next((c for c in df.columns if "tº" in c.lower() or "temp" in c.lower()), None)
    col_viento = next((c for c in df.columns if "v.vien" in c.lower() or "viento" in c.lower()), None)
    col_dir = next((c for c in df.columns if "d.vien" in c.lower() or "dir" in c.lower()), None)
    col_hum = next((c for c in df.columns if "h (" in c.lower() or "hum" in c.lower()), None)

    if not col_fecha or not col_hora:
        return None

    # Procesar hora y fechas (gestión de 24:00)
    horas_raw = df[col_hora].astype(str).str.strip()
    is_24 = horas_raw.isin(["24:00", "24", "24:00:00"])
    h_clean = horas_raw.replace({"24:00": "00:00", "24": "00:00", "24:00:00": "00:00"})
    
    fechas_raw = df[col_fecha].astype(str).str.strip()
    ts = pd.to_datetime(fechas_raw + " " + h_clean, format="%d/%m/%Y %H:%M", errors="coerce")
    ts[is_24] += pd.Timedelta(days=1)

    def a_numero(col):
        if not col or col not in df.columns:
            return np.nan
        return pd.to_numeric(df[col].astype(str).str.replace(",", ".", regex=False), errors="coerce")

    out = pd.DataFrame({
        "ts": ts,
        "temp_c": a_numero(col_temp),
        "viento_ms": a_numero(col_viento),
        "viento_dir": a_numero(col_dir),
        "humedad": a_numero(col_hum)
    }).dropna(subset=["ts"])

    return out


def main():
    print("=" * 70)
    print("2. EXTRACCIÓN Y LIMPIEZA DE METEOROLOGÍA (BILBAO)")
    print("=" * 70)

    DIR_PROCESADOS.mkdir(parents=True, exist_ok=True)
    ficheros = sorted(DIR_CRUDO.rglob("*BANDERAS*.csv"))

    if not ficheros:
        sys.exit(f"ERROR: No se han encontrado ficheros de BANDERAS en {DIR_CRUDO}")

    print(f"Leyendo {len(ficheros)} ficheros meteorológicos de Monte Banderas...")
    dfs = []
    for f in ficheros:
        res = procesar_fichero_banderas(f)
        if res is not None and not res.empty:
            dfs.append(res)

    if not dfs:
        sys.exit("ERROR: No se pudieron procesar los ficheros meteorológicos.")

    df_meteo = pd.concat(dfs, ignore_index=True)
    df_meteo = df_meteo.drop_duplicates(subset=["ts"]).sort_values("ts").reset_index(drop=True)

    # Exportar serie horaria completa
    f_salida = DIR_PROCESADOS / "meteo_bilbao_horario.csv"
    df_meteo.to_csv(f_salida, index=False)
    print(f"-> Guardada serie horaria de meteorología: {f_salida} ({len(df_meteo):,} horas)")

    # Comparativa por periodos
    df_meteo["periodo"] = np.where(df_meteo["ts"] < FECHA_FASE1, "Pre-ZBE", "Post-ZBE")
    resumen = df_meteo.groupby("periodo")[["temp_c", "viento_ms", "humedad"]].mean().round(2)
    f_resumen = DIR_PROCESADOS / "resumen_meteo_periodos.csv"
    resumen.to_csv(f_resumen)
    print(f"-> Guardado resumen por periodos: {f_resumen}")

    print("\nCONDICIONES METEOROLÓGICAS MEDIAS EN BILBAO:")
    print(resumen.to_string())
    print("\n[OK] Meteorología procesada con éxito.\n")


if __name__ == "__main__":
    main()
