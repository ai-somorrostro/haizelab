#!/usr/bin/env python3
"""
extraer_trafico.py - Extracción de datos de aforos y tráfico de Bilbao y Bizkaia
a partir de las memorias oficiales de la Diputación Foral de Bizkaia.

Genera:
  - salida/trafico_accesos_bilbao.csv: IMD anual 2018-2025 por vía de acceso a Bilbao
  - salida/trafico_circunvalacion.csv: IMD 2020-2025 en los anillos metropolitanos
"""
import os
import sys
from pathlib import Path
import pandas as pd
import pymupdf

def clean_num(val):
    if not val or val == '-' or val == 'None':
        return None
    val_str = str(val).strip().replace('.', '').replace(',', '.')
    try:
        return float(val_str)
    except ValueError:
        return None

def buscar_pdf(nombre, descargas_dir=None):
    if descargas_dir is None:
        descargas_dir = Path.home() / "Downloads"
    posibles = [
        Path("datos/trafico") / nombre,
        Path("datos") / nombre,
        descargas_dir / nombre,
    ]
    for p in posibles:
        if p.exists():
            return p
    return None

def extraer_accesos(pdf_2023_path, pdf_2025_path):
    print(f"Leyendo accesos desde:\n  {pdf_2023_path}\n  {pdf_2025_path}")
    
    doc_2025 = pymupdf.open(pdf_2025_path)
    tab_2025 = doc_2025[150].find_tables()
    rows_2025 = tab_2025.tables[0].extract()
    
    doc_2023 = pymupdf.open(pdf_2023_path)
    tab_2023 = doc_2023[155].find_tables()
    rows_2023 = tab_2023.tables[0].extract()
    
    dict_prev = {}
    for r in rows_2023[2:16]:
        nombre = r[0].replace('\x07', '').replace('\n', ' ').strip()
        val_2018 = clean_num(r[3])
        val_2019 = clean_num(r[4])
        clave = nombre.split('(')[0].strip()
        dict_prev[clave] = (val_2018, val_2019)
    
    registros = []
    current_zone = 'NORTE'
    for r in rows_2025[2:16]:
        nombre_raw = r[0].replace('\x07', '').replace('\n', ' ').strip() if r[0] else ''
        if 'BOLUETA' in nombre_raw or '6.' in nombre_raw:
            current_zone = 'SUR'
        if 'TOTAL' in nombre_raw:
            current_zone = 'TOTAL'
        
        zona = r[1] if r[1] else current_zone
        if 'TOTAL' in nombre_raw:
            zona = 'TOTAL'
            
        estacion = r[2].replace('\n', ' ').strip() if r[2] else ''
        clave = nombre_raw.split('(')[0].strip()
        val_18, val_19 = dict_prev.get(clave, (None, None))
        
        imd_20 = clean_num(r[3])
        imd_21 = clean_num(r[4])
        imd_22 = clean_num(r[5])
        imd_23 = clean_num(r[6])
        imd_24 = clean_num(r[7])
        imd_25 = clean_num(r[8])
        pct_pes = clean_num(r[9])
        
        var_23_24 = ((imd_24 - imd_23) / imd_23 * 100) if (imd_23 and imd_24) else None
        var_22_24 = ((imd_24 - imd_22) / imd_22 * 100) if (imd_22 and imd_24) else None
        
        registros.append({
            'acceso': nombre_raw,
            'zona': zona,
            'estacion': estacion,
            'imd_2018': val_18,
            'imd_2019': val_19,
            'imd_2020': imd_20,
            'imd_2021': imd_21,
            'imd_2022': imd_22,
            'imd_2023': imd_23,
            'imd_2024': imd_24,
            'imd_2025': imd_25,
            'pct_pesados_2025': pct_pes,
            'var_pct_23_24': round(var_23_24, 2) if var_23_24 is not None else None,
            'var_pct_22_24': round(var_22_24, 2) if var_22_24 is not None else None,
        })
    
    return pd.DataFrame(registros)

def extraer_circunvalacion(pdf_2025_path):
    print("Leyendo circunvalación desde 2025.pdf (página 166)...")
    doc = pymupdf.open(pdf_2025_path)
    tab = doc[165].find_tables()
    rows = tab.tables[0].extract()
    
    registros = []
    for r in rows[2:]:
        if not r or len(r) < 9:
            continue
        via = r[0].replace('\n', ' ').strip() if r[0] else ''
        tramo = r[1].replace('\n', ' ').strip() if r[1] else ''
        if not via and not tramo:
            continue
        km = clean_num(r[2])
        registros.append({
            'via': via,
            'tramo': tramo,
            'longitud_km': km,
            'imd_2020': clean_num(r[3]),
            'imd_2021': clean_num(r[4]),
            'imd_2022': clean_num(r[5]),
            'imd_2023': clean_num(r[6]),
            'imd_2024': clean_num(r[7]),
            'imd_2025': clean_num(r[8]),
            'pct_pesados': clean_num(r[9]) if len(r) > 9 else None,
        })
    return pd.DataFrame(registros)

def main():
    salida_dir = Path("salida")
    salida_dir.mkdir(exist_ok=True)
    
    pdf_2023 = buscar_pdf("2023.pdf")
    pdf_2025 = buscar_pdf("2025.pdf")
    
    if not pdf_2025 or not pdf_2023:
        print("ERROR: No se han encontrado 2023.pdf y 2025.pdf en Downloads ni en datos/.")
        sys.exit(1)
        
    df_accesos = extraer_accesos(pdf_2023, pdf_2025)
    f_accesos = salida_dir / "trafico_accesos_bilbao.csv"
    df_accesos.to_csv(f_accesos, index=False, encoding="utf-8")
    print(f"-> Guardado: {f_accesos}")
    
    df_circ = extraer_circunvalacion(pdf_2025)
    f_circ = salida_dir / "trafico_circunvalacion.csv"
    df_circ.to_csv(f_circ, index=False, encoding="utf-8")
    print(f"-> Guardado: {f_circ}")
    
    # Resumen
    print("\n" + "="*80)
    print("RESUMEN DE TRÁFICO EN LOS ACCESOS A BILBAO (2020 - 2025)")
    print("="*80)
    cols_show = ['acceso', 'zona', 'imd_2022', 'imd_2023', 'imd_2024', 'imd_2025', 'var_pct_23_24']
    print(df_accesos[cols_show].to_string(index=False))
    print("="*80)

if __name__ == "__main__":
    main()
