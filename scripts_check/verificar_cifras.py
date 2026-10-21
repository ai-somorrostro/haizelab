#!/usr/bin/env python3
"""
Compara las cifras de los documentos con resultados/resultados.json.

Comprueba tres cosas en cada documento:
  1. Cada cifra con decimales (p. ej. «−1,63») o con punto de miles (p. ej. «332.619») sale de
     resultados.json, directamente o de una cuenta sencilla con sus valores (lista DERIVADAS).
  2. No aparece ninguna cifra antigua de las que se corrigieron (lista ANTIGUAS).
  3. Están las cifras clave de cada documento (lista CLAVE).

Límite: comprueba que cada cifra existe en resultados.json, no de qué campo sale. Una cifra
redondeada puede coincidir por casualidad con otro valor del fichero.

Uso:  python scripts_check/verificar_cifras.py
Sale con código 1 si algo no cuadra.
"""
import html
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
R = json.loads((RAIZ / "resultados" / "resultados.json").read_text(encoding="utf-8"))

DOCUMENTOS = [
    "README.md",
    "docs/informe-cliente-sbd.md",
    "docs/propuesta-modelo-ia.md",
    "presentacion/index.html",
    "chatbot/main.py",
    "grafana/dashboards/haizelab-overview.json",
    "grafana/dashboards/haizelab-analisis-zbe.json",
]

# Cifras corregidas en las fases 1-6 que no deben volver a aparecer
ANTIGUAS = ["2,87", "21,90", "±0,24", "1,74", "28,10", "24,35", "32,32", "27,41", "1,81", "20,10", "17,55",
            "21,30", "18,35", "24,52", "98,8", "332.776", "333.418", "333.376", "41.700", "50.127", "p < 0,001"]


def valores(nodo):
    """Todos los números de resultados.json."""
    if isinstance(nodo, bool):
        return
    if isinstance(nodo, (int, float)):
        yield float(nodo)
    elif isinstance(nodo, dict):
        for v in nodo.values():
            yield from valores(v)
    elif isinstance(nodo, list):
        for v in nodo:
            yield from valores(v)


p1, p2, ia = R["p1_did"], R["p2_horario"], R["modelo_ia"]
rf = ia["metricas"][ia["modelo_elegido"]]
anual = R["medias_anuales_no2"]
tramos = list(ia["no2_por_tramo_viento"].values())
# Cifras que los documentos calculan a partir de resultados.json, con su cuenta
DERIVADAS = {
    "Cambio dentro 2022→2023": [anual["dentro"]["2023"] - anual["dentro"]["2022"]],
    "Cambio fuera 2022→2023": [anual["fuera"]["2023"] - anual["fuera"]["2022"]],
    "Cambio de NO₂ al pasar de un tramo de viento al siguiente": [b - a for a, b in zip(tramos, tramos[1:])],
}


def formatos(x):
    """Formas en que un número puede aparecer escrito (2, 1, 0 o 3 decimales; con y sin signo)."""
    salida = set()
    for v in (x, abs(x)):
        for dec in (0, 1, 2, 3):
            s = f"{v:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")
            salida.add(s.lstrip("-"))
    return salida


PERMITIDAS = set()
for v in list(valores(R)) + [x for lista in DERIVADAS.values() for x in lista]:
    PERMITIDAS |= formatos(v)

CIFRA = re.compile(r"(?<![\w.,])\d{1,3}(?:\.\d{3})+(?:,\d+)?(?![\w.,])|(?<![\w.,])\d+,\d+(?![\w,])")


def texto_visible(ruta, contenido):
    """Quita lo que no ve el lector: CSS, atributos y etiquetas en HTML; nada en los demás."""
    if ruta.endswith(".html"):
        contenido = re.sub(r"<style.*?</style>", " ", contenido, flags=re.S)
        contenido = re.sub(r"<[^>]+>", " ", contenido)
        contenido = html.unescape(contenido)
    return contenido


def es(x):
    return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


CLAVE = {
    "README.md": [p1["efecto_neto_did"], p1["ic95_inf"], p1["ic95_sup"], p2["efecto_neto_en_horario_zbe"], ia["efecto"]["efecto_neto"]],
    "docs/informe-cliente-sbd.md": [p1["efecto_neto_did"], p1["ic95_inf"], p1["ic95_sup"], R["p5_fases"]["fase2_vs_fase1"]["efecto_neto"]],
    "docs/propuesta-modelo-ia.md": [ia["efecto"]["efecto_neto"], rf["mae_val"], ia["placebo_15_06_2023"]["efecto_neto"]],
    "presentacion/index.html": [p1["efecto_neto_did"], p1["ic95_inf"], p1["ic95_sup"], ia["efecto"]["efecto_neto"]],
}

fallos = 0
for ruta in DOCUMENTOS:
    contenido = texto_visible(ruta, (RAIZ / ruta).read_text(encoding="utf-8"))
    cifras = CIFRA.findall(contenido)
    desconocidas = sorted({c for c in cifras if c not in PERMITIDAS})
    antiguas = [a for a in ANTIGUAS if re.search(r"(?<![\d,])" + re.escape(a) + r"(?![\d])", contenido)]
    sin_clave = [es(v) for v in CLAVE.get(ruta, []) if es(abs(v)) not in contenido]
    ok = not (desconocidas or antiguas or sin_clave)
    fallos += not ok
    print(f"[{'OK' if ok else 'FALLO'}] {ruta}: {len(cifras)} cifras revisadas")
    for c in desconocidas:
        i = contenido.find(c)
        print(f"    - {c} no sale de resultados.json: «…{' '.join(contenido[max(0, i - 60):i + 30].split())}…»")
    for a in antiguas:
        print(f"    - cifra antigua: {a}")
    for c in sin_clave:
        print(f"    - falta la cifra clave {c}")

print(f"\n{len(DOCUMENTOS) - fallos} de {len(DOCUMENTOS)} documentos cuadran con resultados/resultados.json.")
sys.exit(1 if fallos else 0)
