"""
Genera el informe para el Ayuntamiento a partir de resultados/resultados.json:
  - docs/informe-cliente-sbd.md
  - docs/Informe_Ejecutivo_ZBE_Bilbao_HaizeLab.docx y .pdf (con Microsoft Word, solo en Windows)

Todas las cifras salen de resultados.json; ninguna se escribe a mano.
Uso (desde la raíz del repo):  python docs/generar_informe.py
Para generar solo el Markdown (sin Word):  python docs/generar_informe.py --solo-md
"""
import html
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

DIR_DOCS = Path(__file__).resolve().parent
DIR_RAIZ = DIR_DOCS.parent
R = json.loads((DIR_RAIZ / "resultados" / "resultados.json").read_text(encoding="utf-8"))
NOMBRE = "Informe_Ejecutivo_ZBE_Bilbao_HaizeLab"


def es(x, dec=2, signo=False):
    """Número en formato español: coma decimal, punto de miles y signo menos tipográfico."""
    texto = f"{x:+,.{dec}f}" if signo else f"{x:,.{dec}f}"
    return texto.replace(",", "_").replace(".", ",").replace("_", ".").replace("-", "−")


def fecha(iso):
    a, m, d = iso.split("-")
    return f"{d}/{m}/{a}"


def intervalo(inf, sup):
    return f"intervalo de {es(inf)} a {es(sup)}"


# ---------------------------------------------------------------------------
# Cifras que se usan en el texto
per = R["periodo_estudio"]
cal, vie, integ = R["calidad_datos"], R["viento"], R["integracion"]
p1, p2, p3, p4, p5 = R["p1_did"], R["p2_horario"], R["p3_calma"], R["p4_so2"], R["p5_fases"]
est, anual = R["estaciones_no2"], R["medias_anuales_no2"]
f1, f2 = p5["fase1_vs_previo"], p5["fase2_vs_fase1"]

completitud = cal["completitud_no2_por_estacion_pct"]
peor, mejor = min(completitud, key=completitud.get), max(completitud, key=completitud.get)
control_min = min((e for e in est if est[e]["zona"] == "fuera"), key=lambda e: est[e]["var_post_vs_previo_pct"])
n_dentro = sum(e["zona"] == "dentro" for e in est.values())
n_fuera = sum(e["zona"] == "fuera" for e in est.values())
cambio_previo_dentro = anual["dentro"]["2023"] - anual["dentro"]["2022"]
cambio_previo_fuera = anual["fuera"]["2023"] - anual["fuera"]["2022"]

# Las frases del informe dependen del signo de estas cifras. Si los datos cambian y dejan de
# cumplirse, el script se para en vez de escribir una conclusión que ya no es cierta.
assert p1["ic95_sup"] < 0, "P1: el intervalo ya no está por debajo de cero; revisar el texto"
assert p2["efecto_neto_en_horario_zbe"] < p2["efecto_neto_fuera_horario"], "P2: revisar el texto"
assert p3["ic95_sup"] < 0, "P3: revisar el texto"
assert p4["ic95_inf"] <= 0 <= p4["ic95_sup"], "P4: el SO2 ya se distingue de cero; revisar el texto"
assert f2["ic95_inf"] <= 0 <= f2["ic95_sup"], "P5: la fase 2 ya se distingue de cero; revisar el texto"
assert est[control_min]["var_post_vs_previo_pct"] < min(e["var_post_vs_previo_pct"] for e in est.values() if e["zona"] == "dentro")

# ---------------------------------------------------------------------------
# Contenido: lista de bloques que se escriben igual en Markdown y en Word
portada = {
    "titulo": "¿Ha reducido la ZBE de Bilbao el NO₂?",
    "subtitulo": "Datos para decidir si ampliar, mantener o ajustar la Zona de Bajas Emisiones",
    "filas": [
        ("Cliente", "Ayuntamiento de Bilbao"),
        ("Equipo", "HaizeLab: Alfred Gabriel, Iñigo Guzmán y Kerman Latorre"),
        ("Periodo analizado", f"{fecha(per['fecha_inicio'])} – {fecha(per['fecha_fin'])}"),
        ("Fecha", "Octubre de 2026"),
    ],
}

B = []
h = lambda t: B.append(("h", t))
p = lambda t: B.append(("p", t))
ul = lambda *items: B.append(("ul", list(items)))
tabla = lambda cab, filas, anchos: B.append(("tabla", cab, filas, anchos))
img = lambda ruta, pie, cm: B.append(("img", ruta, pie, cm))

h("1. Problema y decisión del cliente")
p(f"La ZBE de Bilbao restringe la entrada de vehículos de lunes a viernes laborables, de 7:00 a 20:00: desde el "
  f"{fecha(per['fecha_fase1'])} (**fase 1**), a los vehículos sin etiqueta ambiental, y desde el {fecha(per['fecha_fase2'])} "
  "(**fase 2**), también a los de etiqueta B de no residentes. El Ayuntamiento tiene que decidir si **amplía, mantiene o ajusta** "
  "la ZBE. Para ello necesita saber cuánto ha bajado el **NO₂** (dióxido de nitrógeno, un gas que sale sobre todo de los tubos "
  "de escape) por la ZBE y cuánto habría bajado igualmente por el tiempo atmosférico o por la sustitución normal de coches "
  "viejos por otros más limpios, que ocurre con o sin ZBE.")

h("2. Preguntas y prioridad")
p("**Criterio:** cuánto cambia la respuesta la decisión. **Alta:** por sí sola puede cambiar la decisión. "
  "**Media:** comprueba una respuesta de prioridad alta.")
tabla(["", "Pregunta", "Prioridad", "Por qué"], [
    ["P1", "¿Bajó el NO₂ dentro de la ZBE más que fuera?", "Alta", "Si no bajó más dentro, no hay motivo para mantenerla ni ampliarla."],
    ["P2", "¿La bajada se concentra en el horario de la ZBE?", "Alta", "Dice si el horario actual está bien elegido."],
    ["P3", "¿Se mantiene en las horas de viento en calma?", "Media", "Comprueba que P1 no se debe a que hiciera más viento."],
    ["P4", "¿Baja también el SO₂, que no viene del tráfico?", "Media", "Si bajara igual, P1 podría tener otra causa."],
    ["P5", "¿Qué aportó la fase 2 respecto a la fase 1?", "Alta", "Dice si endurecer las restricciones ha servido."],
], [1, 7, 2, 8])

h("3. Datos: fuentes, tipos y calidad")
tabla(["Fuente", "Quién la publica", "Formato y frecuencia", "Variables usadas", "Pregunta"], [
    ["Calidad del aire", "Gobierno Vasco (Open Data Euskadi)", "CSV; datos horarios por estación, según los propios ficheros descargados", "NO₂ y SO₂ (µg/m³), 8 estaciones", "P1-P5"],
    ["Meteorología", "Open-Meteo (modelo meteorológico, no una estación)", "JSON de una API; horaria", "Velocidad del viento", "P3"],
    ["Calendario", "Elaboración propia: fases de la ZBE y lista de festivos de Bilbao escrita en ingesta/descargar_y_limpiar.py (no contrastada con un calendario oficial)", "CSV; diaria", "Laborable, fase de la ZBE", "P2, P5"],
], [3, 5, 5, 3, 2])
p("**Tipos de datos.** Cada fila es una estación en una hora, con datos numéricos (NO₂, SO₂, viento), categóricos (estación, "
  "grupo, fase), lógicos (laborable, en horario ZBE) y de fecha y hora.")
ul(
    f"**Filas:** {es(cal['filas_crudas'], 0)} crudas, sin fechas no válidas ni repetidas. Se estudian {es(cal['filas_en_periodo'], 0)}, "
    f"hasta el {fecha(per['fecha_fin'])}, para que las cifras no cambien cuando se publican datos nuevos (Grafana puede mostrar datos posteriores).",
    f"**Formato:** {es(cal['celdas_coma_decimal_corregidas'], 0)} celdas con coma decimal y {es(cal['filas_hora_24_corregidas'], 0)} filas con hora "
    "24:00 (pasa a las 00:00 del día siguiente).",
    f"**Negativos:** {cal['no2_negativos_a_nan']} valores de NO₂ ({es(cal['no2_negativos_pct'], 3)} %) pasan a **NaN** (celda vacía). "
    "Un 0 bajaría la media sin motivo y borrar la fila perdería los demás datos de esa hora.",
    f"**Unidades y hora:** el viento llega en {vie['unidad_crudo']} (media {es(vie['media_crudo_kmh'])}) y se pasa a m/s dividiendo entre "
    f"3,6 (media {es(vie['media_limpio_ms'])}). La hora llega en GMT y se pasa a la de Madrid, que es la del horario de la ZBE.",
    f"**Completitud** = horas con dato válido de NO₂ ÷ horas que debería haber: {es(cal['completitud_no2_total_pct'])} % en total, "
    f"de {es(completitud[peor])} % ({peor}) a {es(completitud[mejor])} % ({mejor}). Meteorología: {es(cal['completitud_meteo_pct'], 0)} %.",
    f"**Integración:** a cada medición se le une el calendario (por fecha) y el viento (por hora): {es(integ['filas_antes_join'], 0)} filas antes "
    f"y {es(integ['filas_integradas'], 0)} después, {integ['duplicados_estacion_hora']} repetidas.",
)

h("4. Método")
ul(
    "**Dentro (tratamiento):** Mazarredo y Mª Díaz de Haro, dentro de la ZBE.",
    "**Fuera (control):** Europa, Barakaldo, Basauri, Erandio y Castrejana. Mismo tiempo atmosférico y mismo tipo de coches que el "
    "centro, pero sin ZBE: muestran lo que habría bajado el NO₂ sin ella.",
    f"**Fondo:** Arraiz, en un monte lejos del tráfico ({es(est['Arraiz']['previo'])} µg/m³ antes de la ZBE, frente a "
    f"{es(p1['fuera_pre'])} en el control). No se parece a una estación urbana, así que no entra en el control.",
)
p(f"**Antes:** {fecha(per['fecha_inicio'])} – 14/06/2024. **Después:** {fecha(per['fecha_fase1'])} – {fecha(per['fecha_fin'])} "
  f"(fase 1 hasta el 15/06/2025). **Caída bruta** = media después − media antes. **Efecto neto** = caída bruta dentro − caída bruta "
  "fuera (método de diferencias en diferencias, estadístico). Mirar solo dentro mezclaría la ZBE con lo que habría bajado igualmente; "
  "restar lo que bajó fuera lo separa.")
p(f"**Margen de error.** Dos horas seguidas se parecen (mismo atasco, misma falta de viento) y no son datos independientes. Por eso se "
  f"agrupa por semanas y se repite el cálculo {es(p1['repeticiones_bootstrap'], 0)} veces sorteando semanas (bootstrap). El **intervalo "
  "del 95 %** recoge el 95 % central de los resultados; si no incluye el cero, la bajada no se explica por el azar.")

filas_est = []
for zona, nombre_zona in [("dentro", "Dentro"), ("fuera", "Fuera"), ("fondo", "Fondo")]:
    for e in sorted((e for e in est if est[e]["zona"] == zona), key=lambda e: est[e]["var_post_vs_previo_pct"]):
        filas_est.append([e, nombre_zona, es(est[e]["previo"]), es(est[e]["post"]), es(est[e]["var_post_vs_previo_pct"], 1, signo=True)])
tabla(["Estación", "Grupo", "Antes", "Después", "Cambio (%)"], filas_est, [5, 2, 2, 2, 2])
p("*Antes* y *Después:* NO₂ medio (µg/m³) en cada periodo. *Cambio:* (Después − Antes) ÷ Antes.")

h("5. Resultados")
p(f"**P1. ¿Bajó el NO₂ dentro más que fuera?** Dentro: {es(p1['dentro_pre'])} → {es(p1['dentro_post'])} µg/m³ "
  f"({es(p1['caida_bruta_dentro'])}). Fuera: {es(p1['fuera_pre'])} → {es(p1['fuera_post'])} ({es(p1['caida_bruta_fuera'])}). "
  f"Efecto neto: {es(p1['caida_bruta_dentro'])} − ({es(p1['caida_bruta_fuera'])}) = **{es(p1['efecto_neto_did'])} µg/m³** "
  f"({es(p1['efecto_neto_did_pct'], 1)} % del nivel de antes; {intervalo(p1['ic95_inf'], p1['ic95_sup'])}). "
  f"*Qué significa:* de la bajada de {es(abs(p1['caida_bruta_dentro']))} dentro, {es(abs(p1['caida_bruta_fuera']))} se vio también "
  f"fuera; la parte propia de dentro, {es(abs(p1['efecto_neto_did']))}, es la que se asocia a la ZBE. Es una estimación aproximada: "
  f"de 2022 a 2023 el NO₂ cambió {es(cambio_previo_dentro, signo=True)} dentro y {es(cambio_previo_fuera, signo=True)} fuera, "
  "así que antes de la ZBE no iban del todo en paralelo.")
img("img/p1_evolucion_mensual_no2.png", "Figura 1. La distancia entre la línea roja y la azul se reduce después de la fase 1.", 14)

p(f"**P2. ¿Se concentra en el horario de la ZBE?** En horario ZBE el NO₂ bajó {es(abs(p2['en_horario']['dentro_caida_bruta']))} "
  f"dentro y {es(abs(p2['en_horario']['fuera_caida_bruta']))} fuera: efecto neto **{es(p2['efecto_neto_en_horario_zbe'])}** "
  f"({intervalo(*p2['ic95_en_horario_zbe'])}). Fuera de horario: {es(p2['efecto_neto_fuera_horario'])} "
  f"({intervalo(*p2['ic95_fuera_horario'])}). *Qué significa:* {es(p2['efecto_neto_en_horario_zbe'])} es un efecto neto, no una "
  "caída. La bajada propia de dentro es mayor cuando la ZBE está activa, como cabe esperar si se debe a ella.")
img("img/p2_horario_zbe.png", "Figura 2. La distancia entre la barra roja y la azul de cada grupo es el efecto neto.", 11)

p(f"**P3. ¿Se mantiene en calma?** Con viento de menos de 2 m/s, dentro pasó de {es(p3['dentro_calma_pre'])} a "
  f"{es(p3['dentro_calma_post'])} µg/m³ ({es(p3['var_calma_post_pct'], 1)} %); efecto neto **{es(p3['efecto_neto'])}** "
  f"({intervalo(p3['ic95_inf'], p3['ic95_sup'])}). *Qué significa:* la bajada se mantiene sin viento; no se debe a que hiciera más viento.")
p(f"**P4. ¿Baja también el SO₂?** El SO₂ apenas sale de los coches. Efecto neto: **{es(p4['efecto_neto'], signo=True)}** "
  f"({intervalo(p4['ic95_inf'], p4['ic95_sup'])}; {', '.join(p4['estaciones_sin_so2'])} no lo mide). *Qué significa:* no baja más "
  "dentro que fuera, así que la bajada del NO₂ no parece venir de una causa que afecte a todo el aire del centro.")
p(f"**P5. ¿Qué aportó la fase 2?** Fase 1 frente a antes: **{es(f1['efecto_neto'])}** ({intervalo(f1['ic95_inf'], f1['ic95_sup'])}). "
  f"Fase 2 frente a fase 1: **{es(f2['efecto_neto'])}** ({intervalo(f2['ic95_inf'], f2['ic95_sup'])}). *Qué significa:* la fase 2 no "
  "muestra una bajada adicional que se pueda distinguir de cero; la bajada propia de dentro llegó sobre todo con la fase 1.")
img("img/p5_fases_no2.png", "Figura 3. Las dos zonas bajan; lo que cuenta es cuánto más baja la barra roja de una fase a otra.", 11)

h("6. Conclusiones y recomendaciones")
p("**Conclusiones**")
ul(
    f"El NO₂ bajó dentro de la ZBE más que fuera: efecto neto de {es(p1['efecto_neto_did'])} µg/m³ "
    f"({intervalo(p1['ic95_inf'], p1['ic95_sup'])}), frente a una caída bruta de {es(p1['caida_bruta_dentro'])}.",
    f"Esa bajada se concentra en el horario de la ZBE ({es(p2['efecto_neto_en_horario_zbe'])} frente a "
    f"{es(p2['efecto_neto_fuera_horario'])}), se mantiene en calma ({es(p3['efecto_neto'])}) y no aparece en el SO₂ ({es(p4['efecto_neto'], signo=True)}).",
    f"La fase 2 no muestra una bajada adicional distinguible de cero ({es(f2['efecto_neto'])}; {intervalo(f2['ic95_inf'], f2['ic95_sup'])}).",
)
p("**Recomendaciones**")
ul(
    f"**Mantener la ZBE con su horario actual:** el efecto neto ({es(p1['efecto_neto_did'])} µg/m³) es distinto de cero y mayor "
    f"cuando la ZBE está activa ({es(p2['efecto_neto_en_horario_zbe'])}).",
    f"**No ampliar todavía con medidas como la de la fase 2:** añadió {es(f2['efecto_neto'])} µg/m³, dentro del margen de error. "
    "Repetir el cálculo cuando la fase 2 tenga más datos.",
    f"**Ajustar la medición antes de ampliar:** solo hay {n_dentro} estaciones dentro y el control es desigual. No hemos comprobado si "
    f"la estación de {control_min} tuvo cambios propios (obras, traslado o sensor); su bajada "
    f"({es(est[control_min]['var_post_vs_previo_pct'], 1)} %), mayor que la de las estaciones de dentro, se trata como una limitación "
    "del grupo de control. Conviene valorar más puntos de medida dentro de la ZBE.",
)
p(f"**Limitaciones:** pocas estaciones ({n_dentro} dentro y {n_fuera} de control); antes de la ZBE dentro y fuera no iban del todo en "
  "paralelo; las estaciones miden la concentración de NO₂ en el aire, no lo que emiten los coches.")

h("7. Herramientas")
tabla(["Herramienta", "Para qué", "Por qué"], [
    ["Python, pandas y Jupyter", "Limpiar, unir y analizar; guardar las cifras en resultados.json.", "Lee CSV y fechas con zona horaria; el notebook deja juntos cálculo y resultado y se puede repetir."],
    ["Node-RED", "Consultar las fuentes y escribir en InfluxDB de forma periódica.", "Flujos visuales sin programar un servicio propio. Es automatización, no inteligencia artificial."],
    ["InfluxDB 2.9", "Guardar las series horarias para los paneles.",
     "Hecha para datos con fecha y hora: agrupar por hora o día y borrar datos antiguos son funciones del motor. SQL Server "
     "(relacional, de uso general) también serviría, pero habría que diseñar las tablas y escribir esas agregaciones a mano, "
     "y no necesitamos sus relaciones entre tablas."],
    ["Grafana 11.2", "Paneles, alertas y permisos por equipo.", "Se conecta a InfluxDB sin código intermedio."],
    ["Docker Compose", "Arrancar todos los servicios con un comando.", "Los tres miembros del equipo trabajan con el mismo entorno."],
    ["Servidor MCP", "Consultar InfluxDB desde un asistente.", "Solo lectura: no puede modificar datos."],
], [4, 6, 10])

h("8. Orden de tareas y responsabilidades")
ALFRED = "Alfred Gabriel (Product Owner · Relación con el cliente y desarrollo)"
INIGO = "Iñigo Guzmán (Lead Data Engineer · Datos e infraestructura)"
KERMAN = "Kerman Latorre (Scrum Master · Análisis y modelado)"
tabla(["Paso", "Tarea", "Responsable y rol"], [
    ["1", "Descarga de las fuentes", INIGO],
    ["2", "Limpieza y comprobación crudo frente a limpio", INIGO],
    ["3", "Integración de aire, calendario y meteorología", ALFRED],
    ["4", "Análisis P1-P5, margen de error y resultados.json", KERMAN],
    ["5", "Carga en InfluxDB, paneles y alertas de Grafana", INIGO],
    ["6", "Informe para el cliente", ALFRED],
], [1, 8, 9])
p("Todo el equipo conoce y puede explicar el trabajo completo; la asignación indica quién lideró cada tarea.")


# ---------------------------------------------------------------------------
def a_markdown(bloques=B, portada=portada, nombre=NOMBRE, script="docs/generar_informe.py"):
    out = [f"# {portada['titulo']}", f"### {portada['subtitulo']}", ""]
    out += [f"**{k}:** {v}  " for k, v in portada["filas"]]
    out += ["", f"Versión para imprimir: [{nombre}.docx]({nombre}.docx) · [{nombre}.pdf]({nombre}.pdf). "
            f"Este fichero lo genera `{script}` a partir de `resultados/resultados.json`.", ""]
    for b in bloques:
        if b[0] == "h":
            out += [f"## {b[1]}", ""]
        elif b[0] == "p":
            out += [b[1], ""]
        elif b[0] == "ul":
            out += [f"- {i}" for i in b[1]] + [""]
        elif b[0] == "tabla":
            cab, filas = b[1], b[2]
            out.append("| " + " | ".join(cab) + " |")
            out.append("|" + "---|" * len(cab))
            out += ["| " + " | ".join(f) + " |" for f in filas]
            out.append("")
        elif b[0] == "img":
            out += [f"![{b[2]}]({b[1]})", "", f"*{b[2]}*", ""]
    return subindices("\n".join(out))


def subindices(t):
    """'NO₂' -> 'NO<sub>2</sub>': Word lo pone como subíndice con la misma fuente (Arial)."""
    return t.replace("₂", "<sub>2</sub>")


def html_inline(t):
    t = subindices(html.escape(t, quote=False))
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"\*(.+?)\*", r"<i>\1</i>", t)
    return t


def a_html(bloques=B, portada=portada):
    css = """
    body, p, li, td, th { font-family: Arial; font-size: 11pt; }
    p { margin: 0 0 4pt 0; }
    h2 { font-family: Arial; font-size: 12pt; color: #1F4E79; margin: 8pt 0 3pt 0; page-break-after: avoid; }
    p.vineta { margin: 0 0 2pt 14pt; text-indent: -10pt; }
    table.datos { border-collapse: collapse; margin: 2pt 0 4pt 0; width: 100%; }
    table.datos td, table.datos th { border: 1px solid #999999; padding: 0 3pt; vertical-align: top; }
    table.datos th { background: #DCE6F0; text-align: left; }
    p.pie { text-align: center; font-style: italic; margin-bottom: 6pt; }
    p.figura { text-align: center; margin: 2pt 0 0 0; page-break-after: avoid; }
    """
    out = [f"<html><head><meta charset='utf-8'><style>{css}</style></head><body>"]
    out.append("<p style='margin-top:150pt; text-align:center; font-size:24pt; font-weight:bold; color:#1F4E79'>"
               f"{html_inline(portada['titulo'])}</p>")
    out.append(f"<p style='text-align:center; font-size:14pt; margin-bottom:60pt'>{html.escape(portada['subtitulo'])}</p>")
    out.append("<table style='margin-left:auto; margin-right:auto; border-collapse:collapse'>")
    for k, v in portada["filas"]:
        out.append(f"<tr><td style='padding:5pt 12pt; font-weight:bold; font-size:12pt'>{k}</td>"
                   f"<td style='padding:5pt 12pt; font-size:12pt'>{html.escape(v)}</td></tr>")
    out.append("</table><br clear=all style='page-break-before:always'>")
    for b in bloques:
        if b[0] == "h":
            out.append(f"<h2>{html.escape(b[1])}</h2>")
        elif b[0] == "p":
            out.append(f"<p>{html_inline(b[1])}</p>")
        elif b[0] == "ul":
            # Viñeta escrita como carácter en Arial (las listas de Word usan la fuente Symbol)
            out += [f"<p class='vineta'>•&nbsp;&nbsp;{html_inline(i)}</p>" for i in b[1]]
        elif b[0] == "tabla":
            cab, filas, anchos = b[1], b[2], b[3]
            col = "".join(f"<col width='{a / sum(anchos) * 100:.0f}%'>" for a in anchos)
            out.append(f"<table class='datos'>{col}<tr>" + "".join(f"<th>{html_inline(c)}</th>" for c in cab) + "</tr>")
            out += ["<tr>" + "".join(f"<td>{html_inline(c)}</td>" for c in f) + "</tr>" for f in filas]
            out.append("</table>")
        elif b[0] == "img":
            ruta = DIR_DOCS / b[1]
            ancho_px, alto_px = Image.open(ruta).size
            ancho_pt = b[3] / 2.54 * 72
            alto_pt = ancho_pt * alto_px / ancho_px
            out.append(f"<p class='figura'><img src='{ruta.resolve().as_uri()}' width='{ancho_pt:.0f}' height='{alto_pt:.0f}'></p>")
            out.append(f"<p class='pie'>{html_inline(b[2])}</p>")
    out.append("</body></html>")
    return "\n".join(out)


POWERSHELL_WORD = r"""
$ErrorActionPreference = 'Stop'
$w = New-Object -ComObject Word.Application
$w.Visible = $false
try {
    $d = $w.Documents.Open('{HTML}')
    foreach ($s in @($d.InlineShapes)) {
        if ($s.LinkFormat -ne $null) { $s.LinkFormat.SavePictureWithDocument = $true; $s.LinkFormat.BreakLink() }
    }
    $d.ActiveWindow.View.Type = 3
    $ps = $d.PageSetup
    $ps.PaperSize = 7
    $ps.TopMargin = 56.7; $ps.BottomMargin = 56.7; $ps.LeftMargin = 56.7; $ps.RightMargin = 56.7
    $ps.DifferentFirstPageHeaderFooter = -1
    $null = $d.Sections.Item(1).Footers.Item(1).PageNumbers.Add(1, $false)
    $d.Sections.Item(1).Footers.Item(1).Range.Font.Name = 'Arial'
    $d.Sections.Item(1).Footers.Item(1).Range.Font.Size = 10
    $d.SaveAs2('{DOCX}', 16)
    $d.Close()
    $d = $w.Documents.Open('{DOCX}')
    $d.ExportAsFixedFormat('{PDF}', 17)
    $d.Close(0)
} finally { $w.Quit() }
"""


def a_word(html_texto, nombre=NOMBRE):
    docx = DIR_DOCS / f"{nombre}.docx"
    pdf = DIR_DOCS / f"{nombre}.pdf"
    with tempfile.TemporaryDirectory() as tmp:
        f_html = Path(tmp) / "informe.html"
        f_html.write_text(html_texto, encoding="utf-8")
        script = POWERSHELL_WORD.replace("{HTML}", str(f_html)).replace("{DOCX}", str(docx)).replace("{PDF}", str(pdf))
        f_ps1 = Path(tmp) / "word.ps1"
        f_ps1.write_text(script, encoding="utf-8-sig")
        subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(f_ps1)], check=True)
    return docx, pdf


if __name__ == "__main__":
    (DIR_DOCS / "informe-cliente-sbd.md").write_text(a_markdown(), encoding="utf-8")
    print("[OK] docs/informe-cliente-sbd.md")
    if "--solo-md" not in sys.argv:
        docx, pdf = a_word(a_html())
        print(f"[OK] docs/{docx.name} y docs/{pdf.name}")
