# ── Build stage ──────────────────────────────────────────────────────────────
FROM python:3.11-slim AS base

LABEL maintainer="haizelab"
LABEL description="Analisis Multivariable ZBE Bilbao"

WORKDIR /app

# Instalar dependencias del sistema para matplotlib (backend Agg, sin display)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libfreetype6 \
        libpng16-16 \
        fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias Python primero (cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar scripts, ingesta, notebooks y orquestador
COPY scripts/ ./scripts/
COPY ingesta/ ./ingesta/
COPY notebooks/ ./notebooks/
COPY docs/ ./docs/
COPY ejecutar_todo.py .

# Las carpetas de datos y salida se montan como volumenes en ejecucion
VOLUME ["/app/datos", "/app/salida", "/app/data", "/app/docs/img"]

# Por defecto ejecuta el pipeline completo
CMD ["python", "ejecutar_todo.py"]
