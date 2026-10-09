# HaizeLab Assistant — Chatbot RAG (Reto 0)

Microservicio API REST en **FastAPI** que implementa un asistente inteligente con **RAG** (Retrieval-Augmented Generation) sobre los datos empíricos de la Zona de Bajas Emisiones de Bilbao (2022-2026).

---

## 🎯 Objetivo y Filosofía

El asistente está diseñado para defender las conclusiones técnicas del proyecto y responder a cualquier duda sobre calidad del aire, meteorología, tráfico, stack tecnológico y autoría con **cero alucinaciones**.

### Tres Niveles de Razonamiento Adaptativo

El motor [`chatbot/rag_engine.py`](rag_engine.py) evalúa automáticamente la infraestructura disponible y selecciona el mejor proveedor en este orden:

| Nivel | Proveedor | Requisitos | Características |
|---|---|---|---|
| **1. Motor Analítico** *(Predeterminado)* | `haizelab-analytical-engine` | Ninguno (activo por defecto en Docker) | Respuestas exactas y deterministas calculadas a partir de `knowledge_base.json`. No requiere internet, no requiere GPU ni claves. Ideal para evaluaciones sin conexión. |
| **2. Razonamiento Local** | `ollama/qwen2.5:1.5b` | Ollama instalado y corriendo en el host | Razonamiento libre y generación de lenguaje natural 100 % privada y local mediante `host.docker.internal:11434`. |
| **3. Razonamiento Cloud** | `groq/llama-3.3-70b` o `google/gemini-2.0-flash` | `GROQ_API_KEY` o `GEMINI_API_KEY` en `.env` | Respuestas generadas en la nube en menos de 1 segundo sin consumir CPU ni memoria en el equipo. |

---

## 🚀 Puesta en Marcha

### Opción 1: Con Docker Compose (Recomendada)

El servicio se levanta junto con el resto de la plataforma:
```bash
docker compose up -d chatbot
```

Verificación de salud:
```bash
curl http://localhost:8000/health
```

### Opción 2: Cómo activar el razonamiento con Ollama en local

Si deseas que el chatbot genere lenguaje natural y razone libremente en tu propia máquina:

1. Instala Ollama en Windows:
   ```powershell
   winget install Ollama.Ollama
   ```
2. Descarga e inicia el modelo ligero recomendado:
   ```bash
   ollama run qwen2.5:1.5b
   ```
3. El contenedor detecta Ollama automáticamente a través del puerto `11434` del host.

### Opción 3: Cómo activar razonamiento Cloud (Groq / Gemini)

Si prefieres no instalar Ollama ni consumir recursos de tu ordenador:
1. Obtén una clave API gratuita en [Groq Console](https://console.groq.com/keys) o [Google AI Studio](https://aistudio.google.com/).
2. Añádela a tu fichero `.env`:
   ```env
   GROQ_API_KEY=gsk_tu_clave_aqui
   # o bien:
   GEMINI_API_KEY=AIzaSy_tu_clave_aqui
   ```
3. Reinicia el contenedor:
   ```bash
   docker compose restart chatbot
   ```

---

## 🛡️ Seguridad Defensiva y Gobernanza

El backend incorpora medidas estrictas de ciberseguridad defensiva:

1. **Filtro de Dominio / Anti Prompt Injection:** Bloquea jailbreaks ("olvida tus instrucciones", "dan mode"), intentos de extracción de credenciales, generación de código malicioso y preguntas ajenas al proyecto (cocina, política, cripto).
2. **Rate Limiting:** Límite en memoria de 25 peticiones por minuto por IP para prevenir ataques de denegación de servicio (DoS).
3. **CORS Universal:** Soporte seguro tanto para producción web como para apertura directa de la presentación en disco (`file:///` con `Origin: null`).
4. **Validación de Entradas:** Validación estricta de esquemas mediante Pydantic (máximo 500 caracteres por pregunta).

---

## 🧪 Batería de Pruebas Automatizadas

Se incluye una suite de pruebas que valida 18 preguntas críticas (econometría, tráfico, meteorología, autores, rechazo de prompt injection y temas fuera de dominio):

```bash
python chatbot/test_preguntas.py
```

*Resultado esperado: **18/18 PASS (100 % de éxito)**.*

---

## 📁 Estructura del Módulo

* [`main.py`](main.py): Servidor API REST en FastAPI con middleware CORS y control de tasa.
* [`rag_engine.py`](rag_engine.py): Motor RAG multietapa, filtros de seguridad y adaptadores a Ollama, Groq, Gemini y motor analítico.
* [`knowledge_base.json`](knowledge_base.json): Base de conocimiento vectorial y documental con métricas empíricas del proyecto.
* [`precomputar_conocimiento.py`](precomputar_conocimiento.py): Script generador que sincroniza las cifras del análisis en la base de conocimiento.
* [`test_preguntas.py`](test_preguntas.py): Suite de pruebas automatizadas con aserciones rigurosas.
* [`Dockerfile`](Dockerfile): Imagen contenerizada ligera basada en Python 3.11.
