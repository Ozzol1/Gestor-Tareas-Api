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

# Dar permisos de ejecución al entrypoint antes de cambiar de usuario
RUN chmod +x entrypoint.sh

USER appuser

EXPOSE 5000

CMD ["./entrypoint.sh"]