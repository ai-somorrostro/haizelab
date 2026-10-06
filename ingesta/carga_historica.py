#!/usr/bin/env python3
"""
ingesta/carga_historica.py
==========================

Carga datos históricos de los CSVs procesados directamente en InfluxDB 2
usando la API de escritura en línea de protocolo (line protocol via HTTP).

Buckets de destino:
  - aire     → datos de calidad del aire (NO2 horario, todas las estaciones)
  - meteo    → meteorología horaria histórica (temp, viento, humedad)

El tráfico histórico es agregado anual (IMD) sin marca temporal granular,
no tiene sentido subirlo a InfluxDB; se ignora aquí.

Requisitos:
  pip install pandas requests python-dotenv

Uso desde la raíz del proyecto:
  python ingesta/carga_historica.py [--bucket aire|meteo|all] [--dry-run]

Variables de entorno necesarias (en .env):
  INFLUXDB_URL          → http://localhost:8086
  INFLUXDB_ORG          → haizenlab
  INFLUXDB_ADMIN_TOKEN  → <token-admin>

Optimizaciones:
  - Carga en batches de 5000 puntos para no saturar la API.
  - Si el bucket ya tiene datos, se puede forzar con --force (no idempotente).
  - Usa pandas chunked read para ficheros grandes (NO2 ~1 M filas).
"""

import argparse
import os
import sys
import zipfile
from pathlib import Path

import pandas as pd
import requests

# ── Configuración ──────────────────────────────────────────────────────────────
DIR_BASE = Path(__file__).resolve().parent.parent
DIR_PROCESADOS = DIR_BASE / "datos" / "procesados"

ARCHIVO_NO2_ZIP  = DIR_PROCESADOS / "calidad_aire" / "no2_horario_limpio.zip"
ARCHIVO_METEO    = DIR_PROCESADOS / "meteorologia" / "meteo_bilbao_horario.csv"

BATCH_SIZE = 5_000   # puntos por petición POST a InfluxDB


# ── Utilidades ─────────────────────────────────────────────────────────────────

def cargar_env() -> dict:
    """Lee .env del directorio raíz de forma tolerante (sin requerir python-dotenv forzoso)."""
    env_path = DIR_BASE / ".env"
    if env_path.exists():
        with open(env_path, encoding="utf-8") as f:
            for linea in f:
                linea = linea.strip()
                if not linea or linea.startswith("#") or "=" not in linea:
                    continue
                k, v = linea.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip("'\""))

    url   = os.environ.get("INFLUXDB_URL", "http://localhost:8086")
    org   = os.environ.get("INFLUXDB_ORG", "haizenlab")
    token = os.environ.get("INFLUXDB_BATCH_WRITE_TOKEN") or os.environ.get("INFLUXDB_ADMIN_TOKEN", "")
    if not token:
        print("ERROR: INFLUXDB_BATCH_WRITE_TOKEN ni INFLUXDB_ADMIN_TOKEN encontrados en .env", file=sys.stderr)
        sys.exit(1)
    return {"url": url, "org": org, "token": token}


def ts_a_nanosegundos(serie: pd.Series) -> pd.Series:
    """Convierte una serie de timestamps a nanosegundos Unix (entero)."""
    return pd.to_datetime(serie, utc=True).astype("int64")


def escribir_batch(cfg: dict, bucket: str, lineas: list[str], dry_run: bool) -> None:
    """Envía un batch de line protocol a InfluxDB."""
    if dry_run:
        print(f"  [DRY-RUN] Saltando escritura de {len(lineas)} puntos -> bucket '{bucket}'")
        return

    payload = "\n".join(lineas)
    url = f"{cfg['url']}/api/v2/write?org={cfg['org']}&bucket={bucket}&precision=ns"
    headers = {
        "Authorization": f"Token {cfg['token']}",
        "Content-Type": "text/plain; charset=utf-8",
    }
    resp = requests.post(url, headers=headers, data=payload.encode("utf-8"), timeout=30)
    if resp.status_code not in (200, 204):
        print(f"  ERROR HTTP {resp.status_code}: {resp.text[:300]}", file=sys.stderr)
        sys.exit(1)


def enviar_dataframe(cfg: dict, bucket: str, lineas_gen, dry_run: bool) -> int:
    """Itera el generador de line-protocol y envía en batches. Devuelve total puntos."""
    batch: list[str] = []
    total = 0
    for lp in lineas_gen:
        batch.append(lp)
        if len(batch) >= BATCH_SIZE:
            escribir_batch(cfg, bucket, batch, dry_run)
            total += len(batch)
            print(f"    -> {total:,} puntos enviados...", end="\r", flush=True)
            batch = []
    if batch:
        escribir_batch(cfg, bucket, batch, dry_run)
        total += len(batch)
    print(f"    -> {total:,} puntos enviados. [OK]           ")
    return total


# ── Carga NO2 histórico → bucket 'aire' ────────────────────────────────────────

def generar_lp_no2(df_chunk: pd.DataFrame):
    """
    Genera líneas de line protocol a partir de un chunk del DataFrame de NO2.

    Esquema:
      measurement: contaminantes
      tags:        estacion=<str>, zona=<str>
      fields:      no2=<float>
      timestamp:   nanosegundos UTC
    """
    ts_ns = ts_a_nanosegundos(df_chunk["ts"])
    for i, fila in df_chunk.iterrows():
        no2 = fila["no2"]
        if pd.isna(no2):
            continue
        estacion = str(fila["estacion"]).replace(" ", r"\ ").replace(",", r"\,")
        zona     = str(fila.get("zona", "sin_clasificar")).replace(" ", r"\ ")
        yield (
            f"contaminantes,estacion={estacion},zona={zona}"
            f" no2={float(no2):.4f}"
            f" {ts_ns[i]}"
        )


def cargar_no2(cfg: dict, dry_run: bool) -> None:
    """Lee el ZIP de NO2 directamente mediante stream y sube al bucket 'aire'."""
    if not ARCHIVO_NO2_ZIP.exists():
        print(f"ERROR: No se encontró {ARCHIVO_NO2_ZIP}", file=sys.stderr)
        sys.exit(1)

    print(f"\n[NO2] Abriendo ZIP: {ARCHIVO_NO2_ZIP.name}")
    chunk_size = 50_000
    total_global = 0

    with zipfile.ZipFile(ARCHIVO_NO2_ZIP) as z:
        nombre_interno = z.namelist()[0]
        print(f"  Fichero interno: {nombre_interno}")
        with z.open(nombre_interno) as f:
            reader = pd.read_csv(f, chunksize=chunk_size)
            for n_chunk, chunk in enumerate(reader, 1):
                filas_antes = len(chunk)
                chunk = chunk.dropna(subset=["no2"])
                print(f"  Chunk {n_chunk}: {filas_antes:,} filas -> {len(chunk):,} validas")
                total_global += enviar_dataframe(cfg, "aire", generar_lp_no2(chunk), dry_run)

    print(f"[NO2] Total puntos cargados en bucket 'aire': {total_global:,}")


# ── Carga Meteorología histórica → bucket 'meteo' ─────────────────────────────

def generar_lp_meteo(df: pd.DataFrame):
    """
    Genera líneas de line protocol para meteorología horaria.

    Esquema:
      measurement: clima
      tags:        ubicacion=bilbao, fuente=historico-open-meteo
      fields:      temp_c, viento_kmh, viento_dir, humedad
      timestamp:   nanosegundos UTC

    Nota: el CSV tiene viento en m/s; se convierte a km/h (× 3.6) para
    mantener consistencia con los datos en tiempo real de Node-RED.
    """
    ts_ns = ts_a_nanosegundos(df["ts"])
    for i, fila in df.iterrows():
        temp    = fila.get("temp_c")
        viento  = fila.get("viento_ms")
        dir_v   = fila.get("viento_dir")
        humedad = fila.get("humedad")

        if pd.isna(temp) and pd.isna(viento):
            continue

        campos = []
        if not pd.isna(temp):
            campos.append(f"temp_c={float(temp):.2f}")
        if not pd.isna(viento):
            campos.append(f"viento_kmh={float(viento) * 3.6:.2f}")
        if not pd.isna(dir_v):
            campos.append(f"viento_dir={float(dir_v):.1f}")
        if not pd.isna(humedad):
            campos.append(f"humedad={float(humedad):.1f}")

        if not campos:
            continue

        yield (
            f"clima,ubicacion=bilbao,fuente=historico-open-meteo"
            f" {','.join(campos)}"
            f" {ts_ns[i]}"
        )


def cargar_meteo(cfg: dict, dry_run: bool) -> None:
    """Lee el CSV de meteorología y sube al bucket 'meteo'."""
    if not ARCHIVO_METEO.exists():
        print(f"ERROR: No se encontró {ARCHIVO_METEO}", file=sys.stderr)
        sys.exit(1)

    print(f"\n[METEO] Leyendo: {ARCHIVO_METEO.name}")
    df = pd.read_csv(ARCHIVO_METEO)
    print(f"  {len(df):,} filas | columnas: {list(df.columns)}")

    total = enviar_dataframe(cfg, "meteo", generar_lp_meteo(df), dry_run)
    print(f"[METEO] Total puntos cargados en bucket 'meteo': {total:,}")


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Carga histórica de datos ambientales en InfluxDB 2"
    )
    parser.add_argument(
        "--bucket",
        choices=["aire", "meteo", "all"],
        default="all",
        help="Bucket de destino (default: all)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parsea y valida sin escribir en InfluxDB",
    )
    args = parser.parse_args()

    cfg = cargar_env()

    modo = "(DRY-RUN)" if args.dry_run else ""
    print(f"=== Carga histórica HaizeLab {modo} ===")
    print(f"  InfluxDB : {cfg['url']}")
    print(f"  Org      : {cfg['org']}")
    print(f"  Bucket   : {args.bucket}")
    print()

    if args.bucket in ("aire", "all"):
        cargar_no2(cfg, args.dry_run)

    if args.bucket in ("meteo", "all"):
        cargar_meteo(cfg, args.dry_run)

    print("\n=== Carga completada ===")


if __name__ == "__main__":
    main()
