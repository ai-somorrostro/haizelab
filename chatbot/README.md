# HaizeLab Assistant — Chatbot con Razonamiento (Reto 0)

Microservicio API REST en **FastAPI** que implementa un asistente inteligente explicable para responder y razonar sobre la evaluación de la Zona de Bajas Emisiones (ZBE) de Bilbao (2022-2026).

---

## 🎯 Arquitectura y Razonamiento

El asistente está diseñado con un patrón RAG elemental y explicable:

1. **Evidencia Empírica Oficial (`knowledge_base.json`):** Contiene los resultados del análisis (Diff-in-Diff -1,63 µg/m³, estaciones dentro y fuera, tráfico en San Mamés, controles de viento y placebo de SO₂).
2. **System Prompt de Razonamiento:** Inyecta esta evidencia en el modelo para que razone argumentos y responda hipótesis (*«¿Por qué el SO₂ actúa como placebo?»*, *«¿Ha funcionado la ZBE y en qué medida?»*) ciñéndose a los datos del proyecto.
3. **Modo Offline de Seguridad:** Si no hay ningún motor de IA activo, devuelve respuestas técnicas exactas desde la base de conocimiento para no fallar en el aula.

---

## 🚀 Modos de Funcionamiento

El chatbot opera bajo dos modalidades complementarias:

### 1. Modo Autónomo y Explicable (Por Defecto · Sin Configuración)
Funciona de inmediato sin necesidad de conexión a internet ni claves de API externas. Utiliza la base de conocimiento estructurada (`knowledge_base.json`) para responder con los datos y métricas oficiales del proyecto con tiempo de respuesta instantáneo y reproducibilidad garantizada.

### 2. Modo Razonamiento con Google Gemini (Opcional · En la Nube)
Si se desea razonamiento dinámico profundo y argumentación avanzada:
1. Obtén una clave gratuita en [Google AI Studio](https://aistudio.google.com/) (con cuenta de Google, sin coste).
2. Añade tu clave en el archivo `.env`:
   ```env
   GEMINI_API_KEY=AIzaSy_tu_clave_aqui
   ```
3. Reinicia el servicio:
   ```bash
   docker compose up -d chatbot
   ```
4. El asistente utilizará **Google Gemini 2.0 Flash** para razonar en directo.

---

## 🌐 Uso y Documentación

* **Presentación web con Chatbot embebido:** [http://localhost:8080](http://localhost:8080)
* **Documentación interactiva de la API (Swagger UI):** [http://localhost:8000/docs](http://localhost:8000/docs)
* **Comprobación de salud:**
  ```bash
  curl http://localhost:8000/health
  ```

