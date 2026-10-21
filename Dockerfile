# ── Build stage ──────────────────────────────────────────────────────────────
FROM python:3.11.17-slim AS base

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

# Copiar ingesta, notebooks y documentacion
COPY ingesta/ ./ingesta/
COPY notebooks/ ./notebooks/
COPY docs/ ./docs/

# Las carpetas de datos e imagenes se montan como volumenes en ejecucion
VOLUME ["/app/data", "/app/docs/img"]

# Por defecto ejecuta la descarga, limpieza e integracion de datos
CMD ["python", "ingesta/descargar_y_limpiar.py"]
