# Usamos una imagen base oficial de Python
FROM python:3.11-slim

# Establecemos el directorio de trabajo
WORKDIR /app

# ⬇️ ESTO ES CLAVE: Instalamos las dependencias del sistema para psycopg2
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# Copiamos e instalamos las dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del código
COPY . .

# Damos permisos al script de arranque y cambiamos a un usuario no-root por seguridad
RUN chmod +x entrypoint.sh
RUN useradd --create-home appuser
USER appuser

# Exponemos el puerto (aunque Render usa el de la variable PORT)
EXPOSE 5000

# Comando de arranque
CMD ["./entrypoint.sh"]