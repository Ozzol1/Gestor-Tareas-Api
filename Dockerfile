FROM python:3.11-slim

# Evitar que Python escriba archivos .pyc y forzar logs en consola
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalamos las librerías del sistema que necesita psycopg2 y creamos un usuario seguro
RUN apt-get update && apt-get install -y libpq5 gcc libpq-dev && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash appuser

# Instalamos las dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el proyecto
COPY . .

# Damos permisos al script de arranque y cambiamos al usuario seguro
RUN chmod +x entrypoint.sh
USER appuser

EXPOSE 5000

CMD ["./entrypoint.sh"]