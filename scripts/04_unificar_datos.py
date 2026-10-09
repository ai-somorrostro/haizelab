#!/usr/bin/env python3
"""
scripts/04_unificar_datos.py
============================

OBJETIVO:
  Cruzar a nivel horario los datos procesados de calidad del aire y meteorología,
  y asociar las métricas de tráfico para generar el dataset maestro unificado.

ENTRADA:
  - datos/procesados/calidad_aire/no2_horario_limpio.csv
  - datos/procesados/meteorologia/meteo_bilbao_horario.csv
  - datos/procesados/trafico/trafico_accesos_bilbao.csv

SALIDA:
  - datos/procesados/unificados/dataset_unificado_horario.csv:
      Timestamp, NO2 dentro, NO2 fuera, NO2 fondo, temp_c, viento_ms, humedad,
      periodo (Pre-ZBE / Fase 1 / Fase 2), regimen_viento (Calma / Moderado / Fuerte).
  - datos/procesados/unificados/sintesis_ejecutiva_zbe.csv:
      Resumen consolidado con los indicadores clave (aire, tráfico, clima).
"""

from pathlib import Path
import numpy as np
import pandas as pd

# Rutas del proyecto
DIR_BASE = Path(__file__).resolve().parent.parent
DIR_AIRE = DIR_BASE / "datos" / "procesados" / "calidad_aire"
DIR_METEO = DIR_BASE / "datos" / "procesados" / "meteorologia"
DIR_TRAFICO = DIR_BASE / "datos" / "procesados" / "trafico"
DIR_UNIFICADOS = DIR_BASE / "datos" / "procesados" / "unificados"

FECHA_FASE1 = pd.Timestamp("2024-06-15")
FECHA_FASE2 = pd.Timestamp("2025-06-16")


def main():
    print("=" * 70)
    print("4. UNIFICACIÓN DE DATOS (AIRE + METEO + TRÁFICO)")
    print("=" * 70)

    DIR_UNIFICADOS.mkdir(parents=True, exist_ok=True)

    f_aire_csv = DIR_AIRE / "no2_horario_limpio.csv"
    f_aire_zip = DIR_AIRE / "no2_horario_limpio.zip"
    f_aire = f_aire_csv if f_aire_csv.exists() else f_aire_zip
    f_meteo = DIR_METEO / "meteo_bilbao_horario.csv"
    f_traf = DIR_TRAFICO / "trafico_accesos_bilbao.csv"

    if not f_aire.exists() or not f_meteo.exists() or not f_traf.exists():
        sys.exit("ERROR: Faltan archivos procesados. Ejecuta antes los scripts 01, 02 y 03.")

    print(f"Cargando datasets procesados ({f_aire.name})...")
    df_aire = pd.read_csv(f_aire, parse_dates=["ts"])
    df_meteo = pd.read_csv(f_meteo, parse_dates=["ts"])
    df_traf = pd.read_csv(f_traf)

    # 1. Pivotar NO2 horario por zona (dentro, fuera, fondo)
    print("Agregando NO2 horario por zonas...")
    df_zonas = df_aire[df_aire.zona.isin(["dentro", "fuera", "fondo"])].groupby(
        ["ts", "zona"]
    )["no2"].mean().unstack("zona").reset_index()

    renombrar = {c: f"no2_{c}" for c in ["dentro", "fuera", "fondo"] if c in df_zonas.columns}
    df_zonas = df_zonas.rename(columns=renombrar)

    # 2. Merge con meteorología
    print("Cruzando con datos meteorológicos de Monte Banderas...")
    df_unificado = pd.merge(df_zonas, df_meteo, on="ts", how="inner")

    # 3. Enriquecer con periodos y clasificaciones
    df_unificado["periodo"] = np.select(
        [df_unificado["ts"] < FECHA_FASE1, df_unificado["ts"] < FECHA_FASE2],
        ["previo", "fase1"],
        default="fase2"
    )

    df_unificado["regimen_viento"] = pd.cut(
        df_unificado["viento_ms"],
        bins=[-np.inf, 2.0, 5.0, np.inf],
        labels=["Calma (<2 m/s)", "Moderado (2-5 m/s)", "Fuerte (>5 m/s)"]
    )

    f_salida_unificado = DIR_UNIFICADOS / "dataset_unificado_horario.csv"
    df_unificado.to_csv(f_salida_unificado, index=False)
    print(f"-> Guardado dataset horario unificado: {f_salida_unificado} ({len(df_unificado):,} horas)")

    # 4. Generar Síntesis Ejecutiva Consolidada
    print("Calculando indicadores ejecutivos...")
    
    # NO2 dentro
    no2_pre = df_unificado[df_unificado.periodo == "previo"]["no2_dentro"].mean()
    no2_post = df_unificado[df_unificado.periodo.isin(["fase1", "fase2"])]["no2_dentro"].mean()
    var_no2_dentro = ((no2_post - no2_pre) / no2_pre) * 100

    # NO2 control fuera
    fuera_pre = df_unificado[df_unificado.periodo == "previo"]["no2_fuera"].mean()
    fuera_post = df_unificado[df_unificado.periodo.isin(["fase1", "fase2"])]["no2_fuera"].mean()
    var_no2_fuera = ((fuera_post - fuera_pre) / fuera_pre) * 100

    # Impacto neto Diferencias en Diferencias (Diff-in-Diff)
    efecto_neto_did = (no2_post - no2_pre) - (fuera_post - fuera_pre)
    var_neta_did_pct = (efecto_neto_did / no2_pre) * 100

    # NO2 dentro en calma (< 2 m/s)
    calma_pre = df_unificado[(df_unificado.periodo == "previo") & (df_unificado.regimen_viento == "Calma (<2 m/s)")]["no2_dentro"].mean()
    calma_f1 = df_unificado[(df_unificado.periodo == "fase1") & (df_unificado.regimen_viento == "Calma (<2 m/s)")]["no2_dentro"].mean()
    calma_post = df_unificado[(df_unificado.periodo.isin(["fase1", "fase2"])) & (df_unificado.regimen_viento == "Calma (<2 m/s)")]["no2_dentro"].mean()
    var_no2_calma_f1 = ((calma_f1 - calma_pre) / calma_pre) * 100
    var_no2_calma_post = ((calma_post - calma_pre) / calma_pre) * 100

    # Tráfico San Mamés
    row_sm = df_traf[df_traf.acceso.str.contains("SAN MAMES", case=False, na=False)]
    traf_sm_23 = row_sm["imd_2023"].iloc[0] if not row_sm.empty else None
    traf_sm_24 = row_sm["imd_2024"].iloc[0] if not row_sm.empty else None
    traf_sm_25 = row_sm["imd_2025"].iloc[0] if not row_sm.empty else None
    traf_sm_var_23_24 = row_sm["var_pct_23_24"].iloc[0] if not row_sm.empty else np.nan
    traf_sm_var_23_25 = row_sm["var_pct_23_25"].iloc[0] if not row_sm.empty else np.nan
    traf_sm_var_24_25 = row_sm["var_pct_24_25"].iloc[0] if not row_sm.empty else np.nan

    # Tráfico Total
    row_tot = df_traf[df_traf.acceso.str.contains("TOTAL", case=False, na=False)]
    traf_tot_var = row_tot["var_pct_23_24"].iloc[0] if not row_tot.empty else np.nan

    sintesis = pd.DataFrame([
        {"indicador": "NO2 Dentro ZBE (Caida Bruta)", "unidad": "ug/m3", "valor_previo": round(no2_pre, 2), "valor_post": round(no2_post, 2), "variacion_pct": round(var_no2_dentro, 2)},
        {"indicador": "NO2 Control Fuera ZBE (Gran Bilbao)", "unidad": "ug/m3", "valor_previo": round(fuera_pre, 2), "valor_post": round(fuera_post, 2), "variacion_pct": round(var_no2_fuera, 2)},
        {"indicador": "Impacto Neto ZBE (Diff-in-Diff Atribuible)", "unidad": "ug/m3", "valor_previo": 0.0, "valor_post": round(efecto_neto_did, 2), "variacion_pct": round(var_neta_did_pct, 2)},
        {"indicador": "NO2 Dentro en Calma (Fase 1 vs Pre)", "unidad": "ug/m3", "valor_previo": round(calma_pre, 2), "valor_post": round(calma_f1, 2), "variacion_pct": round(var_no2_calma_f1, 2)},
        {"indicador": "NO2 Dentro en Calma (Post Global vs Pre)", "unidad": "ug/m3", "valor_previo": round(calma_pre, 2), "valor_post": round(calma_post, 2), "variacion_pct": round(var_no2_calma_post, 2)},
        {"indicador": "Trafico San Mames (2023->2024 Inicial)", "unidad": "veh/dia", "valor_previo": traf_sm_23, "valor_post": traf_sm_24, "variacion_pct": traf_sm_var_23_24},
        {"indicador": "Trafico San Mames (2023->2025 Consolidado)", "unidad": "veh/dia", "valor_previo": traf_sm_23, "valor_post": traf_sm_25, "variacion_pct": traf_sm_var_23_25},
        {"indicador": "Trafico San Mames (Rebote 2024->2025)", "unidad": "veh/dia", "valor_previo": traf_sm_24, "valor_post": traf_sm_25, "variacion_pct": traf_sm_var_24_25},
        {"indicador": "Trafico Total Accesos Bilbao (2023->2024)", "unidad": "veh/dia", "valor_previo": row_tot["imd_2023"].iloc[0] if not row_tot.empty else None, "valor_post": row_tot["imd_2024"].iloc[0] if not row_tot.empty else None, "variacion_pct": traf_tot_var},
    ])

    f_sintesis = DIR_UNIFICADOS / "sintesis_ejecutiva_zbe.csv"
    sintesis.to_csv(f_sintesis, index=False)
    print(f"-> Guardada síntesis ejecutiva: {f_sintesis}")

    print("\nSÍNTESIS EJECUTIVA CONSOLIDADA:")
    print(sintesis.to_string(index=False))
    print("\n[OK] Datos unificados con éxito.\n")


if __name__ == "__main__":
    main()
