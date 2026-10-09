# HaizeLab Assistant — Chatbot con Razonamiento (Reto 0)

Microservicio API REST en **FastAPI** que implementa un asistente inteligente explicable para responder y razonar sobre la evaluación de la Zona de Bajas Emisiones (ZBE) de Bilbao (2022-2026).

---

## 🎯 Arquitectura y Razonamiento

El asistente está diseñado con un patrón RAG elemental y explicable:

1. **Evidencia Empírica Oficial (`knowledge_base.json`):** Contiene los resultados del análisis (Diff-in-Diff -1,63 µg/m³, estaciones dentro y fuera, tráfico en San Mamés, controles de viento y placebo de SO₂).
2. **System Prompt de Razonamiento:** Inyecta esta evidencia en el modelo para que razone argumentos y responda hipótesis (*«¿Por qué el SO₂ actúa como placebo?»*, *«¿Ha funcionado la ZBE y en qué medida?»*) ciñéndose a los datos del proyecto.
3. **Modo Offline de Seguridad:** Si no hay ningún motor de IA activo, devuelve respuestas técnicas exactas desde la base de conocimiento para no fallar en el aula.

---

## 🚀 Cómo Activar el Razonamiento con IA

El chatbot puede funcionar de dos formas:

### 1. Modo Razonamiento en la Nube con Google Gemini (Recomendado)
Es la opción más rápida y potente. No requiere instalar nada ni consume memoria de tu ordenador:

1. Entra en [Google AI Studio](https://aistudio.google.com/) y genera una clave API gratuita (con tu cuenta de Google, sin tarjeta).
2. En la raíz del proyecto, añade tu clave en el archivo `.env`:
   ```env
   GEMINI_API_KEY=AIzaSy_tu_clave_aqui
   ```
3. Reinicia el contenedor:
   ```bash
   docker compose up -d chatbot
   ```
4. El asistente utilizará **Gemini 2.0 Flash** para razonar en directo con alta velocidad.

### 2. Modo Razonamiento Local con Ollama (100% en tu máquina)
Si prefieres no usar internet ni claves:

1. Abre Ollama en tu ordenador y ejecuta el modelo ligero recomendado:
   ```bash
   ollama run qwen2.5:1.5b
   ```
2. El contenedor detecta Ollama automáticamente a través de `http://host.docker.internal:11434`.

### 3. Modo Offline (Sin configuración)
Si no defines `GEMINI_API_KEY` ni abres Ollama, el chatbot funciona de forma autónoma respondiendo directamente con la información oficial de `knowledge_base.json`.

---

## 🌐 Uso y Documentación

* **Presentación web con Chatbot embebido:** [http://localhost:8080](http://localhost:8080)
* **Documentación interactiva de la API (Swagger UI):** [http://localhost:8000/docs](http://localhost:8000/docs)
* **Comprobación de salud:**
  ```bash
  curl http://localhost:8000/health
  ```

---

## 🧪 Pruebas Automatizadas

Para validar que el chatbot responde correctamente a las preguntas clave del proyecto:

```bash
python chatbot/test_preguntas.py
```
