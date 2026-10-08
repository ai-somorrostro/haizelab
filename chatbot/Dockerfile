# Imagen base ligera de Python
FROM python:3.11-slim

# Evitar escritura de bytecode y habilitar buffer inmediato en stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias del sistema y de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar artefactos y código del chatbot
COPY knowledge_base.json .
COPY rag_engine.py .
COPY main.py .

# Puerto de exposición
EXPOSE 8000

# Arranque del servidor uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
