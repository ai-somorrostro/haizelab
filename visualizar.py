import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path

CSV   = Path("salida/aire_limpio.csv")
OUT   = Path("salida/no2_mensual_2022_2026.png")
FASE1 = pd.Timestamp("2024-06-15")
FASE2 = pd.Timestamp("2025-06-16")
LIMITE = pd.Timestamp("2026-12-31")

COLORES = {"dentro":"#FF6B6B","fuera":"#4ECDC4","fondo":"#A78BFA","sin_clasificar":"#94A3B8"}
ETIQUETAS = {"dentro":"Dentro ZBE","fuera":"Control (fuera)","fondo":"Fondo regional","sin_clasificar":"Resto estaciones"}

df = pd.read_csv(CSV, parse_dates=["ts"])
df["mes"] = df["ts"].dt.to_period("M").dt.to_timestamp()
mensual = df.groupby(["mes","zona"])["no2"].mean().reset_index()

plt.style.use("dark_background")
fig, ax = plt.subplots(figsize=(14,6))
fig.patch.set_facecolor("#0F172A")
ax.set_facecolor("#1E293B")

for zona in ["dentro","fuera","fondo","sin_clasificar"]:
    sub = mensual[mensual.zona==zona].sort_values("mes")
    if sub.empty: continue
    color = COLORES[zona]
    ax.plot(sub.mes, sub.no2, color=color, linewidth=2.2, marker="o", markersize=4, label=ETIQUETAS[zona], zorder=3)
    ax.fill_between(sub.mes, sub.no2, alpha=0.08, color=color)

ymax = mensual["no2"].max() * 1.15
ax.set_ylim(0, ymax)

for fecha, etiqueta, color_f in [(FASE1,"ZBE Fase 1\n(jun 2024)","#FCD34D"),(FASE2,"ZBE Fase 2\n(jun 2025)","#FB923C")]:
    ax.axvline(fecha, color=color_f, lw=1.4, ls="--", alpha=0.85, zorder=4)
    ax.text(fecha+pd.Timedelta(days=8), ymax*0.96, etiqueta, color=color_f, fontsize=8.5, va="top", fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", fc="#0F172A", ec=color_f, alpha=0.8))

datos_max = mensual["mes"].max() + pd.offsets.MonthEnd(1)
if datos_max < LIMITE:
    ax.axvspan(datos_max, LIMITE, color="#334155", alpha=0.4, zorder=1)
    ax.text(datos_max+(LIMITE-datos_max)/2, ymax*0.5, "Sin datos aun",
            color="#64748B", fontsize=10, ha="center", va="center", style="italic", fontweight="bold")

ax.axhline(10, color="#34D399", lw=1, ls=":", alpha=0.7)
ax.text(pd.Timestamp("2022-02-01"), 10.5, u"Limite OMS (10 \u00b5g/m\u00b3)", color="#34D399", fontsize=8, alpha=0.85)

ax.set_xlim(pd.Timestamp("2022-01-01"), LIMITE)
ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1,4,7,10]))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
ax.tick_params(colors="#94A3B8", labelsize=8.5)
ax.spines[:].set_color("#334155")
ax.yaxis.grid(True, color="#334155", lw=0.7, alpha=0.6)
ax.set_axisbelow(True)
ax.set_ylabel(u"NO\u2082 medio mensual (\u00b5g/m\u00b3)", color="#CBD5E1", fontsize=10)
ax.set_title(u"Evoluci\u00f3n NO\u2082 por zona \u2014 ZBE Bilbao (2022\u20132026)",
             color="#F1F5F9", fontsize=14, fontweight="bold", pad=14)
ax.legend(loc="upper right", fontsize=9, facecolor="#1E293B", edgecolor="#334155", labelcolor="#CBD5E1", framealpha=0.9)
plt.tight_layout(pad=1.5)
plt.savefig(OUT, dpi=180, bbox_inches="tight", facecolor=fig.get_facecolor())
print("Guardado en", OUT)
