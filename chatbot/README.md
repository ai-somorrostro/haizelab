# HaizeLab Assistant — Chatbot Local (Reto 0)

Microservicio API REST en **FastAPI** que implementa un asistente inteligente explicable para responder a preguntas técnicas sobre la Zona de Bajas Emisiones (ZBE) de Bilbao (2022-2026).

---

## 🎯 Arquitectura Explicable

El asistente está diseñado con un patrón sencillo y transparente:

1. **Base de Conocimiento Local (`knowledge_base.json`):** Contiene los resultados del análisis (Diff-in-Diff -1,63 µg/m³, estaciones dentro y fuera, tráfico en San Mamés y arquitectura técnica).
2. **Inyección de Contexto en Prompt:** Si hay un servidor de **Ollama** activo en el equipo (por defecto `qwen2.5:1.5b`), el chatbot inyecta el contexto en el prompt para que el modelo redacte una respuesta precisa sin alucinaciones.
3. **Modo Determinista Offline:** Si Ollama no está corriendo, la API selecciona y devuelve automáticamente la respuesta técnica consolidada desde la base de conocimiento local, garantizando que el servicio nunca falle.

---

## 🚀 Puesta en Marcha

### Con Docker Compose (Predeterminado)
El servicio se levanta automáticamente:
```bash
docker compose up -d chatbot
```

Comprobar salud:
```bash
curl http://localhost:8000/health
```

Documentación interactiva de la API (Swagger UI):
```
http://localhost:8000/docs
```

---

## 🧪 Pruebas Automatizadas

Para validar que el chatbot responde correctamente a las preguntas clave del proyecto:

```bash
python chatbot/test_preguntas.py
```
