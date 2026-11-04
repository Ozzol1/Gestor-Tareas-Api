FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Ya no necesitamos instalar libpq-dev ni gcc
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x entrypoint.sh
RUN useradd --create-home appuser
USER appuser

EXPOSE 5000

CMD ["./entrypoint.sh"]