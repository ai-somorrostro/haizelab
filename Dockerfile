# ── Build stage ──────────────────────────────────────────────────────────────
FROM python:3.11-slim AS base

LABEL maintainer="haizelab"
LABEL description="Analisis NO2 ZBE Bilbao"

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

# Copiar scripts
COPY analisis.py .
COPY visualizar.py .

# La carpeta de datos se monta como volumen en tiempo de ejecucion
# salida/ tambien se monta para recuperar los resultados
VOLUME ["/app/datos", "/app/salida"]

# Por defecto ejecuta el pipeline completo
CMD ["python", "analisis.py"]
