#!/usr/bin/env python3
"""
haizelab/chatbot/test_preguntas.py
==================================
Pruebas de validación automatizada para HaizeLab Assistant.
Ejecución: python chatbot/test_preguntas.py
"""

import asyncio
import sys
import unicodedata
from pathlib import Path

# Asegurar codificación UTF-8 en consola
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

DIR_CHATBOT = Path(__file__).resolve().parent
sys.path.insert(0, str(DIR_CHATBOT))

from main import chat, ChatRequest

def normalizar(s: str) -> str:
    nfkd = unicodedata.normalize("NFKD", s.lower())
    return "".join([c for c in nfkd if not unicodedata.combining(c)])

PRUEBAS = [
    {
        "id": 1,
        "categoria": "Impacto Causal ZBE",
        "pregunta": "¿Cuál es la reducción neta atribuible a la ZBE de Bilbao?",
        "esperado": ["-1,63", "diff-in-diff"]
    },
    {
        "id": 2,
        "categoria": "Calidad del Aire",
        "pregunta": "¿Cuánto bajó el NO2 dentro de la ZBE?",
        "esperado": ["25,50", "21,90"]
    },
    {
        "id": 3,
        "categoria": "Fuentes de Datos",
        "pregunta": "¿Qué fuentes de datos habéis utilizado en el proyecto?",
        "esperado": ["41.700", "open data euskadi"]
    },
    {
        "id": 4,
        "categoria": "Estaciones de Medición",
        "pregunta": "¿Qué estaciones están dentro de la ZBE?",
        "esperado": ["mazarredo", "maria diaz de haro"]
    },
    {
        "id": 5,
        "categoria": "Tráfico",
        "pregunta": "¿Cómo varió el tráfico en el acceso de San Mamés?",
        "esperado": ["-10,1%", "san mames"]
    },
    {
        "id": 6,
        "categoria": "Equipo y Roles",
        "pregunta": "¿Quiénes forman el equipo de HaizeLab?",
        "esperado": ["alfred", "iñigo", "kerman"]
    },
    {
        "id": 7,
        "categoria": "Infraestructura",
        "pregunta": "¿Qué base de datos y herramientas de monitorización usáis?",
        "esperado": ["influxdb", "grafana", "node-red"]
    }
]

async def ejecutar_pruebas():
    print("=" * 70)
    print("HaizeLab Assistant — Validación de Respuestas del Chatbot")
    print("=" * 70)
    exitos = 0

    for p in PRUEBAS:
        req = ChatRequest(message=p["pregunta"])
        res = await chat(req)
        resp_norm = normalizar(res.respuesta)

        paso = any(normalizar(esp) in resp_norm for esp in p["esperado"])
        if paso:
            exitos += 1
            print(f"[OK] Test {p['id']} ({p['categoria']}): superado ({res.modelo})")
        else:
            print(f"[FALLO] Test {p['id']} ({p['categoria']}):")
            print(f"       Pregunta: {p['pregunta']}")
            print(f"       Respuesta: {res.respuesta[:100]}...")

    print("-" * 70)
    print(f"Resultado: {exitos}/{len(PRUEBAS)} pruebas superadas correctamente.")
    print("=" * 70)
    return exitos == len(PRUEBAS)

if __name__ == "__main__":
    ok = asyncio.run(ejecutar_pruebas())
    sys.exit(0 if ok else 1)
