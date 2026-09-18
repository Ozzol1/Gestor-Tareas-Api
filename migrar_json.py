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
from app import create_app, db
from app.models import Tarea


def migrar(ruta_json):
    # 1. Manejo de FileNotFoundError
    if not os.path.exists(ruta_json):
        print(f"❌ ERROR: No se encontró el archivo '{ruta_json}'.")
        print("   Verifica la ruta e intenta de nuevo.")
        sys.exit(1)

    # 2. Manejo de JSONDecodeError
    try:
        with open(ruta_json, "r", encoding="utf-8") as f:
            datos = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ ERROR: El archivo JSON está corrupto o mal formado.")
        print(f"   Detalle: {e}")
        sys.exit(1)
    except UnicodeDecodeError:
        print("❌ ERROR: El archivo no está en UTF-8.")
        sys.exit(1)

    # 3. Soportar formato dict {"tareas": [...]} y lista directa [...]
    if isinstance(datos, dict):
        lista_tareas = datos.get("tareas", [])
    elif isinstance(datos, list):
        lista_tareas = datos
    else:
        print("❌ ERROR: Formato de JSON no reconocido.")
        print("   Se esperaba una lista o un dict con la clave 'tareas'.")
        sys.exit(1)

    if not lista_tareas:
        print("📭 El archivo no contiene tareas. Nada que migrar.")
        return

    print(f"📋 Se encontraron {len(lista_tareas)} tarea(s) para migrar.")

    # 4. Insertar en SQLite
    app = create_app()
    with app.app_context():
        migradas = 0
        omitidas = 0
        for t in lista_tareas:
            titulo = (t.get("titulo") or "").strip()
            if not titulo:
                omitidas += 1
                continue

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

    # 5. Resumen final
    print("=" * 40)
    print(f"✅ Migración completada")
    print(f"   - {migradas} tarea(s) insertada(s)")
    if omitidas:
        print(f"   - {omitidas} tarea(s) omitida(s) (sin título válido)")
    print("=" * 40)


if __name__ == "__main__":
    ruta = sys.argv[1] if len(sys.argv) > 1 else "tareas.json"
    migrar(ruta)