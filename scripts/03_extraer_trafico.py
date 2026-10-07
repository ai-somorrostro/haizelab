#!/usr/bin/env python3
"""
scripts/03_extraer_trafico.py
=============================

OBJETIVO:
  Extraer y estructurar las intensidades medias diarias (IMD) de tráfico
  en todos los accesos a Bilbao y vías metropolitanas a partir de las
  memorias oficiales en PDF de la Diputación Foral de Bizkaia (2018-2025).

ENTRADA:
  - datos/crudo/trafico/2023.pdf (Memoria de Tráfico Bizkaia 2023)
  - datos/crudo/trafico/2025.pdf (Memoria de Tráfico Bizkaia 2025)

SALIDA:
  - datos/procesados/trafico/trafico_accesos_bilbao.csv:
      IMD por vía de acceso a Bilbao para 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025
      y variaciones porcentuales (incluyendo variación 2023->2024 inicio ZBE).
  - datos/procesados/trafico/trafico_circunvalacion.csv:
      IMD 2020-2025 en las rondas metropolitanas (Solución Sur, Rontegi, Txorierri, Este).
  - datos/procesados/trafico/resumen_trafico_zbe.csv:
      Resumen ejecutivo centrado en los accesos directos al centro y perímetro ZBE.
"""

from pathlib import Path
import sys
import pandas as pd
import pymupdf

# Rutas del proyecto
DIR_BASE = Path(__file__).resolve().parent.parent
DIR_CRUDO = DIR_BASE / "datos" / "crudo" / "trafico"
DIR_PROCESADOS = DIR_BASE / "datos" / "procesados" / "trafico"


def clean_num(val):
    """Limpia cadenas numéricas europeas (10.608 -> 10608.0)."""
    if not val or str(val).strip() in ("-", "None", ""):
        return None
    val_str = str(val).strip().replace(".", "").replace(",", ".")
    try:
        return float(val_str)
    except ValueError:
        return None


def extraer_accesos(pdf_2023: Path, pdf_2025: Path) -> pd.DataFrame:
    """Extrae la tabla A/5.1.1.1 de evolución del tráfico en los accesos a Bilbao."""
    # 1. 2025.pdf contiene 2020 a 2025 (Página 151 del documento, índice 150)
    doc_2025 = pymupdf.open(pdf_2025)
    tab_2025 = doc_2025[150].find_tables()
    if not tab_2025.tables:
        raise ValueError(f"No se encontró la tabla de accesos en {pdf_2025} pág 151")
    rows_2025 = tab_2025.tables[0].extract()

    # 2. 2023.pdf contiene 2018 a 2019 (Página 156 del documento, índice 155)
    doc_2023 = pymupdf.open(pdf_2023)
    tab_2023 = doc_2023[155].find_tables()
    rows_2023 = tab_2023.tables[0].extract() if tab_2023.tables else []

    prev_18_19 = {}
    for r in rows_2023[2:16]:
        nombre = r[0].replace("\x07", "").replace("\n", " ").strip()
        clave = nombre.split("(")[0].strip()
        prev_18_19[clave] = (clean_num(r[3]), clean_num(r[4]))

    registros = []
    current_zone = "NORTE"
    for r in rows_2025[2:16]:
        nombre_raw = r[0].replace("\x07", "").replace("\n", " ").strip() if r[0] else ""
        if "BOLUETA" in nombre_raw or "6." in nombre_raw:
            current_zone = "SUR"
        if "TOTAL" in nombre_raw:
            current_zone = "TOTAL"

        zona = r[1] if r[1] else current_zone
        if "TOTAL" in nombre_raw:
            zona = "TOTAL"

        estacion = r[2].replace("\n", " ").strip() if r[2] else ""
        clave = nombre_raw.split("(")[0].strip()
        val_18, val_19 = prev_18_19.get(clave, (None, None))

        imd_20 = clean_num(r[3])
        imd_21 = clean_num(r[4])
        imd_22 = clean_num(r[5])
        imd_23 = clean_num(r[6])
        imd_24 = clean_num(r[7])
        imd_25 = clean_num(r[8])
        pct_pes = clean_num(r[9]) if len(r) > 9 else None

        # Variaciones clave
        var_23_24 = ((imd_24 - imd_23) / imd_23 * 100) if (imd_23 and imd_24) else None
        var_22_24 = ((imd_24 - imd_22) / imd_22 * 100) if (imd_22 and imd_24) else None
        var_23_25 = ((imd_25 - imd_23) / imd_23 * 100) if (imd_23 and imd_25) else None
        var_24_25 = ((imd_25 - imd_24) / imd_24 * 100) if (imd_24 and imd_25) else None

        registros.append({
            "acceso": nombre_raw,
            "zona": zona,
            "estacion": estacion,
            "imd_2018": val_18,
            "imd_2019": val_19,
            "imd_2020": imd_20,
            "imd_2021": imd_21,
            "imd_2022": imd_22,
            "imd_2023": imd_23,
            "imd_2024": imd_24,
            "imd_2025": imd_25,
            "pct_pesados_2025": pct_pes,
            "var_pct_23_24": round(var_23_24, 2) if var_23_24 is not None else None,
            "var_pct_22_24": round(var_22_24, 2) if var_22_24 is not None else None,
            "var_pct_23_25": round(var_23_25, 2) if var_23_25 is not None else None,
            "var_pct_24_25": round(var_24_25, 2) if var_24_25 is not None else None
        })

    return pd.DataFrame(registros)


def extraer_circunvalacion(pdf_2025: Path) -> pd.DataFrame:
    """Extrae la tabla A/5.2.1.1 de vías de circunvalación (1er anillo metropolitano)."""
    doc = pymupdf.open(pdf_2025)
    tab = doc[165].find_tables()
    if not tab.tables:
        return pd.DataFrame()
    rows = tab.tables[0].extract()

    registros = []
    for r in rows[2:]:
        if not r or len(r) < 9:
            continue
        via = r[0].replace("\n", " ").strip() if r[0] else ""
        tramo = r[1].replace("\n", " ").strip() if r[1] else ""
        if not via and not tramo:
            continue
        km = clean_num(r[2])
        registros.append({
            "via": via,
            "tramo": tramo,
            "longitud_km": km,
            "imd_2020": clean_num(r[3]),
            "imd_2021": clean_num(r[4]),
            "imd_2022": clean_num(r[5]),
            "imd_2023": clean_num(r[6]),
            "imd_2024": clean_num(r[7]),
            "imd_2025": clean_num(r[8]),
            "pct_pesados": clean_num(r[9]) if len(r) > 9 else None
        })
    return pd.DataFrame(registros)


def main():
    print("=" * 70)
    print("3. EXTRACCIÓN DE TRÁFICO Y AFOROS (DIPUTACIÓN DE BIZKAIA)")
    print("=" * 70)

    DIR_PROCESADOS.mkdir(parents=True, exist_ok=True)
    pdf_2023 = DIR_CRUDO / "2023.pdf"
    pdf_2025 = DIR_CRUDO / "2025.pdf"

    if not pdf_2025.exists() or not pdf_2023.exists():
        print("\n" + "=" * 70)
        print("AVISO: Las memorias de tráfico oficiales en PDF no están presentes en:")
        print(f"  {DIR_CRUDO}")
        print("Los documentos PDF originales están excluidos del repositorio para mantenerlo ligero.")
        print("Los datos procesados de aforos y accesos ya están disponibles en:")
        print(f"  {DIR_PROCESADOS / 'trafico_accesos_bilbao.csv'}")
        print("Puedes ejecutar directamente el análisis cruzado con:")
        print("  python scripts/04_unificar_datos.py")
        print("=" * 70 + "\n")
        return

    print(f"Extrayendo accesos a Bilbao desde:\n  - {pdf_2023.name}\n  - {pdf_2025.name}")
    df_accesos = extraer_accesos(pdf_2023, pdf_2025)
    f_accesos = DIR_PROCESADOS / "trafico_accesos_bilbao.csv"
    df_accesos.to_csv(f_accesos, index=False)
    print(f"-> Guardado tráfico de accesos: {f_accesos}")

    df_circ = extraer_circunvalacion(pdf_2025)
    f_circ = DIR_PROCESADOS / "trafico_circunvalacion.csv"
    df_circ.to_csv(f_circ, index=False)
    print(f"-> Guardado tráfico de circunvalación: {f_circ}")

    # Resumen ejecutivo de accesos
    resumen_cols = ["acceso", "zona", "imd_2022", "imd_2023", "imd_2024", "imd_2025", "var_pct_23_24"]
    f_resumen = DIR_PROCESADOS / "resumen_trafico_zbe.csv"
    df_accesos[resumen_cols].to_csv(f_resumen, index=False)
    print(f"-> Guardado resumen ZBE tráfico: {f_resumen}")

    print("\nRESUMEN DE TRÁFICO EN LOS ACCESOS A BILBAO:")
    print(df_accesos[resumen_cols].to_string(index=False))

    sm = df_accesos[df_accesos.acceso.str.contains("SAN MAMES", case=False, na=False)]
    if not sm.empty:
        var = sm["var_pct_23_24"].iloc[0]
        print(f"\n[!] HALLAZGO: Acceso San Mamés (puerta de la ZBE) cayó {var:+.2f}% en 2024.")

    print("\n[OK] Tráfico procesado con éxito.\n")


if __name__ == "__main__":
    main()
