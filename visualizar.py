#!/usr/bin/env python3
"""
visualizar.py - Visualización multivariable del impacto de la ZBE de Bilbao:
Combina Calidad del Aire (NO2), Tráfico oficial (Aforos Bizkaia) y Meteorología.

Genera:
  - salida/no2_mensual.png: Evolución mensual NO2 (Dentro vs Fuera vs Fondo)
  - salida/informe_multivariable_zbe.png: Dashboard analítico completo de 4 paneles
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

SALIDA = Path("salida")
CSV_AIRE = SALIDA / "aire_limpio.csv"
CSV_TRAF = SALIDA / "trafico_accesos_bilbao.csv"
CSV_METEO_VIENTO = SALIDA / "no2_regimen_viento.csv"

OUT_MENSUAL = SALIDA / "no2_mensual.png"
OUT_DASHBOARD = SALIDA / "informe_multivariable_zbe.png"

FASE1 = pd.Timestamp("2024-06-15")
FASE2 = pd.Timestamp("2025-06-16")
LIMITE = pd.Timestamp("2026-12-31")

COLORES = {
    "dentro": "#FF6B6B",
    "fuera": "#38BDF8",
    "fondo": "#A78BFA",
    "sin_clasificar": "#64748B",
    "fase1": "#FBBF24",
    "fase2": "#F97316",
    "oms": "#34D399",
    "trafico_sm": "#F59E0B",
    "trafico_total": "#94A3B8"
}

def plot_no2_mensual(df):
    """Genera gráfico temporal mensual de NO2 por zona"""
    df["mes"] = df["ts"].dt.to_period("M").dt.to_timestamp()
    mensual = df.groupby(["mes", "zona"])["no2"].mean().reset_index()

    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(14, 6))
    fig.patch.set_facecolor("#0F172A")
    ax.set_facecolor("#1E293B")

    etiquetas = {
        "dentro": "Dentro ZBE (Mazarredo, Mª Díaz de Haro)",
        "fuera": "Control urbano fuera ZBE (Europa, Erandio, Barakaldo...)",
        "fondo": "Fondo regional (Arraiz, Mundaka, Pagoeta...)",
        "sin_clasificar": "Resto estaciones"
    }

    for zona in ["dentro", "fuera", "fondo", "sin_clasificar"]:
        sub = mensual[mensual.zona == zona].sort_values("mes")
        if sub.empty:
            continue
        color = COLORES[zona]
        ax.plot(sub.mes, sub.no2, color=color, linewidth=2.4, marker="o", markersize=4, label=etiquetas[zona], zorder=3)
        ax.fill_between(sub.mes, sub.no2, alpha=0.08, color=color)

    ymax = max(mensual["no2"].max() * 1.15, 45)
    ax.set_ylim(0, ymax)

    for fecha, etiqueta, color_f in [(FASE1, "ZBE Fase 1\n(15 jun 2024)", COLORES["fase1"]),
                                     (FASE2, "ZBE Fase 2\n(16 jun 2025)", COLORES["fase2"])]:
        ax.axvline(fecha, color=color_f, lw=1.5, ls="--", alpha=0.9, zorder=4)
        ax.text(fecha + pd.Timedelta(days=8), ymax * 0.94, etiqueta, color=color_f, fontsize=8.5, va="top", fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.3", fc="#0F172A", ec=color_f, alpha=0.85))

    datos_max = mensual["mes"].max() + pd.offsets.MonthEnd(1)
    if datos_max < LIMITE:
        ax.axvspan(datos_max, LIMITE, color="#334155", alpha=0.35, zorder=1)
        ax.text(datos_max + (LIMITE - datos_max) / 2, ymax * 0.5, "Sin datos aun",
                color="#64748B", fontsize=10, ha="center", va="center", style="italic", fontweight="bold")

    ax.axhline(10, color=COLORES["oms"], lw=1.2, ls=":", alpha=0.85)
    ax.text(pd.Timestamp("2022-02-01"), 11.2, "Limite OMS (10 ug/m3)", color=COLORES["oms"], fontsize=8.5, alpha=0.9, fontweight="bold")

    ax.set_xlim(pd.Timestamp("2022-01-01"), LIMITE)
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
    ax.tick_params(colors="#94A3B8", labelsize=8.5)
    ax.spines[:].set_color("#334155")
    ax.yaxis.grid(True, color="#334155", lw=0.7, alpha=0.6)
    ax.set_axisbelow(True)
    ax.set_ylabel("NO2 medio mensual (ug/m3)", color="#CBD5E1", fontsize=10)
    ax.set_title("Evolucion NO2 por zona - ZBE Bilbao (2022-2026)", color="#F1F5F9", fontsize=14, fontweight="bold", pad=14)
    ax.legend(loc="upper right", fontsize=8.5, facecolor="#1E293B", edgecolor="#334155", labelcolor="#CBD5E1", framealpha=0.9)
    plt.tight_layout(pad=1.5)
    plt.savefig(OUT_MENSUAL, dpi=180, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print(f"-> Grafico temporal mensual guardado: {OUT_MENSUAL}")


def plot_dashboard(df_aire, df_traf):
    """Genera dashboard multivariable integrado de 4 paneles"""
    plt.style.use("dark_background")
    fig, axs = plt.subplots(2, 2, figsize=(18, 12))
    fig.patch.set_facecolor("#0B0F19")
    for ax in axs.flat:
        ax.set_facecolor("#151E2E")
        ax.spines[:].set_color("#2D3748")
        ax.tick_params(colors="#94A3B8", labelsize=9)
        ax.yaxis.grid(True, color="#2D3748", lw=0.6, alpha=0.6)
        ax.set_axisbelow(True)

    # -----------------------------------------------------------
    # Panel 1: Evolución mensual NO2 (Dentro vs Fuera)
    # -----------------------------------------------------------
    ax1 = axs[0, 0]
    df_aire["mes"] = df_aire["ts"].dt.to_period("M").dt.to_timestamp()
    m_no2 = df_aire.groupby(["mes", "zona"])["no2"].mean().unstack("zona")
    
    if "dentro" in m_no2.columns:
        ax1.plot(m_no2.index, m_no2["dentro"], color=COLORES["dentro"], lw=2.4, marker="o", ms=4, label="Dentro ZBE (Mazarredo / Diaz Haro)")
        ax1.fill_between(m_no2.index, m_no2["dentro"], alpha=0.1, color=COLORES["dentro"])
    if "fuera" in m_no2.columns:
        ax1.plot(m_no2.index, m_no2["fuera"], color=COLORES["fuera"], lw=2.2, marker="s", ms=3.5, label="Control Urbano (fuera ZBE)")
    if "fondo" in m_no2.columns:
        ax1.plot(m_no2.index, m_no2["fondo"], color=COLORES["fondo"], lw=1.8, ls="--", label="Fondo regional")

    ax1.axvline(FASE1, color=COLORES["fase1"], lw=1.5, ls="--")
    ax1.text(FASE1 + pd.Timedelta(days=8), 38, "Inicio ZBE\n(Jun 2024)", color=COLORES["fase1"], fontsize=8, fontweight="bold")
    ax1.axhline(10, color=COLORES["oms"], lw=1.2, ls=":")
    ax1.text(pd.Timestamp("2022-02-01"), 10.8, "Limite OMS (10 ug/m3)", color=COLORES["oms"], fontsize=8)
    ax1.set_xlim(pd.Timestamp("2022-01-01"), pd.Timestamp("2026-10-01"))
    ax1.set_ylim(0, 42)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))
    ax1.set_ylabel("NO2 medio (ug/m3)", color="#CBD5E1", fontsize=10)
    ax1.set_title("A. Evolucion Calidad del Aire (NO2) en Bilbao", color="#F8FAFC", fontsize=12, fontweight="bold", pad=10)
    ax1.legend(loc="upper right", fontsize=8.5, facecolor="#151E2E", edgecolor="#2D3748")

    # -----------------------------------------------------------
    # Panel 2: Tráfico en Accesos Oficiales a Bilbao (2018-2025)
    # -----------------------------------------------------------
    ax2 = axs[0, 1]
    years = [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
    cols_imd = [f"imd_{y}" for y in years]
    
    # Extraer San Mamés, Juan de Garai, y Subtotal Sur
    row_sm = df_traf[df_traf.acceso.str.contains("SAN MAMES", case=False, na=False)]
    row_jg = df_traf[df_traf.acceso.str.contains("JUAN DE GARAI", case=False, na=False)]
    row_tot = df_traf[df_traf.acceso.str.contains("TOTAL", case=False, na=False)]

    if not row_sm.empty:
        vals_sm = [row_sm[c].iloc[0] / 1000 for c in cols_imd]
        ax2.plot(years, vals_sm, color="#F59E0B", lw=2.6, marker="o", ms=6, label="Acceso San Mames (Entrada ZBE)")
        # Anotación caída ZBE
        ax2.annotate("-10.1% ZBE", xy=(2024, vals_sm[6]), xytext=(2023.2, vals_sm[6] - 4),
                     arrowprops=dict(arrowstyle="->", color="#EF4444", lw=1.5),
                     color="#EF4444", fontsize=9, fontweight="bold")
    
    if not row_jg.empty:
        vals_jg = [row_jg[c].iloc[0] / 1000 for c in cols_imd]
        ax2.plot(years, vals_jg, color="#38BDF8", lw=2.0, marker="s", ms=5, label="Zabalburu / Juan de Garai")

    ax2.axvline(2024.45, color=COLORES["fase1"], lw=1.5, ls="--")
    ax2.text(2024.5, 52, "ZBE Fase 1\n(Junio 2024)", color=COLORES["fase1"], fontsize=8, fontweight="bold")
    ax2.set_xticks(years)
    ax2.set_xticklabels(years)
    ax2.set_ylabel("Intensidad Media Diaria (miles veh/dia)", color="#CBD5E1", fontsize=10)
    ax2.set_title("B. Trafico en Accesos a Bilbao (Diputacion Foral Bizkaia)", color="#F8FAFC", fontsize=12, fontweight="bold", pad=10)
    ax2.legend(loc="upper left", fontsize=8.5, facecolor="#151E2E", edgecolor="#2D3748")

    # -----------------------------------------------------------
    # Panel 3: NO2 según Régimen de Viento (Control Meteorológico)
    # -----------------------------------------------------------
    ax3 = axs[1, 0]
    if CSV_METEO_VIENTO.exists():
        df_viento = pd.read_csv(CSV_METEO_VIENTO)
        # Formato: periodo, regimen_viento, dentro, fuera
        regimenes = ["Calma (<2 m/s)", "Moderado (2-5 m/s)", "Fuerte (>5 m/s)"]
        x = np.arange(len(regimenes))
        w = 0.35

        p_pre = df_viento[df_viento.periodo == "Pre-ZBE"]
        p_post = df_viento[df_viento.periodo == "Post-ZBE"]

        v_pre = [p_pre[p_pre.regimen_viento == r]["dentro"].values[0] if len(p_pre[p_pre.regimen_viento == r]) else 0 for r in regimenes]
        v_post = [p_post[p_post.regimen_viento == r]["dentro"].values[0] if len(p_post[p_post.regimen_viento == r]) else 0 for r in regimenes]

        b1 = ax3.bar(x - w/2, v_pre, width=w, label="Pre-ZBE (Dentro)", color="#64748B", alpha=0.85)
        b2 = ax3.bar(x + w/2, v_post, width=w, label="Post-ZBE (Dentro)", color=COLORES["dentro"], alpha=0.9)

        # Anotaciones de porcentaje
        for i in range(len(regimenes)):
            diff = v_post[i] - v_pre[i]
            pct = (diff / v_pre[i]) * 100
            ax3.text(x[i] + w/2, v_post[i] + 0.8, f"{pct:.1f}%", ha="center", color="#FCA5A5", fontsize=8.5, fontweight="bold")

        ax3.set_xticks(x)
        ax3.set_xticklabels(regimenes)
        ax3.set_ylabel("NO2 medio (ug/m3)", color="#CBD5E1", fontsize=10)
        ax3.set_title("C. Desestacionalizacion Meteo: NO2 por Regimen de Viento", color="#F8FAFC", fontsize=12, fontweight="bold", pad=10)
        ax3.legend(loc="upper right", fontsize=8.5, facecolor="#151E2E", edgecolor="#2D3748")
    else:
        ax3.text(0.5, 0.5, "Ejecuta analisis.py para generar no2_regimen_viento.csv", ha="center", va="center", color="#94A3B8")

    # -----------------------------------------------------------
    # Panel 4: Síntesis de Impacto Multivariable ZBE (%)
    # -----------------------------------------------------------
    ax4 = axs[1, 1]
    metricas = [
        "Trafico Acceso\nSan Mames (ZBE)",
        "Trafico Total\nAccesos Bilbao",
        "NO2 Dentro ZBE\n(Absoluto)",
        "NO2 Dentro ZBE\n(En Calma Meteo)",
        "NO2 Control Fuera\n(Ext. ZBE)",
        "Diferencia Neta\n(Dentro vs Fuera)"
    ]
    # Valores observados calculados
    valores = [
        -10.12,  # Trafico San Mames 2023->2024
        -0.68,   # Trafico Total Bilbao 2023->2024
        -14.57,  # NO2 dentro 25.62 -> 21.89
        -17.14,  # NO2 calma dentro 32.32 -> 26.78
        -13.86,  # NO2 fuera 15.92 -> 13.71
        -1.59    # Cambio dif mensual dentro - fuera (ug/m3) -> normalizado
    ]
    colores_barras = ["#F59E0B", "#94A3B8", "#FF6B6B", "#EF4444", "#38BDF8", "#10B981"]

    y_pos = np.arange(len(metricas))
    bars = ax4.barh(y_pos, valores, color=colores_barras, height=0.55, alpha=0.9)
    ax4.axvline(0, color="#94A3B8", lw=1.0)

    for bar, val in zip(bars, valores):
        unidad = "%" if bar != bars[-1] else " ug/m3"
        x_text = val - 0.4 if val < 0 else val + 0.4
        ha = "right" if val < 0 else "left"
        ax4.text(x_text, bar.get_y() + bar.get_height()/2, f"{val:+.1f}{unidad}",
                 va="center", ha=ha, color="#F8FAFC", fontsize=9, fontweight="bold")

    ax4.set_yticks(y_pos)
    ax4.set_yticklabels(metricas, color="#CBD5E1", fontsize=9)
    ax4.set_xlabel("Variacion tras inicio ZBE (%)", color="#CBD5E1", fontsize=10)
    ax4.set_title("D. Resumen Ejecutivo Multivariable del Impacto ZBE", color="#F8FAFC", fontsize=12, fontweight="bold", pad=10)
    ax4.set_xlim(-22, 5)

    plt.suptitle("INFORME INTEGRADO ZBE BILBAO (2022-2026)\nCalidad del Aire (NO2) + Aforos Oficiales de Trafico + Control Meteorologico",
                 color="#F8FAFC", fontsize=15, fontweight="bold", y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.95], pad=2.0)
    plt.savefig(OUT_DASHBOARD, dpi=180, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print(f"-> Dashboard multivariable guardado: {OUT_DASHBOARD}")


def main():
    if not CSV_AIRE.exists():
        print(f"ERROR: No se encuentra {CSV_AIRE}. Ejecuta primero: python analisis.py")
        return

    print("Cargando datos para visualizacion...")
    df_aire = pd.read_csv(CSV_AIRE, parse_dates=["ts"])
    
    # 1. Gráfico temporal mensual
    plot_no2_mensual(df_aire)
    
    # 2. Dashboard si existe tráfico
    if CSV_TRAF.exists():
        df_traf = pd.read_csv(CSV_TRAF)
        plot_dashboard(df_aire, df_traf)
    else:
        print("[!] No se encontro salida/trafico_accesos_bilbao.csv para generar el dashboard completo.")

if __name__ == "__main__":
    main()
