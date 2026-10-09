#!/usr/bin/env python3
"""
haizelab/chatbot/main.py
========================
Servidor API REST para HaizeLab Assistant (Reto 0).
Tecnología: FastAPI + Pydantic + HTTPX.

Arquitectura de Razonamiento:
1. Inyecta la evidencia empírica oficial del proyecto en un System Prompt de razonamiento analítico.
2. Si GEMINI_API_KEY está configurada en .env, consulta a Google Gemini (rápido y con razonamiento profundo).
3. Si Ollama está activo en el host (11434), consulta a Ollama en local.
4. Si no hay ningún LLM activo, utiliza la base de conocimiento local para responder con datos oficiales.
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
import json
import os
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── Configuración ──────────────────────────────────────────────────────────────
DIR_CHATBOT = Path(__file__).resolve().parent
FICHERO_KB = DIR_CHATBOT / "knowledge_base.json"

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://host.docker.internal:11434").rstrip("/")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:1.5b")

app = FastAPI(
    title="HaizeLab Assistant API",
    description="Asistente con razonamiento para la evaluación de la ZBE de Bilbao (Reto 0)",
    version="2.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Base de Conocimiento y Prompt de Razonamiento ──────────────────────────────
try:
    with open(FICHERO_KB, "r", encoding="utf-8") as f:
        KB_DATA = json.load(f)
except Exception:
    KB_DATA = {}

SYSTEM_PROMPT = """Eres HaizeLab Assistant, un asistente analítico riguroso del proyecto "Evaluación de la Zona de Bajas Emisiones de Bilbao (2022-2026)" (Reto 0 del Centro de Formación Somorrostro).

EVIDENCIA EMPÍRICA Y DATOS OFICIALES DEL PROYECTO:
1. Modelo Causal: Diferencias en Diferencias (Diff-in-Diff) con 41.700 horas de datos en 8 estaciones oficiales.
2. Resultado Neto Atribuible: Reducción neta de -1,63 µg/m³ (-6,4%) en NO2 (IC 95%: -1,87 a -1,39 µg/m³, p < 0,001).
3. Comparativa: Dentro de la ZBE (Mazarredo y Mª Díaz de Haro) el NO2 bajó de 25,50 a 21,90 µg/m³ (-14,1%). Fuera en control metropolitano (Europa, Barakaldo, Basauri, Erandio, Castrejana) bajó de 18,25 a 16,29 µg/m³ (-10,8%). La diferencia neta (-1,63 µg/m³) aísla el efecto real de la ZBE.
4. Control de Meteorología: En episodios de calma atmosférica (<2 m/s), el NO2 bajó un -13,4% dentro de la ZBE, demostrando que la mejora no dependió del viento. Regresión con controles climáticos arroja -1,74 µg/m³.
5. Control Placebo: El SO2 (que proviene de la industria, no del tráfico) tuvo un cambio neto de +0,33 µg/m³, confirmando que el método no inventa bajadas y que la reducción de NO2 proviene del tráfico.
6. Aforos de Tráfico: El acceso por San Mamés descendió un -10,1% en 2024 (de 50.127 a 45.052 veh/día) con rebote a 48.543 en 2025 (-3,2% neto vs 2023).
7. Equipo y Metodología: Alfred Gabriel (Product Owner / Docker, redes, MCP), Iñigo Guzman (Lead Data Engineer / InfluxDB, Node-RED, Grafana), Kerman Latorre (Scrum Master / econometría Diff-in-Diff).
8. Stack: Docker Compose, InfluxDB 2.9 (buckets aire, meteo, trafico, aire_demo), Node-RED 5.0, Grafana 11.2 (con control de acceso por roles: Directiva, Análisis, IT), Servidor MCP (:5001).

DIRECTRICES DE RAZONAMIENTO:
- Razona y explica el 'por qué' de los resultados conectando tráfico, meteorología y calidad del aire.
- Si te preguntan si ha funcionado la ZBE, responde que el efecto reductor está confirmado pero es moderado (-1,63 µg/m³), explicando que más de la mitad de la bajada bruta se debió a factores climáticos y renovación del parque móvil.
- Responde siempre en español, de forma analítica, estructurada y concisa."""

RESPUESTAS_LOCALES = {
    "resultado_zbe": (
        "La evaluación con el modelo Diferencias en Diferencias (Diff-in-Diff) demuestra que la ZBE "
        "redujo el NO₂ de forma neta atribuible en **-1,63 µg/m³ (-6,4%)**.\n\n"
        "Dentro de la ZBE la concentración bajó de 25,50 a 21,90 µg/m³ (-14,1%), mientras que en las estaciones "
        "de control exteriores bajó de 18,25 a 16,29 µg/m³ (-10,8%). La diferencia entre ambas variaciones "
        "aísla el efecto real de la ordenanza frente a la meteorología."
    ),
    "datos": (
        "El proyecto integra **41.700 horas de registros** continuos entre 2022 y 2026 de 8 estaciones oficiales:\n"
        "- Dentro de la ZBE: Mazarredo y María Díaz de Haro.\n"
        "- Control urbano metropolitano: Europa, Barakaldo, Basauri, Erandio y Castrejana.\n"
        "- Fondo regional: Monte Arraiz.\n"
        "Las fuentes son Open Data Euskadi (calidad del aire) y Open-Meteo (clima)."
    ),
    "trafico": (
        "El aforo vehicular del acceso principal por San Mamés descendió de 50.127 vehículos/día en 2023 "
        "a 45.052 en 2024 (**-10,1%**), repuntando a 48.543 en 2025. El descenso del NO₂ en el centro "
        "guarda correlación directa con esta reducción de intensidad de tráfico."
    ),
    "infraestructura": (
        "La infraestructura se despliega con Docker Compose e integra:\n"
        "1. **InfluxDB 2.9:** Almacenamiento en series temporales con 4 buckets y tokens con permisos mínimos.\n"
        "2. **Node-RED 5.0:** Ingesta continua en tiempo real de meteorología cada 15 min y tráfico cada 5 min.\n"
        "3. **Grafana 11.2:** Cuadros de mando analíticos con control de acceso por roles (Directiva, Análisis e IT).\n"
        "4. **Servidor MCP:** Servicio de solo lectura para conectar herramientas de IA a InfluxDB."
    ),
    "equipo": (
        "El equipo de HaizeLab (Reto 0) está formado por tres especialistas:\n"
        "- **Alfred Gabriel:** Product Owner (infraestructura Docker, despliegue y MCP).\n"
        "- **Iñigo Guzman:** Lead Data Engineer (Node-RED, InfluxDB y cuadros de mando en Grafana).\n"
        "- **Kerman Latorre:** Scrum Master (análisis econométrico Diff-in-Diff y modelado en Python)."
    ),
    "general": (
        "Soy HaizeLab Assistant. Puedo razonar y responder a tus preguntas sobre los resultados de la ZBE de Bilbao, "
        "las 8 estaciones analizadas, el impacto en el tráfico, la meteorología o la arquitectura tecnológica del proyecto."
    )
}

# ── Modelos de Datos (Pydantic) ────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: Optional[str] = None
    mensaje: Optional[str] = None
    history: Optional[List[Dict[str, Any]]] = None

class ChatResponse(BaseModel):
    respuesta: str
    fuentes: List[str]
    modelo: str

# ── Motores de Razonamiento (Gemini / Ollama / Local) ──────────────────────────
async def razonar_con_gemini(pregunta: str) -> Optional[str]:
    """Razonamiento dinámico mediante Google Gemini API."""
    if not GEMINI_API_KEY:
        return None
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": f"{SYSTEM_PROMPT}\n\nPregunta del usuario:\n{pregunta}\n\nRespuesta razonada:"}]}],
        "generationConfig": {"temperature": 0.25, "maxOutputTokens": 800}
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                cands = data.get("candidates", [])
                if cands:
                    return cands[0]["content"]["parts"][0]["text"].strip()
    except Exception:
        pass
    return None

async def razonar_con_ollama(pregunta: str) -> Optional[str]:
    """Razonamiento local mediante Ollama si está activo."""
    prompt = f"{SYSTEM_PROMPT}\n\nPregunta del usuario:\n{pregunta}\n\nRespuesta razonada:"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
            )
            if resp.status_code == 200:
                texto = resp.json().get("response", "").strip()
                if texto:
                    return texto
    except Exception:
        pass
    return None

def responder_localmente(pregunta: str) -> str:
    """Fallback determinista si no hay ningún motor LLM configurado."""
    p = pregunta.lower()
    if any(k in p for k in ["estacion", "estaciones", "mazarredo", "maria diaz", "maría díaz"]):
        return RESPUESTAS_LOCALES["datos"]
    elif any(k in p for k in ["docker", "influx", "grafana", "node-red", "nodered", "mcp", "arquitectura", "infraestructura", "base de datos", "monitorizaci"]):
        return RESPUESTAS_LOCALES["infraestructura"]
    elif any(k in p for k in ["trafico", "tráfico", "coche", "san mames", "san mamés", "aforo", "vehiculo"]):
        return RESPUESTAS_LOCALES["trafico"]
    elif any(k in p for k in ["equipo", "autor", "quien", "quién", "iñigo", "kerman", "alfred", "somorrostro"]):
        return RESPUESTAS_LOCALES["equipo"]
    elif any(k in p for k in ["fuente", "dataset", "hora", "registro", "datos"]):
        return RESPUESTAS_LOCALES["datos"]
    elif any(k in p for k in ["zbe", "no2", "calidad", "resultado", "funcionado", "reduccion", "reducción", "caida", "caída", "efecto", "did", "diff"]):
        return RESPUESTAS_LOCALES["resultado_zbe"]
    return RESPUESTAS_LOCALES["general"]

# ── Endpoints HTTP ─────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {
        "status": "ok",
        "servicio": "haizelab-chatbot",
        "razonamiento_gemini": bool(GEMINI_API_KEY),
        "razonamiento_ollama": OLLAMA_URL
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(peticion: ChatRequest):
    pregunta = (peticion.message or peticion.mensaje or "").strip()
    if not pregunta:
        return ChatResponse(
            respuesta="Por favor, escribe una pregunta sobre el proyecto HaizeLab.",
            fuentes=["Validación"],
            modelo="Local"
        )

    # 1. Intentar razonamiento con Gemini (si hay API key en .env)
    resp_gemini = await razonar_con_gemini(pregunta)
    if resp_gemini:
        return ChatResponse(
            respuesta=resp_gemini,
            fuentes=["Google Gemini 2.0 Flash", "Evidencia HaizeLab"],
            modelo="Gemini 2.0 Flash (Razonamiento)"
        )

    # 2. Intentar razonamiento con Ollama local (si Ollama está corriendo)
    resp_ollama = await razonar_con_ollama(pregunta)
    if resp_ollama:
        return ChatResponse(
            respuesta=resp_ollama,
            fuentes=["Ollama Local", "Evidencia HaizeLab"],
            modelo=f"Ollama ({OLLAMA_MODEL})"
        )

    # 3. Fallback seguro desde la base de conocimiento local
    resp_fija = responder_localmente(pregunta)
    return ChatResponse(
        respuesta=resp_fija,
        fuentes=["knowledge_base.json", "Informe ZBE Bilbao"],
        modelo="HaizeLab Knowledge Engine (Offline)"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
