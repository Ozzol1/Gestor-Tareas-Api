#!/bin/bash
set -e

# Crear las tablas si no existen (una sola vez)
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all(); print('✅ Tablas creadas/verificadas')"

# Arrancar gunicorn (1 worker para evitar race condition)
exec gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 1 --timeout 60 "app:create_app()"