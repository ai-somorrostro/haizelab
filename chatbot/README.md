# HaizeLab Assistant

API REST en **FastAPI** que responde preguntas sobre la evaluación de la Zona de Bajas Emisiones (ZBE) de Bilbao.

## De dónde salen las respuestas

- **Cifras del análisis:** se leen al arrancar de `resultados/resultados.json`, el fichero que escribe el notebook. En Docker Compose se monta en solo lectura en `/resultados`. Si cambia el análisis, basta con reiniciar el servicio. Si el fichero no está, el asistente lo dice en vez de dar cifras.
- **Datos en directo:** consultas de solo lectura a InfluxDB (calidad del aire de demostración, meteorología y tráfico), con el mismo token que el servidor MCP.

## Modos de funcionamiento

1. **Sin configuración (por defecto).** Responde con textos fijos generados a partir de `resultados.json`. No necesita internet ni claves.
2. **Con Google Gemini (opcional).** Si se define `GEMINI_API_KEY` en `.env`, Gemini redacta la respuesta con las cifras de `resultados.json` y puede consultar InfluxDB.
   ```env
   GEMINI_API_KEY=tu_clave
   ```
   ```bash
   docker compose up -d chatbot
   ```

## Uso

- Presentación web con el asistente: http://localhost:8080
- Documentación de la API: http://localhost:8000/docs
- Comprobación de estado: `curl http://localhost:8000/health`
