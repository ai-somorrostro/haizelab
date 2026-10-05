#!/usr/bin/env python3
"""
ejecutar_todo.py - Orquestador maestro del pipeline de HaizeLab
==============================================================

Ejecuta secuencialmente los 6 módulos del proyecto:
  1. Extraer y limpiar calidad del aire (NO2)
  2. Extraer y limpiar meteorología (Monte Banderas)
  3. Extraer tráfico de accesos a Bilbao (memorias PDF de Bizkaia)
  4. Unificar datos horarios y consolidar indicadores
  5. Análisis estadístico de impacto (Diff-in-Diff + Control climático)
  6. Generar visualizaciones y dashboard para toma de decisiones

USO:
  python ejecutar_todo.py           # Ejecuta el pipeline completo
  python ejecutar_todo.py --paso 6  # Ejecuta solo un paso específico (1 a 6)
"""

import sys
import subprocess
import argparse
from pathlib import Path

PASOS = [
    (1, "scripts/01_extraer_calidad_aire.py", "Extracción y limpieza de Calidad del Aire (NO2)"),
    (2, "scripts/02_extraer_meteorologia.py", "Extracción y limpieza de Meteorología (Monte Banderas)"),
    (3, "scripts/03_extraer_trafico.py",      "Extracción de Tráfico y Aforos (PDFs Bizkaia)"),
    (4, "scripts/04_unificar_datos.py",       "Unificación de datos (Aire + Meteo + Tráfico)"),
    (5, "scripts/05_analisis_impacto_zbe.py",  "Análisis estadístico multivariable de impacto ZBE"),
    (6, "scripts/06_visualizar_decision.py",  "Generación de gráficos y dashboard de decisión"),
]


def ejecutar_script(ruta_script: str, descripcion: str):
    print("\n" + "=" * 80)
    print(f">> EJECUTANDO: {descripcion}")
    print(f">> Script: {ruta_script}")
    print("=" * 80)
    
    cmd = [sys.executable, ruta_script]
    res = subprocess.run(cmd)
    if res.returncode != 0:
        print(f"\n[!] ERROR en {ruta_script} (código de salida: {res.returncode})")
        sys.exit(res.returncode)


def main():
    parser = argparse.ArgumentParser(description="Orquestador del pipeline HaizeLab")
    parser.add_argument("--paso", type=int, choices=range(1, 7), help="Ejecutar solo el paso indicado (1-6)")
    args = parser.parse_args()

    if args.paso:
        pasos_a_ejecutar = [p for p in PASOS if p[0] == args.paso]
    else:
        pasos_a_ejecutar = PASOS

    print("\n" + "#" * 80)
    print("  HAIZELAB — PIPELINE DE ANÁLISIS MULTIVARIABLE ZBE BILBAO")
    print("#" * 80)

    for num, ruta, desc in pasos_a_ejecutar:
        ejecutar_script(ruta, desc)

    print("\n" + "#" * 80)
    print("  [EXITO] Pipeline completado. Resultados listos en ./salida/ y ./datos/procesados/")
    print("#" * 80 + "\n")


if __name__ == "__main__":
    main()
