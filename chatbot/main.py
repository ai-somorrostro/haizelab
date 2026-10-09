#!/usr/bin/env python3
"""
haizelab/chatbot/main.py
========================
Servidor API REST para HaizeLab Assistant (Reto 0).
Tecnología: FastAPI + Pydantic + HTTPX.

Funcionamiento:
1. Carga la base de conocimiento local (knowledge_base.json) con los resultados del proyecto.
2. Si un modelo LLM local (Ollama) está disponible, le inyecta el contexto y genera la respuesta.
3. Si Ollama no está disponible, responde de forma determinista desde la base de conocimiento local.
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

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://host.docker.internal:11434").rstrip("/")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:1.5b")

app = FastAPI(
    title="HaizeLab Assistant API",
    description="Asistente explicable para la evaluación de la ZBE de Bilbao (Reto 0)",
    version="2.0.0"
)

# Permitir conexiones desde cualquier origen local (Presentación, Grafana, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Carga de Conocimiento del Proyecto ─────────────────────────────────────────
try:
    with open(FICHERO_KB, "r", encoding="utf-8") as f:
        KB_DATA = json.load(f)
except Exception:
    KB_DATA = {}

ESTADISTICAS = KB_DATA.get("estadisticas", {})

# Contexto resumido para inyectar al modelo de lenguaje
CONTEXTO_PROYECTO = f"""
Proyecto HaizeLab - Reto 0 (CF Somorrostro):
- Evaluación de la Zona de Bajas Emisiones (ZBE) de Bilbao sobre el NO2 (2022-2026).
- Muestra: 41.700 horas de datos en 8 estaciones oficiales.
- Modelo Cuasiexperimental: Diferencias en Diferencias (Diff-in-Diff).
- Resultado Neto Atribuible a la ZBE: -1,63 µg/m³ (-6,4%) en NO2.
- Dentro de la ZBE (Mazarredo y Mª Díaz de Haro): bajó -14,1% (de 25,50 a 21,90 µg/m³).
- Estaciones de Control fuera (Gran Bilbao): bajó -10,8% (de 18,25 a 16,29 µg/m³).
- En episodios de calma atmosférica (<2 m/s): el NO2 bajó un -13,4% dentro de la ZBE.
- Test de placebo con SO2: variación neta de +0,33 µg/m³ (confirma que la bajada de NO2 es por tráfico y no genérica).
- Tráfico en acceso San Mamés: -10,1% en 2024 respecto a 2023.
- Infraestructura: Docker Compose, InfluxDB 2 (4 buckets: aire, meteo, trafico, aire_demo), Node-RED (ingesta en tiempo real), Grafana (dashboards y control de acceso), Servidor MCP (puerto 5001).
- Equipo y Roles: Alfred Gabriel (Product Owner), Iñigo Guzman (Lead Data Engineer) y Kerman Latorre (Scrum Master).
"""

# Respuestas precomputadas para cuando no haya LLM disponible (modo local garantizado)
RESPUESTAS_LOCALES = {
    "resultado_zbe": (
        "La evaluación con el modelo Diferencias en Diferencias (Diff-in-Diff) demuestra que la ZBE "
        "redujo el NO₂ de forma neta atribuible en **-1,63 µg/m³ (-6,4%)**.\n\n"
        "Dentro de la ZBE la concentración bajó de 25,50 a 21,90 µg/m³ (-14,1%), mientras que en las estaciones "
        "de control exteriores bajó de 18,25 a 16,29 µg/m³ (-10,8%). La diferencia entre ambas variaciones "
        "aisla el efecto real de la ordenanza frente a la meteorología."
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
        "a 45.052 en 2024 (**-10,1%**), repuntando levemente a 48.543 en 2025. El descenso del NO₂ en el centro "
        "guarda correlación directa con esta reducción de intensidad de tráfico."
    ),
    "infraestructura": (
        "La infraestructura se despliega con Docker Compose e integra:\n"
        "1. **InfluxDB 2.9:** Almacenamiento en series temporales con 4 buckets (aire, meteo, trafico, aire_demo) y tokens con permisos mínimos.\n"
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
        "Soy HaizeLab Assistant. Puedo responder a tus preguntas sobre los resultados de la ZBE de Bilbao, "
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

# ── Lógica de Inferencia ───────────────────────────────────────────────────────
async def consultar_ollama(pregunta: str) -> Optional[str]:
    """Intenta consultar a Ollama local inyectando el contexto del proyecto."""
    prompt = (
        f"Eres HaizeLab Assistant, un asistente técnico para el proyecto de evaluación de la ZBE de Bilbao.\n"
        f"Responde en español de forma precisa y concisa usando esta información oficial:\n"
        f"{CONTEXTO_PROYECTO}\n\n"
        f"Pregunta del usuario: {pregunta}\n"
        f"Respuesta:"
    )
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
    """Fallback determinista que selecciona la mejor respuesta según palabras clave."""
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
    """Comprobación de estado del servicio."""
    return {"status": "ok", "servicio": "haizelab-chatbot"}

@app.post("/chat", response_model=ChatResponse)
async def chat(peticion: ChatRequest):
    """Endpoint principal de conversación."""
    texto_usuario = (peticion.message or peticion.mensaje or "").strip()
    if not texto_usuario:
        return ChatResponse(
            respuesta="Por favor, escribe una pregunta sobre el proyecto HaizeLab.",
            fuentes=["Validación"],
            modelo="Local"
        )

    # 1. Intentar responder con Ollama local
    respuesta_llm = await consultar_ollama(texto_usuario)
    if respuesta_llm:
        return ChatResponse(
            respuesta=respuesta_llm,
            fuentes=["Ollama Local", "knowledge_base.json"],
            modelo=f"Ollama ({OLLAMA_MODEL})"
        )

    # 2. Si Ollama no está activo, usar la base de conocimiento local
    respuesta_fija = responder_localmente(texto_usuario)
    return ChatResponse(
        respuesta=respuesta_fija,
        fuentes=["knowledge_base.json", "Informe ZBE Bilbao"],
        modelo="HaizeLab Knowledge Engine"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
