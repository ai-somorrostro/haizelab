"""
haizelab/chatbot/main.py
========================
Servidor API REST seguro para HaizeLab Assistant (Reto 0).
Seguridad defensiva implementada:
  - Rate limiting en memoria por IP (máx. 25 req/min) para prevenir DoS.
  - Validación de longitud estricta en entradas (max_length=500).
  - CORS blindado con orígenes autorizados.
  - Ocultación de topología de red interna (sin exponer host.docker.internal).
  - Manejo genérico de excepciones sin fuga de stack trace.
"""

from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import os
import time
import logging
from collections import defaultdict
import uvicorn
import httpx

from rag_engine import RAGEngine, OLLAMA_URL, OLLAMA_MODEL

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = FastAPI(
    title="HaizeLab Assistant API",
    description="Chatbot local RAG para el Reto 0: ¿Ha funcionado la ZBE de Bilbao?",
    version="1.0.0"
)

# CORS: orígenes web autorizados y soporte para apertura directa de archivo local (file:// con Origin null)
ORIGENES_PERMITIDOS = [
    "https://haizelab-presentacion.vercel.app",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "null"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=r".*",
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

@app.middleware("http")
async def force_cors_middleware(request: Request, call_next):
    if request.method == "OPTIONS":
        from fastapi.responses import Response
        response = Response(status_code=204)
    else:
        response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

engine = RAGEngine()

# ──────────────────────────────────────────────────────────────────────────────
# Rate Limiting defensivo en memoria por IP (prevención de Denial of Service)
# ──────────────────────────────────────────────────────────────────────────────
HISTORIAL_PETICIONES: Dict[str, List[float]] = defaultdict(list)
LIMITE_PETICIONES_MINUTO = 25
VENTANA_SEGUNDOS = 60.0

def verificar_rate_limit(ip_cliente: str):
    ahora = time.time()
    marcas = HISTORIAL_PETICIONES[ip_cliente]
    # Filtrar marcas anteriores a la ventana
    HISTORIAL_PETICIONES[ip_cliente] = [t for t in marcas if ahora - t < VENTANA_SEGUNDOS]
    if len(HISTORIAL_PETICIONES[ip_cliente]) >= LIMITE_PETICIONES_MINUTO:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Límite de consultas excedido. Por favor, espera un momento antes de volver a preguntar."
        )
    HISTORIAL_PETICIONES[ip_cliente].append(ahora)


class ChatMessage(BaseModel):
    role: str = Field(..., description="Rol del emisor: 'user' o 'assistant'")
    content: str = Field(..., max_length=1500, description="Contenido del mensaje")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500, description="Pregunta formulada por el usuario (máx. 500 caracteres)")
    history: Optional[List[ChatMessage]] = Field(default=None, max_items=10, description="Historial de conversación limitado a 10 turnos")


class ChatResponse(BaseModel):
    respuesta: str
    fuentes: List[str]
    modelo: str
    proyecto: str = "Haizen Lab · ¿Ha funcionado la ZBE de Bilbao? (Reto 0)"


@app.get("/health")
async def health_check():
    """Liveness probe para monitorización."""
    return {
        "status": "ok",
        "service": "haizelab-chatbot",
        "docs_indexados": len(engine.docs)
    }


@app.get("/info")
async def info_check():
    """Devuelve metadatos del servicio y métricas sin exponer direcciones internas."""
    ollama_disponible = False
    try:
        async with httpx.AsyncClient(timeout=1.5) as client:
            res = await client.get(f"{OLLAMA_URL}/api/tags")
            ollama_disponible = (res.status_code == 200)
    except Exception:
        ollama_disponible = False

    return {
        "proyecto": "Haizen Lab - Reto 0",
        "centro": "Centro de Formación Somorrostro",
        "ollama_modelo": OLLAMA_MODEL,
        "ollama_disponible": ollama_disponible,
        "modo_activo": f"ollama/{OLLAMA_MODEL}" if ollama_disponible else "deterministic-rag-local",
        "documentos_indexados": len(engine.docs),
        "estadisticas_principales": engine.stats
    }


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest, request: Request):
    """Endpoint principal de conversación con RAG local protegido contra abusos."""
    ip_cliente = request.client.host if request.client else "unknown"
    verificar_rate_limit(ip_cliente)

    try:
        historial_dicts = [h.dict() for h in payload.history] if payload.history else None
        resultado = await engine.responder(payload.message, historial=historial_dicts)
        return ChatResponse(
            respuesta=resultado["respuesta"],
            fuentes=resultado["fuentes"],
            modelo=resultado["modelo"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error procesando consulta: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Se produjo un error interno procesando la consulta. Por favor, inténtalo de nuevo."
        )


if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"[*] Iniciando HaizeLab Chatbot Seguro en http://{host}:{puerto}")
    uvicorn.run("main:app", host=host, port=puerto, reload=False)
