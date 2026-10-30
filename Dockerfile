# ====================================================
# STAGE 1: BUILDER (Instalamos dependencias)
# ====================================================
FROM python:3.11-slim AS builder

WORKDIR /app

# Instalamos gcc y libpq-dev para asegurar que psycopg2 compile si lo necesita
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --user -r requirements.txt


# ====================================================
# STAGE 2: RUNTIME (Imagen final, ligera)
# ====================================================
FROM python:3.11-slim

# Instalamos libpq5, que es la librería que necesita psycopg2 para conectarse a PostgreSQL
RUN apt-get update && apt-get install -y libpq5 && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/home/appuser/.local/bin:$PATH

RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Copiamos las dependencias instaladas del stage anterior
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

# Copiamos el código de la app
COPY --chown=appuser:appuser . .

# Dar permisos de ejecución al entrypoint ANTES de cambiar de usuario
RUN chmod +x entrypoint.sh

USER appuser

EXPOSE 5000

CMD ["./entrypoint.sh"]