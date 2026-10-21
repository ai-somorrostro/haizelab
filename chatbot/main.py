#!/usr/bin/env python3
"""
haizelab/chatbot/main.py
========================
Servidor API REST para HaizeLab Assistant con integración MCP a InfluxDB.
Tecnología: FastAPI + Pydantic + HTTPX.

Arquitectura de Razonamiento:
1. Conecta con el servidor InfluxDB mediante el token de solo lectura (mismo que el servidor MCP).
2. Expone herramientas analíticas (Function Calling) a Google Gemini para consultar en tiempo real:
   - Calidad del aire (NO2 en Mazarredo, Mª Díaz de Haro, Europa, Arraiz).
   - Meteorología (temperatura, viento, lluvia).
   - Aforos e intensidades de tráfico.
   - Consultas Flux personalizadas de solo lectura.
3. Las cifras del análisis se leen de resultados/resultados.json, que escribe el notebook.
4. Si no hay clave de API o falla la conexión, responde con textos generados a partir de esas cifras.
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

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
INFLUXDB_URL = os.environ.get("INFLUXDB_URL", "http://influxdb:8086").rstrip("/")
INFLUXDB_ORG = os.environ.get("INFLUXDB_ORG", "haizenlab")
MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://influx-mcp:5001/mcp/").rstrip("/")

app = FastAPI(
    title="HaizeLab Assistant API",
    description="Asistente con razonamiento y acceso a InfluxDB MCP para la evaluación de la ZBE de Bilbao",
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

# ── Cifras del análisis y prompt de razonamiento ───────────────────────────────
# Todas las cifras salen de resultados/resultados.json, que escribe el notebook.
# Aquí no se escribe ninguna a mano: si el fichero no está, el asistente lo dice.
RUTA_RESULTADOS = Path(os.environ.get("RESULTADOS_JSON", DIR_CHATBOT.parent / "resultados" / "resultados.json"))

try:
    RESULTADOS = json.loads(RUTA_RESULTADOS.read_text(encoding="utf-8"))
except Exception:
    RESULTADOS = None


def es(x: float, dec: int = 2) -> str:
    """Número con coma decimal, punto de miles y signo menos tipográfico."""
    return f"{x:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".").replace("-", "−")


def con_intervalo(r: Dict[str, float], clave: str = "efecto_neto") -> str:
    """Cifra con su intervalo del 95 % y si incluye o no el cero."""
    cero = "incluye el cero" if r["ic95_inf"] <= 0 <= r["ic95_sup"] else "no incluye el cero"
    return f"{es(r[clave])} µg/m³ (intervalo del 95 %: de {es(r['ic95_inf'])} a {es(r['ic95_sup'])}; {cero})"


def fecha(iso: str) -> str:
    a, m, d = iso.split("-")
    return f"{d}/{m}/{a}"


def textos_resultados(R: Dict[str, Any]) -> Dict[str, str]:
    """Textos del asistente generados a partir de resultados.json."""
    per, cal = R["periodo_estudio"], R["calidad_datos"]
    p1, p2, p3, p4, p5 = R["p1_did"], R["p2_horario"], R["p3_calma"], R["p4_so2"], R["p5_fases"]
    ia = R["modelo_ia"]
    mae = ia["metricas"][ia["modelo_elegido"]]["mae_val"]
    mae_base = ia["metricas"]["Base: media por hora y mes (sin IA)"]["mae_val"]
    p2_en = {"efecto_neto": p2["efecto_neto_en_horario_zbe"],
             "ic95_inf": p2["ic95_en_horario_zbe"][0], "ic95_sup": p2["ic95_en_horario_zbe"][1]}
    p2_fuera = {"efecto_neto": p2["efecto_neto_fuera_horario"],
                "ic95_inf": p2["ic95_fuera_horario"][0], "ic95_sup": p2["ic95_fuera_horario"][1]}
    return {
        "datos": (
            f"El análisis usa {es(cal['filas_en_periodo'], 0)} horas-estación de NO₂ y SO₂ de 8 estaciones, "
            f"del {fecha(per['fecha_inicio'])} al {fecha(per['fecha_fin'])}. Hay dato de NO₂ en el "
            f"{es(cal['completitud_no2_total_pct'])} % de las horas.\n"
            "- Dentro de la ZBE: Mazarredo y Mª Díaz de Haro.\n"
            "- Control (fuera de la ZBE): Europa, Barakaldo, Basauri, Erandio y Castrejana.\n"
            "- Fondo (lejos del tráfico, solo como referencia): Arraiz.\n"
            "Fuentes: calidad del aire del Gobierno Vasco (Open Data Euskadi), meteorología de Open-Meteo "
            "y el calendario de la ZBE con los festivos."
        ),
        "resultado_zbe": (
            f"Dentro de la ZBE el NO₂ medio pasó de {es(p1['dentro_pre'])} a {es(p1['dentro_post'])} µg/m³ "
            f"({es(p1['caida_bruta_dentro'])}). Fuera, sin ZBE, pasó de {es(p1['fuera_pre'])} a "
            f"{es(p1['fuera_post'])} ({es(p1['caida_bruta_fuera'])}).\n\n"
            f"El **efecto neto** (lo que bajó dentro menos lo que bajó fuera) es "
            f"**{con_intervalo(p1, 'efecto_neto_did')}**. Es el método de diferencias en diferencias, "
            "un método estadístico, no inteligencia artificial."
        ),
        "pruebas": (
            f"- Horario: efecto neto de {con_intervalo(p2_en)} con la ZBE activa y de "
            f"{con_intervalo(p2_fuera)} fuera de horario.\n"
            f"- Viento en calma (menos de 2 m/s): {con_intervalo(p3)}.\n"
            f"- SO₂, que no viene del tráfico: {con_intervalo(p4)}.\n"
            f"- Fase 1 frente a antes: {con_intervalo(p5['fase1_vs_previo'])}. "
            f"Fase 2 frente a fase 1: {con_intervalo(p5['fase2_vs_fase1'])}."
        ),
        "modelo": (
            f"El modelo de IA es **{ia['modelo_elegido']}**, elegido entre regresión lineal, Random Forest y "
            "Gradient Boosting por tener el menor error en un periodo que no vio al entrenar "
            f"(MAE de {es(mae)} µg/m³ por hora; el modelo base sin IA, {es(mae_base)}). Aprende con los datos de "
            "antes de la ZBE qué NO₂ hay según el tiempo atmosférico y el calendario, y predice lo que habría "
            "habido sin ZBE.\n\n"
            f"Efecto de la ZBE con el modelo (dentro menos fuera): {con_intervalo(ia['efecto'])}. "
            f"Con una ZBE ficticia el 15/06/2023 sale {con_intervalo(ia['placebo_15_06_2023'])}. "
            f"Con diferencias en diferencias, el efecto es {es(p1['efecto_neto_did'])} µg/m³: los dos métodos "
            "dan una bajada, pero de distinto tamaño, así que el tamaño exacto se da con cautela."
        ),
    }


TEXTOS = textos_resultados(RESULTADOS) if RESULTADOS else {}
SIN_CIFRAS = f"No encuentro las cifras del análisis ({RUTA_RESULTADOS}). Hay que ejecutar el notebook."

SYSTEM_PROMPT = f"""Eres HaizeLab Assistant, el asistente de la evaluación de la Zona de Bajas Emisiones (ZBE) de Bilbao para el Ayuntamiento, que tiene que decidir si amplía, mantiene o ajusta la ZBE.

DATOS EN DIRECTO (InfluxDB, solo lectura):
- Bucket `aire_demo`: NO₂ histórico reproducido deprisa (una hora cada 5 s) en 4 estaciones. No es el aire de ahora.
- Bucket `meteo`: meteorología de Open-Meteo, cada 15 min.
- Bucket `trafico`: estado del tráfico de Bilbao, cada 5 min.
- Bucket `aire`: histórico oficial de calidad del aire de 8 estaciones.

RESULTADOS DEL ANÁLISIS (salen de resultados/resultados.json):
{TEXTOS.get("datos", SIN_CIFRAS)}

{TEXTOS.get("resultado_zbe", "")}

Comprobaciones:
{TEXTOS.get("pruebas", "")}

Modelo de IA:
{TEXTOS.get("modelo", "")}

DIRECTRICES:
- Para valores actuales o recientes de estaciones, meteorología o tráfico, usa tus herramientas de InfluxDB.
- Usa solo las cifras de arriba. No inventes cifras ni menciones técnicas que no estén aquí.
- Diferencias en diferencias es un método estadístico, no IA. Node-RED es automatización, no IA.
- El análisis no usa los aforos de tráfico; el tráfico solo se muestra en directo en Grafana.
- Responde en español, en lenguaje llano, y define cada término técnico la primera vez."""

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
    "resultado_zbe": TEXTOS.get("resultado_zbe", SIN_CIFRAS),
    "pruebas": TEXTOS.get("pruebas", SIN_CIFRAS),
    "datos": TEXTOS.get("datos", SIN_CIFRAS),
    "modelo_propuesto": TEXTOS.get("modelo", SIN_CIFRAS),
    "trafico": (
        "El análisis de la ZBE no usa los aforos de tráfico: responde con la calidad del aire. "
        "El tráfico de Bilbao se recoge cada 5 minutos en el bucket `trafico` y se ve en directo en Grafana."
    ),
    "infraestructura": (
        "La plataforma se arranca con Docker Compose:\n"
        "1. **InfluxDB 2.9:** base de datos de series temporales con 4 buckets y un token con el permiso mínimo para cada servicio.\n"
        "2. **Node-RED:** automatización que consulta la meteorología cada 15 min y el tráfico cada 5 min y los escribe en InfluxDB. No es IA.\n"
        "3. **Grafana 11.2:** paneles, alertas y permisos por equipo (Dirección, Análisis e IT).\n"
        "4. **Servidor MCP:** consultas de solo lectura a InfluxDB desde un asistente (:5001)."
    ),
    "equipo": (
        "El equipo de HaizeLab:\n"
        "- **Alfred Gabriel:** Product Owner · Relación con el cliente y desarrollo.\n"
        "- **Iñigo Guzmán:** Lead Data Engineer · Datos e infraestructura.\n"
        "- **Kerman Latorre:** Scrum Master · Análisis y modelado."
    ),
    "general": (
        "Soy HaizeLab Assistant. Puedo responder sobre el efecto de la ZBE de Bilbao en el NO₂, las comprobaciones "
        "(horario, calma, SO₂ y fases), el modelo de IA, los datos usados y la plataforma."
    )
}

def responder_localmente(pregunta: str) -> str:
    p = pregunta.lower()
    if any(k in p for k in ["modelo", "propuesta", "propuesto", "random forest", "gradient", "boosting", "machine learning", "algoritmo", "inteligencia artificial"]):
        return RESPUESTAS_LOCALES["modelo_propuesto"]
    elif any(k in p for k in ["estacion", "estaciones", "mazarredo", "maria diaz", "maría díaz"]):
        return RESPUESTAS_LOCALES["datos"]
    elif any(k in p for k in ["docker", "influx", "grafana", "node-red", "nodered", "mcp", "arquitectura", "infraestructura", "base de datos", "monitorizaci"]):
        return RESPUESTAS_LOCALES["infraestructura"]
    elif any(k in p for k in ["trafico", "tráfico", "coche", "san mames", "san mamés", "aforo", "vehiculo"]):
        return RESPUESTAS_LOCALES["trafico"]
    elif any(k in p for k in ["equipo", "autor", "quien", "quién", "iñigo", "kerman", "alfred"]):
        return RESPUESTAS_LOCALES["equipo"]
    elif any(k in p for k in ["placebo", "so2", "so₂", "calma", "viento", "horario", "fase", "comprobaci", "intervalo"]):
        return RESPUESTAS_LOCALES["pruebas"]
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
        "modo": "Google Gemini + MCP InfluxDB" if (GEMINI_API_KEY and token_mcp) else ("Google Gemini (Nube)" if GEMINI_API_KEY else "Respuestas locales (resultados.json)")
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
        fuentes=["resultados/resultados.json"],
        modelo="Respuestas locales (resultados.json)"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
