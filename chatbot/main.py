#!/usr/bin/env python3
"""
haizelab/chatbot/main.py
========================
Servidor API REST para HaizeLab Assistant (Reto 0) con integración MCP a InfluxDB.
Tecnología: FastAPI + Pydantic + HTTPX.

Arquitectura de Razonamiento:
1. Conecta con el servidor InfluxDB mediante el token de solo lectura (mismo que el servidor MCP).
2. Expone herramientas analíticas (Function Calling) a Google Gemini para consultar en tiempo real:
   - Calidad del aire (NO2 en Mazarredo, Mª Díaz de Haro, Europa, Arraiz).
   - Meteorología (temperatura, viento, lluvia).
   - Aforos e intensidades de tráfico.
   - Consultas Flux personalizadas de solo lectura.
3. Si no hay clave de API o falla la conexión, utiliza la base de conocimiento local estructurada.
"""

from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
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
INFLUXDB_URL = os.environ.get("INFLUXDB_URL", "http://influxdb:8086").rstrip("/")
INFLUXDB_ORG = os.environ.get("INFLUXDB_ORG", "haizenlab")
MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://influx-mcp:5001/mcp/").rstrip("/")

app = FastAPI(
    title="HaizeLab Assistant API",
    description="Asistente con razonamiento y acceso a InfluxDB MCP para la evaluación de la ZBE de Bilbao (Reto 0)",
    version="2.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Carga de Credenciales InfluxDB / MCP ───────────────────────────────────────
def obtener_token_mcp() -> str:
    """Carga el token de solo lectura para InfluxDB desde el entorno o desde /tokens/tokens.env."""
    token = os.environ.get("INFLUXDB_MCP_TOKEN") or os.environ.get("INFLUXDB_READ_TOKEN")
    if token:
        return token.strip()
    tokens_path = Path("/tokens/tokens.env")
    if tokens_path.exists():
        try:
            with open(tokens_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("INFLUXDB_MCP_TOKEN="):
                        return line.split("=", 1)[1].strip()
                    elif line.startswith("INFLUXDB_READ_TOKEN=") and not token:
                        token = line.split("=", 1)[1].strip()
        except Exception:
            pass
    return token or os.environ.get("INFLUXDB_ADMIN_TOKEN", "")

# ── Base de Conocimiento y Prompt de Razonamiento ──────────────────────────────
try:
    with open(FICHERO_KB, "r", encoding="utf-8") as f:
        KB_DATA = json.load(f)
except Exception:
    KB_DATA = {}

SYSTEM_PROMPT = """Eres HaizeLab Assistant, un asistente analítico riguroso del proyecto "Evaluación de la Zona de Bajas Emisiones de Bilbao (2022-2026)" (Reto 0 del Centro de Formación Somorrostro).

ACCESO A DATOS EN TIEMPO REAL (INFLUXDB + MCP):
Dispones de herramientas integradas para consultar en directo la base de datos de series temporales InfluxDB 2.9 (organización haizenlab):
- Bucket `aire_demo`: Concentración horaria simulada y en streaming continuo de NO2 en 4 estaciones (Mazarredo y Mª Díaz de Haro dentro de la ZBE; Europa fuera; Monte Arraiz fondo).
- Bucket `meteo`: Ingesta continua de Open-Meteo cada 15 min (temperatura, viento, lluvia, etc.).
- Bucket `trafico`: Aforo y ocupación vehicular de los tramos de Bilbao cada 5 min.
- Bucket `aire`: Histórico completo oficial 2022-2026 de 8 estaciones (332.776 filas).

MODELOS Y EVIDENCIA EMPÍRICA (MIA & SBD):
En el proyecto se utilizan y contrastan dos familias metodológicas, ambas implementadas y ejecutadas con datos reales en el notebook oficial (`notebooks/zbe_bilbao.ipynb`):
1. Modelo de IA Propuesto y Elegido (Módulo MIA):
   - **Gradient Boosting** (`HistGradientBoostingRegressor`): Elegido formalmente en el entregable de MIA (`docs/propuesta-modelo-ia.md`) y ejecutado en el notebook (celdas 18 y 19).
   - Justificación: Modela la física no lineal del NO2 ante variables meteorológicas (velocidad y dirección de viento, lluvia, temperatura, humedad) y calendario.
   - Funcionamiento: Se entrena exclusivamente con datos pre-ZBE (2022 a junio 2024) y predice la serie horaria contrafactual (lo que habría ocurrido sin la ZBE).
   - Resultado: Reducción neta atribuible de **-2,87 µg/m³ (-11,6%)** en el periodo post-ZBE.
2. Contraste de Robustez Metodológica (Módulo SBD / Econometría Causal):
   - **Diferencias en Diferencias (Diff-in-Diff / DiD)**: Modelo cuasiexperimental sobre 41.700 horas en 8 estaciones oficiales.
   - Resultado Neto Atribuible: Reducción neta de **-1,63 µg/m³ (-6,4%)** en NO2 (IC 95%: -1,87 a -1,39 µg/m³, p < 0,001).
   - Comparativa: Dentro de la ZBE (Mazarredo y Mª Díaz de Haro) el NO2 bajó de 25,50 a 21,90 µg/m³ (-14,1%). Fuera en control metropolitano (Europa, Barakaldo, Basauri, Erandio, Castrejana) bajó de 18,25 a 16,29 µg/m³ (-10,8%). La diferencia neta (-1,63 µg/m³) aísla el efecto real de la ZBE.
3. Convergencia y Validación:
   - Ambos modelos convergen en que la ZBE reduce de forma neta el contaminante (-1,63 µg/m³ en DiD y -2,87 µg/m³ en Gradient Boosting), descartando que sea un artefacto metodológico.
   - Validación triple de placebos: SO2 (variación neta +0,33 µg/m³, confirmando especificidad del tráfico), control exterior y fecha de implantación falsa.
   - En calma (<2 m/s), el NO2 bajó un -13,4% dentro de la ZBE. Regresión con controles meteorológicos: -1,74 µg/m³.
4. Aforos de Tráfico: San Mamés cayó un -10,1% en 2024 con rebote a -3,2% en 2025.
5. Equipo: Alfred Gabriel (Product Owner), Iñigo Guzmán (Lead Data Engineer), Kerman Latorre (Scrum Master).
6. Stack: InfluxDB 2.9, Node-RED 5.0, Grafana 11.2 (RBAC), Servidor MCP InfluxDB (:5001), FastAPI (:8000).

DIRECTRICES:
- Si el usuario te pregunta por valores actuales, mediciones recientes o datos en directo de estaciones, meteorología o tráfico, USA SIEMPRE tus herramientas de InfluxDB.
- Si te preguntan por el modelo propuesto, aclara que el modelo de IA elegido para el entregable de MIA es Gradient Boosting (contrafactual no lineal ejecutado en el notebook), y que Diferencias en Diferencias es el contraste econométrico de robustez.
- Razona y explica el contexto de las cifras de forma analítica, estructurada y en español."""

# ── Herramientas Function Calling para Gemini ──────────────────────────────────
GEMINI_TOOLS = [
    {
        "function_declarations": [
            {
                "name": "consultar_influx_mcp",
                "description": "Ejecuta una consulta Flux personalizada de solo lectura en InfluxDB mediante MCP sobre los buckets aire_demo, aire, meteo o trafico.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "query": {
                            "type": "STRING",
                            "description": "Consulta Flux para InfluxDB (ej: from(bucket: \"aire_demo\") |> range(start: -1h) |> filter(fn: (r) => r._measurement == \"contaminantes\") |> group(columns: [\"estacion\", \"zona\"]) |> last())"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "obtener_calidad_aire_tiempo_real",
                "description": "Obtiene los últimos datos reales de NO2 registrados en las estaciones de Bilbao (Mazarredo, Mª Díaz de Haro, Europa, Arraiz) desde el bucket aire_demo.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "estacion": {
                            "type": "STRING",
                            "description": "Opcional: nombre de la estación ('Mazarredo', 'Mª Díaz de Haro', 'Europa', 'Arraiz') o vacío para todas."
                        }
                    }
                }
            },
            {
                "name": "obtener_meteorologia_tiempo_real",
                "description": "Obtiene los últimos datos meteorológicos de Bilbao (temperatura, velocidad del viento, lluvia y humedad) desde el bucket meteo.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {}
                }
            },
            {
                "name": "obtener_estado_trafico_tiempo_real",
                "description": "Obtiene las métricas recientes de aforo y ocupación vehicular en los accesos de Bilbao desde el bucket trafico.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {}
                }
            },
            {
                "name": "listar_buckets_influx",
                "description": "Lista los buckets disponibles en InfluxDB y su política de retención.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {}
                }
            }
        ]
    }
]

# ── Ejecutor de Consultas Flux en InfluxDB ─────────────────────────────────────
async def ejecutar_consulta_flux(query: str) -> str:
    """Envía una consulta Flux a InfluxDB usando el token MCP de solo lectura."""
    token = obtener_token_mcp()
    if not token:
        return "Error: Token MCP de InfluxDB no disponible en el sistema."
    url = f"{INFLUXDB_URL}/api/v2/query?org={INFLUXDB_ORG}"
    headers = {
        "Authorization": f"Token {token}",
        "Accept": "application/csv",
        "Content-Type": "application/vnd.flux"
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, headers=headers, content=query)
            if resp.status_code == 200:
                lineas = [l for l in resp.text.strip().split("\n") if not l.startswith("#") and l.strip()]
                if not lineas:
                    return "Sin registros en el rango de tiempo consultado."
                return "\n".join(lineas[:20])
            return f"Error en InfluxDB ({resp.status_code}): {resp.text[:200]}"
    except Exception as e:
        return f"Error al conectar con InfluxDB: {e}"

async def despachar_herramienta(name: str, args: dict) -> str:
    """Ejecuta la función solicitada por Gemini llamando a InfluxDB."""
    if name == "consultar_influx_mcp":
        return await ejecutar_consulta_flux(args.get("query", ""))
    elif name == "obtener_calidad_aire_tiempo_real":
        estacion = args.get("estacion")
        filtro_est = f' |> filter(fn: (r) => r.estacion == "{estacion}")' if estacion else ""
        q = (
            f'from(bucket: "aire_demo")\n'
            f'  |> range(start: -2h)\n'
            f'  |> filter(fn: (r) => r._measurement == "contaminantes")\n'
            f'  |> filter(fn: (r) => r._field == "no2"){filtro_est}\n'
            f'  |> group(columns: ["estacion", "zona"])\n'
            f'  |> last()'
        )
        return await ejecutar_consulta_flux(q)
    elif name == "obtener_meteorologia_tiempo_real":
        q = (
            'from(bucket: "meteo")\n'
            '  |> range(start: -2h)\n'
            '  |> filter(fn: (r) => r._measurement == "clima")\n'
            '  |> group(columns: ["_field"])\n'
            '  |> last()'
        )
        return await ejecutar_consulta_flux(q)
    elif name == "obtener_estado_trafico_tiempo_real":
        q = (
            'from(bucket: "trafico")\n'
            '  |> range(start: -30m)\n'
            '  |> filter(fn: (r) => r._measurement == "estado")\n'
            '  |> group(columns: ["_field"])\n'
            '  |> mean()'
        )
        return await ejecutar_consulta_flux(q)
    elif name == "listar_buckets_influx":
        return (
            "Buckets en InfluxDB:\n"
            "- aire_demo: Streaming en tiempo real de NO2 para demostración (retención: 7 días)\n"
            "- meteo: Ingesta meteorológica continua cada 15 min de Open-Meteo (retención: infinita)\n"
            "- trafico: Ingesta de aforo vehicular cada 5 min de Open Data Bilbao (retención: 30 días)\n"
            "- aire: Histórico oficial consolidado 2022-2026 de 8 estaciones (retención: infinita)"
        )
    return f"Herramienta no reconocida: {name}"

# ── Modelos de Datos (Pydantic) ────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: Optional[str] = None
    mensaje: Optional[str] = None
    history: Optional[List[Dict[str, Any]]] = None

class ChatResponse(BaseModel):
    respuesta: str
    fuentes: List[str]
    modelo: str

# ── Fallback Local de Contingencia ─────────────────────────────────────────────
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
        "4. **Servidor MCP:** Servicio de solo lectura (:5001) para conectar herramientas de IA a InfluxDB."
    ),
    "modelo_propuesto": (
        "En el proyecto HaizeLab se articulan dos enfoques metodológicos complementarios, ambos implementados y calculados con datos reales:\n\n"
        "1. **Modelo de IA Propuesto y Elegido (Módulo MIA):**\n"
        "Se seleccionó formalmente **Gradient Boosting** (`HistGradientBoostingRegressor`) como el modelo central de Machine Learning "
        "para estimar el contrafactual de NO₂. Modela de forma no lineal la interacción entre meteorología (viento, lluvia, temperatura, humedad) "
        "y calendario. **Está implementado y ejecutado en el notebook** (`notebooks/zbe_bilbao.ipynb`, celdas 18 y 19), donde entrenado en pre-ZBE "
        "predice el NO₂ post-ZBE y arroja una reducción neta de **-2,87 µg/m³ (-11,6%)**.\n\n"
        "2. **Contraste de Robustez Metodológica (Módulo SBD / Econometría Causal):**\n"
        "Se utiliza **Diferencias en Diferencias (Diff-in-Diff / DiD)** con 41.700 horas en 8 estaciones oficiales frente al control metropolitano, "
        "arrojando una reducción neta atribuible de **-1,63 µg/m³ (-6,4%)** (IC 95%: -1,87 a -1,39 µg/m³, p < 0,001).\n\n"
        "Ambos modelos convergen en que la ZBE genera un impacto positivo y real en el aire de Bilbao, respaldado por tres controles placebo."
    ),
    "equipo": (
        "El equipo de HaizeLab (Reto 0) está formado por tres especialistas:\n"
        "- **Alfred Gabriel:** Product Owner / Sistemas de Big Data & Modelado (pipeline reproducible de datos 332k filas, econometría Diff-in-Diff e informe).\n"
        "- **Iñigo Guzmán:** Lead Data Engineer / Big Data Aplicado (infraestructura Docker, InfluxDB, Node-RED, Grafana RBAC y alertas).\n"
        "- **Kerman Latorre:** Scrum Master / Modelos de IA & Protocolos (servidor MCP, integración de herramientas IA y metodología ágil Scrum)."
    ),
    "general": (
        "Soy HaizeLab Assistant. Puedo razonar y responder a tus preguntas sobre los resultados de la ZBE de Bilbao, "
        "el modelo de Machine Learning propuesto (Gradient Boosting vs Diff-in-Diff), datos en vivo en InfluxDB mediante MCP, métricas de tráfico o arquitectura."
    )
}

def responder_localmente(pregunta: str) -> str:
    p = pregunta.lower()
    if any(k in p for k in ["modelo", "propuesta", "propuesto", "gradient", "boosting", "mia", "machine learning", "algoritmo"]):
        return RESPUESTAS_LOCALES["modelo_propuesto"]
    elif any(k in p for k in ["estacion", "estaciones", "mazarredo", "maria diaz", "maría díaz"]):
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

# ── Motor de Razonamiento Gemini con Function Calling (MCP) ────────────────────
async def razonar_con_gemini(pregunta: str, historial: Optional[List[Dict[str, Any]]] = None) -> Tuple[Optional[str], List[str], str]:
    """
    Razonamiento dinámico con Google Gemini. Si Gemini decide consultar datos en vivo,
    ejecuta la herramienta de InfluxDB mediante MCP y le devuelve el resultado para la síntesis final.
    Soporta múltiples turnos de llamadas a herramientas (Multi-turn Function Calling).
    """
    if not GEMINI_API_KEY:
        return None, [], ""

    # Modelos activos en la API con soporte verificado de Function Calling
    modelos = [
        "gemini-3.1-flash-lite",
        "gemini-3.5-flash-lite",
        "gemini-3-flash-preview",
        "gemini-3.8-flash"
    ]
    base_contents: List[Dict[str, Any]] = [
        {"role": "user", "parts": [{"text": f"{SYSTEM_PROMPT}\n\nPregunta del usuario:\n{pregunta}"}]}
    ]

    async with httpx.AsyncClient(timeout=25.0) as client:
        for mod in modelos:
            contents = [dict(c) for c in base_contents]
            usado_mcp = False
            try:
                for _ in range(5):  # Hasta 5 llamadas a herramientas consecutivas
                    payload = {
                        "contents": contents,
                        "tools": GEMINI_TOOLS,
                        "generationConfig": {"temperature": 0.25, "maxOutputTokens": 800}
                    }
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{mod}:generateContent?key={GEMINI_API_KEY}"
                    resp = await client.post(url, json=payload)
                    if resp.status_code != 200:
                        break
                    data = resp.json()
                    cands = data.get("candidates", [])
                    if not cands:
                        break

                    candidate_content = cands[0].get("content", {})
                    parts = candidate_content.get("parts", [])
                    fn_part = next((p for p in parts if "functionCall" in p), None)

                    if fn_part:
                        usado_mcp = True
                        fn_name = fn_part["functionCall"]["name"]
                        fn_args = fn_part["functionCall"].get("args", {})
                        resultado_herramienta = await despachar_herramienta(fn_name, fn_args)

                        # Enviar el resultado de la función como rol 'tool'
                        contents.append(candidate_content)
                        contents.append({
                            "role": "tool",
                            "parts": [{
                                "functionResponse": {
                                    "name": fn_name,
                                    "response": {"resultado": resultado_herramienta}
                                }
                            }]
                        })
                        continue

                    # Si no hay más llamadas a herramientas, extraer texto final
                    textos = [p["text"].strip() for p in parts if "text" in p and p.get("text", "").strip()]
                    if textos:
                        texto_final = "\n\n".join(textos)
                        if usado_mcp:
                            return texto_final, ["InfluxDB (Servidor MCP)", "Google Gemini", "Evidencia HaizeLab"], "Google Gemini + MCP InfluxDB"
                        else:
                            return texto_final, ["Google Gemini", "Evidencia HaizeLab"], "Google Gemini (IA Generativa)"
                    break
            except Exception:
                continue

    return None, [], ""

# ── Endpoints HTTP ─────────────────────────────────────────────────────────────
@app.get("/health")
@app.get("/info")
def health():
    token_mcp = bool(obtener_token_mcp())
    return {
        "status": "ok",
        "servicio": "haizelab-chatbot",
        "razonamiento_gemini": bool(GEMINI_API_KEY),
        "mcp_disponible": token_mcp,
        "modo": "Google Gemini + MCP InfluxDB" if (GEMINI_API_KEY and token_mcp) else ("Google Gemini (Nube)" if GEMINI_API_KEY else "Knowledge Engine (Local Autónomo)")
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

    # 1. Intentar razonamiento con Gemini + MCP InfluxDB
    texto_gemini, fuentes, modelo = await razonar_con_gemini(pregunta, peticion.history)
    if texto_gemini:
        return ChatResponse(
            respuesta=texto_gemini,
            fuentes=fuentes,
            modelo=modelo
        )

    # 2. Fallback seguro desde la base de conocimiento local
    resp_fija = responder_localmente(pregunta)
    return ChatResponse(
        respuesta=resp_fija,
        fuentes=["knowledge_base.json", "Informe ZBE Bilbao"],
        modelo="HaizeLab Knowledge Engine (Local Autónomo)"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
