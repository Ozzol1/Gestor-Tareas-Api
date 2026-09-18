"""
Script de migración: lee el archivo tareas.json (del Proyecto 1)
y lo inserta en la base de datos SQLite de la API.

Uso:
    py migrar_json.py ruta/al/tareas.json

Si no se pasa ruta, busca 'tareas.json' en la carpeta actual.
"""
import json
import os
import sys
from datetime import datetime

from app import create_app, db
from app.models import Tarea


def migrar(ruta_json):
    if not os.path.exists(ruta_json):
        print(f"❌ No se encontró el archivo: {ruta_json}")
        print("   No hay nada que migrar. La base de datos queda como está.")
        return

    print(f"📂 Leyendo {ruta_json}...")
    try:
        with open(ruta_json, "r", encoding="utf-8") as f:
            datos = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"❌ El archivo JSON está corrupto: {e}")
        return

    # Soportar formato nuevo (dict con "tareas") y antiguo (lista directa)
    if isinstance(datos, dict):
        lista_tareas = datos.get("tareas", [])
    elif isinstance(datos, list):
        lista_tareas = datos
    else:
        print("❌ Formato de JSON no reconocido.")
        return

    if not lista_tareas:
        print("📭 El archivo no contiene tareas. Nada que migrar.")
        return

    print(f"📋 Se encontraron {len(lista_tareas)} tarea(s) para migrar.")

    app = create_app()
    with app.app_context():
        migradas = 0
        omitidas = 0
        for t in lista_tareas:
            titulo = (t.get("titulo") or "").strip()
            if not titulo:
                omitidas += 1
                continue  # Saltamos las que no tienen título válido

            nueva = Tarea(
                titulo=titulo,
                descripcion=t.get("descripcion"),
                completada=bool(t.get("completada", False)),
                prioridad=t.get("prioridad", "media"),
                fecha_limite=t.get("fecha_limite"),
            )
            db.session.add(nueva)
            migradas += 1

        db.session.commit()

    print(f"✅ Migración completada:")
    print(f"   - {migradas} tarea(s) insertada(s).")
    if omitidas:
        print(f"   - {omitidas} tarea(s) omitida(s) (sin título válido).")


if __name__ == "__main__":
    ruta = sys.argv[1] if len(sys.argv) > 1 else "tareas.json"
    migrar(ruta)