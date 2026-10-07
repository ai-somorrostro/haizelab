#!/usr/bin/env python3
"""
scripts/06_visualizar_decision.py
=================================

OBJETIVO:
  Generar las visualizaciones ejecutivas esenciales para responder con rigor
  a la pregunta estratégica: ¿AVANZAMOS CON ESTE PROYECTO O NO?

ENTRADA:
  - datos/procesados/unificados/dataset_unificado_horario.csv
  - datos/procesados/trafico/trafico_accesos_bilbao.csv
  - datos/procesados/unificados/analisis_estratificado_viento.csv

SALIDA (carpeta salida/):
  - salida/dashboard_decision_zbe.png:
      Dashboard integral de 4 paneles con las 3 pruebas causales (Aire, Tráfico, Clima)
      y el cuadro de mando para la toma de decisión.
  - salida/evolucion_mensual_no2.png:
      Serie temporal mensual detallada por zona (2022-2026).
"""

from pathlib import Path
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

DIR_BASE = Path(__file__).resolve().parent.parent
DIR_UNIFICADOS = DIR_BASE / "datos" / "procesados" / "unificados"
DIR_TRAFICO = DIR_BASE / "datos" / "procesados" / "trafico"
DIR_SALIDA = DIR_BASE / "salida"

FASE1 = pd.Timestamp("2024-06-15")
FASE2 = pd.Timestamp("2025-06-16")
LIMITE = pd.Timestamp("2026-10-01")

# Paleta premium de diseño (Dark Mode)
C_DENTRO = "#FF6B6B"       # Coral/Rojo ZBE
C_FUERA = "#38BDF8"        # Cyan Control Exterior
C_FONDO = "#A78BFA"        # Púrpura Fondo regional
C_TRAFICO = "#F59E0B"      # Ámbar Tráfico San Mamés
C_OMS = "#34D399"          # Verde esmeralda OMS
C_FASE1 = "#FBBF24"        # Amarillo Hito ZBE
C_BG = "#0B0F19"           # Fondo exterior oscuro
C_PANEL = "#151E2E"        # Fondo panel
C_GRID = "#2D3748"         # Rejilla


def plot_dashboard_decision(df_uni: pd.DataFrame, df_traf: pd.DataFrame):
    """Genera el dashboard de decisión ejecutiva de 4 cuadrantes."""
    plt.style.use("dark_background")
    fig, axs = plt.subplots(2, 2, figsize=(18, 12))
    fig.patch.set_facecolor(C_BG)

    for ax in axs.flat:
        ax.set_facecolor(C_PANEL)
        ax.spines[:].set_color(C_GRID)
        ax.tick_params(colors="#94A3B8", labelsize=9)
        ax.yaxis.grid(True, color=C_GRID, lw=0.6, alpha=0.6)
        ax.set_axisbelow(True)

    # -----------------------------------------------------------
    # Panel 1: Prueba de Calidad del Aire (Evolución NO2)
    # -----------------------------------------------------------
    ax1 = axs[0, 0]
    df_uni["mes"] = df_uni["ts"].dt.to_period("M").dt.to_timestamp()
    m_no2 = df_uni.groupby("mes")[["no2_dentro", "no2_fuera", "no2_fondo"]].mean()

    ax1.plot(m_no2.index, m_no2["no2_dentro"], color=C_DENTRO, lw=2.5, marker="o", ms=4, label="Dentro ZBE (Mazarredo / Díaz Haro)")
    ax1.fill_between(m_no2.index, m_no2["no2_dentro"], alpha=0.10, color=C_DENTRO)
    ax1.plot(m_no2.index, m_no2["no2_dentro"], color=C_DENTRO, lw=2.5, marker="o", ms=4, label="Dentro ZBE (Mazarredo / Díaz Haro)")
    ax1.fill_between(m_no2.index, m_no2["no2_dentro"], alpha=0.10, color=C_DENTRO)
    ax1.plot(m_no2.index, m_no2["no2_fuera"], color=C_FUERA, lw=2.0, marker="s", ms=3.5, label="Control Urbano Exterior (5 est. Gran Bilbao)")
    if "no2_fondo" in m_no2.columns:
        ax1.plot(m_no2.index, m_no2["no2_fondo"], color=C_FONDO, lw=1.6, ls="--", label="Fondo regional (Monte Arraiz)")

    ax1.axvline(FASE1, color=C_FASE1, lw=1.5, ls="--")
    ax1.text(FASE1 + pd.Timedelta(days=8), 38, "Inicio ZBE\n(Junio 2024)", color=C_FASE1, fontsize=8.5, fontweight="bold")
    ax1.axhline(10, color=C_OMS, lw=1.2, ls=":")
    ax1.text(pd.Timestamp("2022-02-01"), 10.8, "Objetivo OMS (10 ug/m3)", color=C_OMS, fontsize=8)

    ax1.set_xlim(pd.Timestamp("2022-01-01"), LIMITE)
    ax1.set_ylim(0, 42)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))
    ax1.set_ylabel("NO2 medio mensual (ug/m3)", color="#CBD5E1", fontsize=10)
    ax1.set_title("1. CALIDAD DEL AIRE: Evolucion de NO2 en Bilbao (2022-2026)", color="#F8FAFC", fontsize=11, fontweight="bold", pad=10)
    ax1.legend(loc="upper right", fontsize=8.5, facecolor=C_PANEL, edgecolor=C_GRID)

    # -----------------------------------------------------------
    # Panel 2: Prueba de Tráfico (Intensidad en San Mamés)
    # -----------------------------------------------------------
    ax2 = axs[0, 1]
    years = [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
    cols_imd = [f"imd_{y}" for y in years]

    row_sm = df_traf[df_traf.acceso.str.contains("SAN MAMES", case=False, na=False)]
    row_jg = df_traf[df_traf.acceso.str.contains("JUAN DE GARAI", case=False, na=False)]

    if not row_sm.empty:
        vals_sm = [row_sm[c].iloc[0] / 1000 for c in cols_imd]
        ax2.plot(years, vals_sm, color=C_TRAFICO, lw=2.6, marker="o", ms=6, label="Acceso San Mames (Entrada ZBE)")
        ax2.annotate("-10.1% (2024)", xy=(2024, vals_sm[6]), xytext=(2023.1, vals_sm[6] - 4.5),
                     arrowprops=dict(arrowstyle="->", color="#EF4444", lw=1.5),
                     color="#EF4444", fontsize=8.5, fontweight="bold")
        ax2.annotate("Rebote: 48.5k\n(-3.2% vs 2023)", xy=(2025, vals_sm[7]), xytext=(2024.1, vals_sm[7] + 2.0),
                     arrowprops=dict(arrowstyle="->", color="#FBBF24", lw=1.5),
                     color="#FBBF24", fontsize=8.5, fontweight="bold")

    if not row_jg.empty:
        vals_jg = [row_jg[c].iloc[0] / 1000 for c in cols_imd]
        ax2.plot(years, vals_jg, color=C_FUERA, lw=2.0, marker="s", ms=5, label="Zabalburu / Juan de Garai")

    ax2.axvline(2024.45, color=C_FASE1, lw=1.5, ls="--")
    ax2.text(2024.5, 52, "ZBE Fase 1\n(Junio 2024)", color=C_FASE1, fontsize=8.5, fontweight="bold")
    ax2.set_xticks(years)
    ax2.set_xticklabels(years)
    ax2.set_ylabel("Intensidad Media Diaria (miles veh/dia)", color="#CBD5E1", fontsize=10)
    ax2.set_title("2. TRÁFICO: Aforos de Acceso al Centro (Diputacion Foral Bizkaia)", color="#F8FAFC", fontsize=11, fontweight="bold", pad=10)
    ax2.legend(loc="upper left", fontsize=8.5, facecolor=C_PANEL, edgecolor=C_GRID)

    # -----------------------------------------------------------
    # Panel 3: Prueba Climática (Control por Viento)
    # -----------------------------------------------------------
    ax3 = axs[1, 0]
    regimenes = ["Calma (<2 m/s)", "Moderado (2-5 m/s)", "Fuerte (>5 m/s)"]
    x = np.arange(len(regimenes))
    w = 0.35

    df_pre = df_uni[df_uni.periodo == "previo"]
    df_post = df_uni[df_uni.periodo.isin(["fase1", "fase2"])]

    v_pre = [df_pre[df_pre.regimen_viento == r]["no2_dentro"].mean() for r in regimenes]
    v_post = [df_post[df_post.regimen_viento == r]["no2_dentro"].mean() for r in regimenes]

    ax3.bar(x - w/2, v_pre, width=w, label="Pre-ZBE (Dentro)", color="#64748B", alpha=0.85)
    ax3.bar(x + w/2, v_post, width=w, label="Post-ZBE (Dentro)", color=C_DENTRO, alpha=0.9)

    for i in range(len(regimenes)):
        diff = v_post[i] - v_pre[i]
        pct = (diff / v_pre[i]) * 100
        ax3.text(x[i] + w/2, v_post[i] + 0.8, f"{pct:.1f}%", ha="center", color="#FCA5A5", fontsize=8.5, fontweight="bold")

    ax3.set_xticks(x)
    ax3.set_xticklabels(regimenes)
    ax3.set_ylabel("NO2 medio (ug/m3)", color="#CBD5E1", fontsize=10)
    ax3.set_title("3. CONTROL METEOROLÓGICO: NO2 por Regimen de Viento (Monte Banderas)", color="#F8FAFC", fontsize=11, fontweight="bold", pad=10)
    ax3.legend(loc="upper right", fontsize=8.5, facecolor=C_PANEL, edgecolor=C_GRID)

    # -----------------------------------------------------------
    # Panel 4: Resumen y Veredicto para la Toma de Decisión
    # -----------------------------------------------------------
    ax4 = axs[1, 1]

    # Cálculos dinámicos
    caida_bruta_dentro = ((df_post["no2_dentro"].mean() - df_pre["no2_dentro"].mean()) / df_pre["no2_dentro"].mean()) * 100
    caida_bruta_fuera = ((df_post["no2_fuera"].mean() - df_pre["no2_fuera"].mean()) / df_pre["no2_fuera"].mean()) * 100
    efecto_did_neto = ((df_post["no2_dentro"].mean() - df_pre["no2_dentro"].mean()) - (df_post["no2_fuera"].mean() - df_pre["no2_fuera"].mean())) / df_pre["no2_dentro"].mean() * 100
    caida_calma = ((v_post[0] - v_pre[0]) / v_pre[0]) * 100

    metricas = [
        "Trafico S. Mames '24\n(Disuasion inicial)",
        "Trafico S. Mames '25\n(Rebote consolidado)",
        "NO2 Dentro Calma\n(<2 m/s viento)",
        "NO2 Dentro ZBE\n(Caida bruta antes/despues)",
        "Control Gran Bilbao\n(Tendencia exterior)",
        "Efecto Neto ZBE\n(Diff-in-Diff atribuible)"
    ]
    valores = [-10.12, -3.16, caida_calma, caida_bruta_dentro, caida_bruta_fuera, efecto_did_neto]
    colores_b = [C_TRAFICO, "#FBBF24", "#EF4444", C_DENTRO, C_FUERA, "#10B981"]

    y_pos = np.arange(len(metricas))
    bars = ax4.barh(y_pos, valores, color=colores_b, height=0.52, alpha=0.9)
    ax4.axvline(0, color="#94A3B8", lw=1.0)

    for bar, val in zip(bars, valores):
        ax4.text(val - 0.4, bar.get_y() + bar.get_height()/2, f"{val:+.1f}%",
                 va="center", ha="right", color="#F8FAFC", fontsize=9.0, fontweight="bold")

    ax4.set_yticks(y_pos)
    ax4.set_yticklabels(metricas, color="#CBD5E1", fontsize=8.5)
    ax4.set_xlabel("Variacion tras implantacion de la ZBE (%)", color="#CBD5E1", fontsize=10)
    ax4.set_title("4. RESUMEN EJECUTIVO: Variaciones Porcentuales Reales", color="#F8FAFC", fontsize=11, fontweight="bold", pad=10)
    ax4.set_xlim(-22, 5)

    # Veredicto de decisión institucional honesto
    ax4.text(-21, -0.9, "VEREDICTO: EFECTO CONFIRMADO PERO MODERADO\nEfecto neto ZBE atribuible: -7.1% (-1.8 ug/m3). Disuasion inicial de trafico (-10.1% en 2024)\namortiguada en 2025 (-3.2% vs 2023). El impacto se sostiene bajo 5 limitaciones metodologicas.",
             fontsize=8.0, color="#38BDF8", fontweight="bold",
             bbox=dict(boxstyle="round,pad=0.4", fc="#082F49", ec="#38BDF8", alpha=0.9))

    plt.suptitle("PANEL DE DECISIÓN ESTRATÉGICA — EVALUACIÓN DEL IMPACTO DE LA ZBE DE BILBAO\n¿Debemos avanzar con el proyecto? Datos oficiales de Calidad del Aire (Euskadi) + Tráfico (Bizkaia) + Clima (Banderas)",
                 color="#F8FAFC", fontsize=14, fontweight="bold", y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.95], pad=2.0)

    f_out = DIR_SALIDA / "dashboard_decision_zbe.png"
    plt.savefig(f_out, dpi=200, facecolor=C_BG)
    plt.close()
    print(f"-> Guardado dashboard de decisión: {f_out}")

    # Guardar copia directa en docs/img para informes y markdown
    f_docs_img = DIR_BASE / "docs" / "img" / "dashboard_decision_v1.png"
    import shutil
    shutil.copy2(f_out, f_docs_img)
    print(f"-> Copiado dashboard a docs/img: {f_docs_img}")


def plot_evolucion_no2(df_uni: pd.DataFrame):
    """Genera la serie temporal mensual estilizada de NO2."""
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(14, 6))
    fig.patch.set_facecolor(C_BG)
    ax.set_facecolor(C_PANEL)

    df_uni["mes"] = df_uni["ts"].dt.to_period("M").dt.to_timestamp()
    m = df_uni.groupby("mes")[["no2_dentro", "no2_fuera", "no2_fondo"]].mean()

    ax.plot(m.index, m["no2_dentro"], color=C_DENTRO, lw=2.4, marker="o", ms=4, label="Dentro ZBE (Mazarredo / Díaz Haro)")
    ax.fill_between(m.index, m["no2_dentro"], alpha=0.1, color=C_DENTRO)
    ax.plot(m.index, m["no2_fuera"], color=C_FUERA, lw=2.2, marker="s", ms=3.5, label="Control Urbano Fuera ZBE (Gran Bilbao)")
    if "no2_fondo" in m.columns:
        ax.plot(m.index, m["no2_fondo"], color=C_FONDO, lw=1.8, ls="--", label="Fondo Regional (Arraiz / Mundaka)")

    ymax = max(m["no2_dentro"].max() * 1.15, 42)
    ax.set_ylim(0, ymax)

    for fecha, etiqueta, color_f in [(FASE1, "ZBE Fase 1\n(15 jun 2024)", C_FASE1),
                                     (FASE2, "ZBE Fase 2\n(16 jun 2025)", "#F97316")]:
        ax.axvline(fecha, color=color_f, lw=1.5, ls="--", alpha=0.9)
        ax.text(fecha + pd.Timedelta(days=8), ymax * 0.94, etiqueta, color=color_f, fontsize=8.5, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.3", fc=C_BG, ec=color_f, alpha=0.85))

    ax.axhline(10, color=C_OMS, lw=1.2, ls=":", alpha=0.85)
    ax.text(pd.Timestamp("2022-02-01"), 10.8, "Limite OMS (10 ug/m3)", color=C_OMS, fontsize=8.5, fontweight="bold")

    ax.set_xlim(pd.Timestamp("2022-01-01"), LIMITE)
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
    ax.tick_params(colors="#94A3B8", labelsize=8.5)
    ax.spines[:].set_color(C_GRID)
    ax.yaxis.grid(True, color=C_GRID, lw=0.7, alpha=0.6)
    ax.set_axisbelow(True)
    ax.set_ylabel("NO2 medio mensual (ug/m3)", color="#CBD5E1", fontsize=10)
    ax.set_title("Evolucion Temporal de NO2 por Zona — ZBE Bilbao (2022–2026)", color="#F1F5F9", fontsize=13, fontweight="bold", pad=12)
    ax.legend(loc="upper right", fontsize=8.5, facecolor=C_PANEL, edgecolor=C_GRID, labelcolor="#CBD5E1")

    plt.tight_layout(pad=1.5)
    f_out = DIR_SALIDA / "evolucion_mensual_no2.png"
    plt.savefig(f_out, dpi=180, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print(f"-> Gráfico mensual guardado: {f_out}")


def main():
    print("=" * 70)
    print("6. GENERACIÓN DE VISUALIZACIONES PARA LA TOMA DE DECISIÓN")
    print("=" * 70)

    DIR_SALIDA.mkdir(parents=True, exist_ok=True)
    f_uni = DIR_UNIFICADOS / "dataset_unificado_horario.csv"
    f_traf = DIR_TRAFICO / "trafico_accesos_bilbao.csv"

    if not f_uni.exists() or not f_traf.exists():
        sys.exit("ERROR: Faltan archivos unificados. Ejecuta antes 04_unificar_datos.py.")

    print("Cargando datos para visualización...")
    df_uni = pd.read_csv(f_uni, parse_dates=["ts"])
    df_traf = pd.read_csv(f_traf)

    # 1. Gráfico temporal mensual de NO2
    plot_evolucion_no2(df_uni)

    # 2. Dashboard de decisión estratégica (4 paneles)
    plot_dashboard_decision(df_uni, df_traf)

    print("\n[OK] Todas las visualizaciones se han generado con éxito en ./salida/\n")


if __name__ == "__main__":
    main()
