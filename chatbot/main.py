"""
haizelab/chatbot/main.py
========================
Servidor API REST para HaizeLab Assistant (Reto 0).
Expone:
  - POST /chat: Consulta con recuperación aumentada (RAG local).
  - GET /health: Comprobación de estado y liveness probe.
  - GET /info: Metadatos del sistema, estadísticas y estado del motor.
"""

from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import os
import uvicorn
import httpx

from rag_engine import RAGEngine, OLLAMA_URL, OLLAMA_MODEL

app = FastAPI(
    title="HaizeLab Assistant API",
    description="Chatbot local RAG para el Reto 0: ¿Ha funcionado la ZBE de Bilbao?",
    version="1.0.0"
)

# Permitir solicitudes CORS desde la presentación local y remota (Vercel)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = RAGEngine()


class ChatMessage(BaseModel):
    role: str = Field(..., description="Rol del emisor: 'user' o 'assistant'")
    content: str = Field(..., description="Contenido del mensaje")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Pregunta formulada por el usuario")
    history: Optional[List[ChatMessage]] = Field(default=None, description="Historial de conversación")


class ChatResponse(BaseModel):
    respuesta: str
    fuentes: List[str]
    modelo: str
    proyecto: str = "Haizen Lab · ¿Ha funcionado la ZBE de Bilbao? (Reto 0)"


@app.get("/health")
async def health_check():
    """Liveness probe para monitorización y comprobación de conexión desde el cliente web."""
    return {
        "status": "ok",
        "service": "haizelab-chatbot",
        "docs_indexados": len(engine.docs)
    }


@app.get("/info")
async def info_check():
    """Devuelve metadatos del servicio, disponibilidad de Ollama y métricas clave."""
    ollama_disponible = False
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            res = await client.get(f"{OLLAMA_URL}/api/tags")
            ollama_disponible = (res.status_code == 200)
    except Exception:
        ollama_disponible = False

    return {
        "proyecto": "Haizen Lab - Reto 0",
        "centro": "Centro de Formación Somorrostro",
        "ollama_url": OLLAMA_URL,
        "ollama_modelo": OLLAMA_MODEL,
        "ollama_disponible": ollama_disponible,
        "modo_activo": f"ollama/{OLLAMA_MODEL}" if ollama_disponible else "deterministic-rag-local",
        "documentos_indexados": len(engine.docs),
        "estadisticas_principales": engine.stats
    }


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest):
    """Endpoint principal de conversación con RAG local sobre el proyecto."""
    try:
        historial_dicts = [h.dict() for h in payload.history] if payload.history else None
        resultado = await engine.responder(payload.message, historial=historial_dicts)
        return ChatResponse(
            respuesta=resultado["respuesta"],
            fuentes=resultado["fuentes"],
            modelo=resultado["modelo"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno procesando consulta: {str(e)}")


if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"[*] Iniciando HaizeLab Chatbot en http://{host}:{puerto}")
    uvicorn.run("main:app", host=host, port=puerto, reload=False)
