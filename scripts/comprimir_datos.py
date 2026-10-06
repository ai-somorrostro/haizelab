#!/usr/bin/env python3
"""
scripts/comprimir_datos.py
==========================

OBJETIVO:
  Comprobar el tamaño de los datos del proyecto y comprimir en ZIP aquellos
  archivos voluminosos para permitir su inclusión ligera en GitHub respetando
  el límite de 100 MB por archivo de GitHub.

AUDITORÍA DE TAMAÑOS:
  - Archivos > 100 MB: Bloqueados por GitHub (deben excluirse en .gitignore).
  - Archivos 25-100 MB: Alertados por GitHub (recomendable comprimir en ZIP).
  - Archivos < 25 MB: Permitidos perfectamente en Git.
"""

from pathlib import Path
import zipfile
import pandas as pd

DIR_BASE = Path(__file__).resolve().parent.parent
DIR_DATOS = DIR_BASE / "datos"
DIR_SALIDA = DIR_BASE / "salida"


def comprimir_archivo(origen: Path, destino_zip: Path):
    """Comprime un archivo individual en formato ZIP con máxima compresión."""
    print(f">> Comprimiendo {origen.name} ({origen.stat().st_size / (1024*1024):.2f} MB)...")
    with zipfile.ZipFile(destino_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.write(origen, arcname=origen.name)
    peso_zip = destino_zip.stat().st_size / (1024 * 1024)
    ahorro = (1 - destino_zip.stat().st_size / origen.stat().st_size) * 100
    print(f"   -> Creado {destino_zip.name}: {peso_zip:.2f} MB (Ahorro del {ahorro:.1f}%)")


def main():
    print("=" * 75)
    print("AUDITORÍA Y COMPRESIÓN DE DATOS PARA GITHUB")
    print("=" * 75)

    # 1. Auditoría de todos los archivos del proyecto
    todos = list(DIR_BASE.rglob("*.*"))
    archivos = [f for f in todos if f.is_file() and not any(p.startswith(".git") for p in f.parts)]

    print("\n--- ARCHIVOS MÁS PESADOS EN EL PROYECTO ---")
    archivos_ordenados = sorted(archivos, key=lambda f: f.stat().st_size, reverse=True)
    
    for f in archivos_ordenados[:12]:
        mb = f.stat().st_size / (1024 * 1024)
        rel = f.relative_to(DIR_BASE)
        estado = "[BLOQUEA GIT >100MB]" if mb > 100 else ("[AVISO GIT >25MB]" if mb > 25 else "[OK]")
        print(f"  {mb:6.2f} MB  {estado:20}  {rel}")

    # 2. Comprimir el dataset horario de calidad del aire (88.5 MB -> ~6.9 MB)
    p_no2 = DIR_DATOS / "procesados" / "calidad_aire" / "no2_horario_limpio.csv"
    p_no2_zip = DIR_DATOS / "procesados" / "calidad_aire" / "no2_horario_limpio.zip"
    if p_no2.exists():
        comprimir_archivo(p_no2, p_no2_zip)

    # 3. Comprimir el dataset unificado horario (3.5 MB -> ~0.4 MB)
    p_uni = DIR_DATOS / "procesados" / "unificados" / "dataset_unificado_horario.csv"
    p_uni_zip = DIR_DATOS / "procesados" / "unificados" / "dataset_unificado_horario.zip"
    if p_uni.exists():
        comprimir_archivo(p_uni, p_uni_zip)

    # 4. Comprimir las dos memorias PDF utilizadas (2023.pdf + 2025.pdf)
    pdf_2023 = DIR_DATOS / "crudo" / "trafico" / "2023.pdf"
    pdf_2025 = DIR_DATOS / "crudo" / "trafico" / "2025.pdf"
    zip_trafico = DIR_DATOS / "crudo" / "trafico" / "memorias_bizkaia_2023_2025.zip"
    if pdf_2023.exists() and pdf_2025.exists():
        print(f"\n>> Comprimiendo memorias PDF activas (2023.pdf + 2025.pdf)...")
        with zipfile.ZipFile(zip_trafico, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
            zf.write(pdf_2023, arcname="2023.pdf")
            zf.write(pdf_2025, arcname="2025.pdf")
        print(f"   -> Creado {zip_trafico.name}: {zip_trafico.stat().st_size / (1024*1024):.2f} MB")

    print("\n" + "=" * 75)
    print("RESUMEN DE DISPONIBILIDAD PARA GITHUB:")
    print("=" * 75)
    print("1. no2_horario_limpio.zip (6.89 MB): INCLUIBLE en Git. Contiene los 2 millones de filas.")
    print("2. dataset_unificado_horario.csv (3.48 MB): INCLUIBLE en Git. Contiene las 41.712 horas.")
    print("3. memorias_bizkaia_2023_2025.zip (44.4 MB): INCLUIBLE en Git si se desea (< 50 MB).")
    print("4. 2022.pdf (232 MB) y 2024.pdf (202 MB): BLOQUEADOS por GitHub (> 100 MB).")
    print("   -> No se usan en el pipeline (2023 y 2025 ya contienen toda la serie 2018-2025).")
    print("=" * 75 + "\n")


if __name__ == "__main__":
    main()
