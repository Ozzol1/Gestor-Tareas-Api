# ====================================================
# STAGE 1: BUILDER
# ====================================================
FROM python:3.11-slim AS builder

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --user -r requirements.txt


# ====================================================
# STAGE 2: RUNTIME
# ====================================================
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/home/appuser/.local/bin:$PATH

RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 5000

# Shell form para permitir expansión de variables de entorno
CMD gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 2 --timeout 60 "app:create_app()"