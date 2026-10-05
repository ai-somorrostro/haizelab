#!/usr/bin/env python3
"""
scripts/01_extraer_calidad_aire.py
==================================

OBJETIVO:
  Extraer, limpiar y clasificar los datos horarios de dióxido de nitrógeno (NO2)
  provenientes de la Red de Control de Calidad del Aire de Open Data Euskadi.

ENTRADA:
  - datos/crudo/calidad_aire/**/*.csv (ficheros horarios originales por estación y año)

SALIDA:
  - datos/procesados/calidad_aire/no2_horario_limpio.csv:
      Dataset horario unificado con columnas: [ts, estacion, zona, no2]
  - datos/procesados/calidad_aire/inventario_estaciones.csv:
      Control de calidad: número de registros, rango temporal y % de valores nulos por estación.
  - datos/procesados/calidad_aire/comparacion_zonas_periodos.csv:
      Medias de NO2 por zona (dentro, fuera, fondo) antes y después de la ZBE.

CLASIFICACIÓN DE ZONAS (Perímetro ZBE Bilbao):
  - DENTRO: Estaciones en el perímetro oficial ZBE (Abando e Indautxu):
      * Mazarredo (Alameda Mazarredo s/n, junto al Museo Guggenheim)
      * María Díaz de Haro (C/ María Díaz de Haro 60)
  - FUERA (Control urbano): Estaciones urbanas del Gran Bilbao fuera del perímetro:
      * Europa (Bilbao norte), Erandio, Barakaldo, Basauri, Sestao, Santurce, Castrejana, etc.
  - FONDO (Regional/Rural): Estaciones de fondo sin tráfico directo:
      * Arraiz, Serantes, Mundaka, Pagoeta, Montorra, Valderejo, etc.
"""

from pathlib import Path
import re
import sys
import unicodedata
import numpy as np
import pandas as pd

# Rutas del proyecto
DIR_BASE = Path(__file__).resolve().parent.parent
DIR_CRUDO = DIR_BASE / "datos" / "crudo" / "calidad_aire"
DIR_PROCESADOS = DIR_BASE / "datos" / "procesados" / "calidad_aire"

FECHA_FASE1 = pd.Timestamp("2024-06-15")  # Entrada en vigor Fase 1
FECHA_FASE2 = pd.Timestamp("2025-06-16")  # Fase 2

ESTACIONES = {
    # --- DENTRO de la ZBE (barrios Abando e Indautxu) ---
    "mazarredo":    ("Mazarredo",         "dentro"),
    "diaz de haro": ("Mª Díaz de Haro",   "dentro"),
    "m diaz haro":  ("Mª Díaz de Haro",   "dentro"),

    # --- FUERA: municipios del Gran Bilbao / Control Urbano ---
    "europa":       ("Europa",            "fuera"),
    "erandio":      ("Erandio",           "fuera"),
    "barakaldo":    ("Barakaldo",         "fuera"),
    "basauri":      ("Basauri",           "fuera"),
    "sestao":       ("Sestao",            "fuera"),
    "muskiz":       ("Muskiz",            "fuera"),
    "zierbena":     ("Zierbena",          "fuera"),
    "santurce":     ("Santurce",          "fuera"),
    "abanto":       ("Abanto",            "fuera"),
    "castrejana":   ("Castrejana",        "fuera"),
    "zalla":        ("Zalla",             "fuera"),
    "lemona":       ("Lemona",            "fuera"),
    "larrabetzu":   ("Larrabetzu",        "fuera"),
    "durango":      ("Durango",           "fuera"),
    "llodio":       ("Llodio",            "fuera"),
    "lasarte":      ("Lasarte-Oria",      "fuera"),
    "andoain":      ("Andoain",           "fuera"),
    "hernani":      ("Hernani",           "fuera"),
    "easo":         ("Easo",              "fuera"),
    "categorrieta": ("Ategorrieta",       "fuera"),
    "anorga":       ("Anorga",            "fuera"),

    # --- FONDO: Regional / Marino / Rural ---
    "arraiz":       ("Arraiz",            "fondo"),
    "serantes":     ("Serantes",          "fondo"),
    "montorra":     ("Montorra",          "fondo"),
    "sangroniz":    ("Sangroniz",         "fondo"),
    "mundaka":      ("Mundaka",           "fondo"),
    "pagoeta":      ("Pagoeta",           "fondo"),
    "valderejo":    ("Valderejo",         "fondo"),
    "elciego":      ("Elciego",           "fondo"),
}


def norm(s):
    if s is None:
        return ""
    t = unicodedata.normalize("NFKD", str(s))
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    return re.sub(r"\s+", " ", t).strip()


def clasificar(texto):
    t = norm(texto)
    for clave, (nombre, zona) in ESTACIONES.items():
        if clave in t or clave.replace(" ", "") in t.replace(" ", ""):
            return nombre, zona
    return str(texto).strip(), "sin_clasificar"


def leer(path):
    if path.suffix.lower() in (".xlsx", ".xls"):
        return pd.read_excel(path, dtype=str)
    err = None
    for enc in ("utf-8-sig", "latin-1"):
        for sep in (";", ",", None):
            try:
                kwargs = dict(encoding=enc, dtype=str)
                if sep is None:
                    kwargs["sep"] = None
                    kwargs["engine"] = "python"
                else:
                    kwargs["sep"] = sep
                df = pd.read_csv(path, **kwargs)
                if len(df.columns) > 1:
                    return df
            except Exception as e:
                err = e
    raise err


def parse_dt(s):
    s = s.astype(str).str.strip()
    es24 = s.str.contains(r"\b24:00", regex=True)
    s2 = s.str.replace(r"\b24:00(:00)?", "00:00", regex=True)
    dayfirst = not s2.str.match(r"^\d{4}-").all()
    dt = pd.to_datetime(s2, dayfirst=dayfirst, errors="coerce")
    return dt.where(~es24, dt + pd.Timedelta(days=1))


def construir_ts(df):
    cols = {norm(c): c for c in df.columns}
    for k in ("fecha hora", "fechahora", "datetime", "timestamp", "fecha y hora"):
        if k in cols:
            return parse_dt(df[cols[k]])
    fecha = next((c for k, c in cols.items() if k.startswith("fecha") or k in ("date", "fecha")), None)
    hora = next((c for k, c in cols.items()
                 if k.startswith("hora")
                 or k in ("hour", "h")
                 or k.startswith("hour")
                 or k.startswith("h ")), None)
    if fecha is None:
        return None
    if hora is None:
        return parse_dt(df[fecha])
    s = df[fecha].astype(str).str.strip()
    f = pd.to_datetime(s, dayfirst=not s.str.match(r"^\d{4}-").all(), errors="coerce")
    h = df[hora].astype(str).str.strip()
    if h.str.contains(":").any():
        hm = h.str.extract(r"(\d{1,2}):(\d{2})").astype(float)
        horas = hm[0] + hm[1] / 60
    else:
        horas = pd.to_numeric(h, errors="coerce")
    return f.dt.normalize() + pd.to_timedelta(horas, unit="h")


def extraer_no2(df):
    cols = {norm(c): c for c in df.columns}
    mag = next((c for k, c in cols.items()
                if k in ("magnitud", "parametro", "contaminante", "pollutant", "variable")), None)
    val = next((c for k, c in cols.items()
                if k in ("valor", "value", "medida", "concentracion", "dato")), None)
    if mag and val:
        m = df[mag].map(norm).str.replace(" ", "")
        mask = m.str.contains("no2") | m.isin(["dioxidodenitrogeno", "nitrogendioxide"])
        return df.loc[mask, val], mask
    col = next((c for k, c in cols.items()
                if k.replace(" ", "").startswith("no2") or "dioxido de nitrogeno" in k), None)
    if col:
        return df[col], pd.Series(True, index=df.index)
    return None, None


def procesar_fichero(path):
    df = leer(path)
    ts = construir_ts(df)
    no2, mask = extraer_no2(df)
    if ts is None or no2 is None:
        return None
    col_est = next((c for c in df.columns
                    if norm(c) in ("estacion", "station", "nombre estacion", "codigo estacion", "id")), None)
    if col_est is not None:
        est = df.loc[mask, col_est]
    else:
        est = pd.Series(path.stem, index=df.index[mask])
    out = pd.DataFrame({
        "ts": ts[mask],
        "estacion_raw": est,
        "no2": pd.to_numeric(no2.astype(str).str.replace(",", ".", regex=False), errors="coerce"),
    })
    return out


def main():
    print("=" * 70)
    print("1. EXTRACCIÓN Y LIMPIEZA DE CALIDAD DEL AIRE (NO2)")
    print("=" * 70)

    DIR_PROCESADOS.mkdir(parents=True, exist_ok=True)
    ficheros = sorted(p for p in DIR_CRUDO.glob("**/*") if p.suffix.lower() in (".csv", ".xlsx", ".xls", ".txt"))

    if not ficheros:
        sys.exit(f"ERROR: No se han encontrado ficheros en {DIR_CRUDO}")

    print(f"Leyendo {len(ficheros)} ficheros de calidad del aire...")
    partes = [p for p in (procesar_fichero(f) for f in ficheros) if p is not None]
    if not partes:
        sys.exit("ERROR: No se ha podido leer ningún fichero.")

    df = pd.concat(partes, ignore_index=True)
    df[["estacion", "zona"]] = df["estacion_raw"].apply(lambda x: pd.Series(clasificar(x)))
    df = df.dropna(subset=["ts"]).drop(columns="estacion_raw")
    df.loc[df["no2"] < 0, "no2"] = np.nan
    df = df.drop_duplicates(subset=["estacion", "ts"]).sort_values(["estacion", "ts"])

    f_limpio = DIR_PROCESADOS / "no2_horario_limpio.csv"
    df.to_csv(f_limpio, index=False)
    print(f"-> Guardado dataset horario limpio: {f_limpio} ({len(df):,} filas)")

    # Comprimir en ZIP para permitir versionado ligero en GitHub (< 10 MB)
    import zipfile
    f_zip = DIR_PROCESADOS / "no2_horario_limpio.zip"
    with zipfile.ZipFile(f_zip, "w", zipfile.ZIP_DEFLATED, 9) as zf:
        zf.write(f_limpio, arcname=f_limpio.name)
    print(f"-> Guardada versión comprimida para Git: {f_zip} ({f_zip.stat().st_size / (1024*1024):.1f} MB)")

    # 1. Inventario
    filas = []
    for est, g in df.groupby("estacion"):
        esperadas = int((g.ts.max() - g.ts.min()) / pd.Timedelta(hours=1)) + 1
        filas.append({
            "estacion": est, "zona": g.zona.iloc[0], "filas": len(g),
            "desde": g.ts.min().strftime("%Y-%m-%d"), "hasta": g.ts.max().strftime("%Y-%m-%d"),
            "pct_nulos_no2": round(100 * g.no2.isna().mean(), 1),
            "horas_ausentes": max(esperadas - len(g), 0),
        })
    inv = pd.DataFrame(filas)
    f_inv = DIR_PROCESADOS / "inventario_estaciones.csv"
    inv.to_csv(f_inv, index=False)
    print(f"-> Guardado inventario de estaciones: {f_inv}")

    # 2. Periodos
    d = df[df.zona.isin(["dentro", "fuera", "fondo"])].copy()
    d["periodo"] = np.select(
        [d.ts < FECHA_FASE1, d.ts < FECHA_FASE2],
        ["previo", "fase1"], default="fase2")
    comp = d.groupby(["zona", "periodo"]).no2.agg(["mean", "count"]).round(2).unstack("periodo")
    f_comp = DIR_PROCESADOS / "comparacion_zonas_periodos.csv"
    comp.to_csv(f_comp)
    print(f"-> Guardada comparativa de periodos: {f_comp}")

    print("\nRESUMEN DE NO2 MEDIO (ug/m3) POR ZONA Y PERIODO:")
    print(comp["mean"].to_string())
    print("\n[OK] Calidad del aire procesada con éxito.\n")


if __name__ == "__main__":
    main()
