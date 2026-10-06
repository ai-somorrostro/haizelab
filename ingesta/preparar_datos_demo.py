#!/usr/bin/env python3
"""
ingesta/preparar_datos_demo.py
==============================

Extrae del ZIP principal solo las 4 estaciones de la demo de NO2
y genera un CSV reducido que monta el contenedor Node-RED.

Salida: ingesta/no2_demo_reducido.csv  (no se sube a git si pesa mas de unos MB)

Columnas de salida:
  ts          - timestamp original (ISO)
  estacion    - nombre limpio de la estacion (ASCII para compatibilidad Linux)
  zona        - clasificacion ZBE (dentro/fuera/fondo)
  no2         - concentracion de NO2 en ug/m3

Nota: M_DIAZ_HARO aparece como sin_clasificar en el CSV fuente; aqui lo
reclasificamos como MDiazDeHaro con zona dentro, sin modificar el script original.
"""

from pathlib import Path
import zipfile
import pandas as pd

# -- Rutas ---------------------------------------------------------------------
DIR_BASE   = Path(__file__).resolve().parent.parent
ZIP_FUENTE = DIR_BASE / "datos" / "procesados" / "calidad_aire" / "no2_horario_limpio.zip"
SALIDA     = DIR_BASE / "ingesta" / "no2_demo_reducido.csv"

# -- Mapeo de estaciones objetivo ----------------------------------------------
# clave = nombre en el CSV fuente, valor = (nombre_limpio_ascii, zona)
ESTACIONES_DEMO = {
    "Mazarredo":   ("Mazarredo",        "dentro"),
    "M_DIAZ_HARO": ("Mª Díaz de Haro", "dentro"),
    "Europa":      ("Europa",           "fuera"),
    "Arraiz":      ("Arraiz",           "fondo"),
}


def main():
    if not ZIP_FUENTE.exists():
        raise FileNotFoundError(f"ZIP no encontrado: {ZIP_FUENTE}")

    print(f"Leyendo {ZIP_FUENTE} ...")
    with zipfile.ZipFile(ZIP_FUENTE) as z:
        nombre_interno = z.namelist()[0]
        print(f"  Fichero interno: {nombre_interno}")
        with z.open(nombre_interno) as f:
            df = pd.read_csv(f)

    print(f"Total filas en ZIP: {len(df):,}")

    partes = []
    for est_raw, (nombre_limpio, zona) in ESTACIONES_DEMO.items():
        sub = df[df["estacion"] == est_raw].copy()
        if sub.empty:
            print(f"  AVISO: No hay filas para estacion='{est_raw}'")
            continue
        sub["estacion"] = nombre_limpio
        sub["zona"]     = zona
        partes.append(sub)
        print(f"  {est_raw:20s} -> {nombre_limpio:20s} ({zona}) : {len(sub):,} filas")

    if not partes:
        raise ValueError("No se han podido extraer datos de ninguna estacion")

    demo = pd.concat(partes, ignore_index=True)
    demo = demo.dropna(subset=["no2"]).sort_values(["ts", "estacion"]).reset_index(drop=True)
    demo = demo[["ts", "estacion", "zona", "no2"]]

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    demo.to_csv(SALIDA, index=False, encoding="utf-8")

    tam_mb = SALIDA.stat().st_size / 1024 / 1024
    print(f"\nGuardado: {SALIDA}")
    print(f"Filas finales: {len(demo):,}")
    print(f"Tamano: {tam_mb:.1f} MB")
    print(f"Rango temporal: {demo['ts'].min()} -- {demo['ts'].max()}")

    if tam_mb > 10:
        print("AVISO: El fichero supera 10 MB, considera anadirlo a .gitignore.")


if __name__ == "__main__":
    main()
