#!/usr/bin/env python3
"""
Comprobación rápida ZBE Bilbao: ¿ha bajado el NO2 dentro más que fuera?

USO
  1. Crea una carpeta "datos" junto a este script y mete dentro los ficheros
     horarios (CSV o XLSX) de Open Data Euskadi. Si el nombre del fichero
     contiene el de la estación (mazarredo, europa...), se detecta solo.
  2. pip install pandas numpy matplotlib openpyxl
  3. python zbe_check.py

SALIDA (carpeta "salida")
  aire_limpio.csv   -> ts, estacion, zona, no2 (una fila por hora y estación)
  inventario.csv    -> filas, rango de fechas, % nulos y huecos por estación
  comparacion.csv   -> media de NO2 por zona y periodo
  no2_mensual.png   -> evolución mensual dentro / fuera / fondo

Es una comprobación rápida SIN corrección meteorológica: sirve para decidir
si el enfoque se sostiene, no para la conclusión final.
"""
import re
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

CARPETA = Path("datos")
SALIDA = Path("salida")
FECHA_FASE1 = pd.Timestamp("2024-06-15")   # sin etiqueta ambiental
FECHA_FASE2 = pd.Timestamp("2025-06-16")   # etiqueta B no residentes
FUENTE_EN_UTC = False  # pon True si comprobáis que las horas vienen en GMT/UTC

# clave (sin tildes, minúsculas) -> (nombre canónico, zona)
# Zonas: dentro | fuera (control) | fondo. Comprobad con el listado oficial de calles.
ESTACIONES = {
    # --- DENTRO de la ZBE (barrios Abando e Indautxu) ---
    "mazarredo":    ("Mazarredo",      "dentro"),   # Alameda Mazarredo s/n (junto Guggenheim)
    "diaz de haro": ("Mª Díaz de Haro", "dentro"),  # C/ María Díaz de Haro 60 (punto control ZBE)
    "m diaz haro":  ("Mª Díaz de Haro", "dentro"),  # alias sin tilde

    # --- FUERA: municipios del Gran Bilbao (área metropolitana) ---
    "europa":       ("Europa",     "fuera"),   # Bilbao norte (fuera de la ZBE)
    "erandio":      ("Erandio",    "fuera"),
    "barakaldo":    ("Barakaldo",  "fuera"),
    "basauri":      ("Basauri",    "fuera"),
    "sestao":       ("Sestao",     "fuera"),
    "muskiz":       ("Muskiz",     "fuera"),
    "zierbena":     ("Zierbena",   "fuera"),
    "santurce":     ("Santurce",   "fuera"),
    "abanto":       ("Abanto",     "fuera"),
    "castrejana":   ("Castrejana", "fuera"),   # estación tráfico Bilbao sur
    "zalla":        ("Zalla",      "fuera"),
    "lemona":       ("Lemona",     "fuera"),
    "larrabetzu":   ("Larrabetzu", "fuera"),
    "ategorrieta":  ("Ategorrieta","fuera"),   # San Sebastián urbano
    "easo":         ("Easo",       "fuera"),   # San Sebastián urbano
    "anorga":       ("Anorga",     "fuera"),   # San Sebastián sur
    "hernani":      ("Hernani",    "fuera"),
    "lasarte":      ("Lasarte-Oria","fuera"),
    "andoain":      ("Andoain",    "fuera"),
    "durango":      ("Durango",    "fuera"),
    "llodio":       ("Llodio",     "fuera"),

    # --- FONDO: estaciones rurales / periféricas ---
    "arraiz":       ("Arraiz",     "fondo"),   # Monte Arraiz, fondo regional Bizkaia
    "montorra":     ("Montorra",   "fondo"),
    "pagoeta":      ("Pagoeta",    "fondo"),   # Parque Pagoeta (rural Gipuzkoa)
    "urkiola":      ("Urkiola",    "fondo"),   # Parque Natural Urkiola
    "valderejo":    ("Valderejo",  "fondo"),   # Parque Natural Valderejo (Álava)
    "elciego":      ("Elciego",    "fondo"),   # Rioja Alavesa (rural)
    "mundaka":      ("Mundaka",    "fondo"),   # Costa (marino)
    "serantes":     ("Serantes",   "fondo"),   # Monte Serantes
    "sangroniz":    ("Sangroniz",  "fondo"),   # Aeropuerto, periferia
}
# Códigos de estación según el roadmap (verifícalos al abrir los ficheros)
IDS = {"60": "mazarredo", "81": "diaz de haro", "62": "europa", "92": "arraiz"}


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def clasificar(texto):
    t = norm(texto)
    if t in IDS:
        t = IDS[t]
    for clave, (nombre, zona) in ESTACIONES.items():
        if clave in t or clave.replace(" ", "") in t.replace(" ", ""):
            return nombre, zona
    return str(texto).strip(), "sin_clasificar"


def leer(path):
    if path.suffix.lower() in (".xlsx", ".xls"):
        return pd.read_excel(path, dtype=str)
    err = None
    # Probamos primero con sep=";" para evitar que pandas malinterprete
    # la coma decimal de columnas como "PM2,5" como separador de campos.
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
                # Descartamos si la separación produjo una sola columna (mal parse)
                if len(df.columns) > 1:
                    return df
            except Exception as e:  # noqa: BLE001
                err = e
    raise err


def parse_dt(s):
    """Fecha-hora en una sola columna; 24:00 pasa a 00:00 del día siguiente."""
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
    # timedelta convierte 24 en las 00:00 del día siguiente (hora fin de periodo)
    return f.dt.normalize() + pd.to_timedelta(horas, unit="h")


def extraer_no2(df):
    """Devuelve (serie de NO2, máscara de filas). Acepta formato ancho o largo."""
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
        print(f"  [!] {path.name}: no encuentro fecha/hora o NO2. Columnas: {list(df.columns)}")
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
    ficheros = sorted(p for p in CARPETA.glob("**/*") if p.suffix.lower() in (".csv", ".xlsx", ".xls", ".txt"))
    if not ficheros:
        sys.exit(f"No hay ficheros en ./{CARPETA}/. Mete ahí los CSV/XLSX y vuelve a ejecutar.")
    print(f"Leyendo {len(ficheros)} ficheros...")
    partes = [p for p in (procesar_fichero(f) for f in ficheros) if p is not None]
    if not partes:
        sys.exit("No se ha podido leer ningún fichero. Pásame las columnas que salen arriba y lo ajusto.")
    df = pd.concat(partes, ignore_index=True)

    if FUENTE_EN_UTC:
        df["ts"] = df["ts"].dt.tz_localize("UTC").dt.tz_convert("Europe/Madrid").dt.tz_localize(None)

    df[["estacion", "zona"]] = df["estacion_raw"].apply(lambda x: pd.Series(clasificar(x)))
    df = df.dropna(subset=["ts"]).drop(columns="estacion_raw")
    neg = (df["no2"] < 0).sum()
    df.loc[df["no2"] < 0, "no2"] = np.nan
    df = df.drop_duplicates(subset=["estacion", "ts"]).sort_values(["estacion", "ts"])
    SALIDA.mkdir(exist_ok=True)
    df.to_csv(SALIDA / "aire_limpio.csv", index=False)

    # Inventario
    filas = []
    for est, g in df.groupby("estacion"):
        esperadas = int((g.ts.max() - g.ts.min()) / pd.Timedelta(hours=1)) + 1
        filas.append({
            "estacion": est, "zona": g.zona.iloc[0], "filas": len(g),
            "desde": g.ts.min(), "hasta": g.ts.max(),
            "pct_nulos_no2": round(100 * g.no2.isna().mean(), 1),
            "horas_ausentes": max(esperadas - len(g), 0),
        })
    inv = pd.DataFrame(filas)
    inv.to_csv(SALIDA / "inventario.csv", index=False)
    print("\n=== INVENTARIO ===")
    print(inv.to_string(index=False))
    print(f"\nValores de NO2 negativos descartados: {neg}")
    sc = inv[inv.zona == "sin_clasificar"]
    if len(sc):
        print("[!] Estaciones sin clasificar (añádelas a ESTACIONES):", ", ".join(sc.estacion))

    # Periodos
    d = df[df.zona.isin(["dentro", "fuera", "fondo"])].copy()
    d["periodo"] = np.select(
        [d.ts < FECHA_FASE1, d.ts < FECHA_FASE2],
        ["previo", "fase1"], default="fase2")
    comp = d.groupby(["zona", "periodo"]).no2.agg(["mean", "count"]).round(2).unstack("periodo")
    comp.to_csv(SALIDA / "comparacion.csv")
    print("\n=== NO2 MEDIO (µg/m3) POR ZONA Y PERIODO ===")
    print(comp.to_string())

    # Diferencia dentro-fuera, mensual, antes vs después
    d["mes"] = d.ts.dt.to_period("M").dt.to_timestamp()
    mensual = d.groupby(["mes", "zona"]).no2.mean().unstack("zona")
    if {"dentro", "fuera"} <= set(mensual.columns):
        dif = (mensual["dentro"] - mensual["fuera"]).dropna()
        pre = dif[dif.index < FECHA_FASE1.to_period("M").to_timestamp()]
        post = dif[dif.index > FECHA_FASE1.to_period("M").to_timestamp()]
        if len(pre) > 2 and len(post) > 2:
            efecto = post.mean() - pre.mean()
            se = np.sqrt(pre.var(ddof=1) / len(pre) + post.var(ddof=1) / len(post))
            print("\n=== DIFERENCIA DENTRO - FUERA (media de medias mensuales) ===")
            print(f"  antes  (n={len(pre)} meses): {pre.mean():+.2f}")
            print(f"  después(n={len(post)} meses): {post.mean():+.2f}")
            print(f"  cambio de la diferencia: {efecto:+.2f} µg/m3  (IC95% aprox. ±{1.96 * se:.2f})")
            print("  Negativo = dentro ha bajado más que fuera. Sin corregir clima ni tendencia;")
            print("  el IC ignora la autocorrelación, así que es optimista.")
        else:
            print("\n[!] Pocos meses antes/después para calcular la diferencia dentro-fuera.")
    else:
        print("\n[!] Faltan estaciones 'dentro' o 'fuera' para la comparación.")

    # Gráfico
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        ax = mensual.plot(figsize=(11, 5), marker="o", ms=3)
        for f, et in ((FECHA_FASE1, "Fase 1"), (FECHA_FASE2, "Fase 2")):
            ax.axvline(f, color="k", ls="--", lw=1)
            ax.text(f, ax.get_ylim()[1], et, va="top", ha="right", fontsize=9)
        ax.set_ylabel("NO2 medio mensual (µg/m3)")
        ax.set_title("NO2 por zona respecto a la ZBE de Bilbao")
        plt.tight_layout()
        plt.savefig(SALIDA / "no2_mensual.png", dpi=150)
        print(f"\nGráfico guardado en {SALIDA / 'no2_mensual.png'}")
    except ImportError:
        print("\n(matplotlib no instalado: se omite el gráfico)")


if __name__ == "__main__":
    main()