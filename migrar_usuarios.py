"""
Script de migración: asigna un usuario por defecto a las tareas huérfanas
(tareas con usuario_id = NULL, creadas antes de añadir autenticación).

Uso:
    py migrar_usuarios.py                    # usa el primer usuario registrado
    py migrar_usuarios.py 2                  # usa el usuario con ID 2
    py migrar_usuarios.py --eliminar         # borra las tareas huérfanas
"""
import sys
from app import create_app, db
from app.models import Usuario, Tarea


def migrar(usuario_id=None, eliminar=False):
    app = create_app()
    with app.app_context():
        # 1. Buscar tareas huérfanas
        huerfanas = Tarea.query.filter(Tarea.usuario_id.is_(None)).all()

        if not huerfanas:
            print("✅ No hay tareas huérfanas. Nada que migrar.")
            return

        print(f"📋 Se encontraron {len(huerfanas)} tarea(s) huérfana(s).")

        # 2. Modo eliminar
        if eliminar:
            for t in huerfanas:
                db.session.delete(t)
            db.session.commit()
            print(f"🗑️  {len(huerfanas)} tarea(s) eliminada(s).")
            return

        # 3. Modo asignar a un usuario
        if usuario_id is None:
            # Tomar el primer usuario registrado (el más antiguo)
            usuario = Usuario.query.order_by(Usuario.id).first()
            if not usuario:
                print("❌ No hay usuarios registrados en la base de datos.")
                print("   Registra un usuario primero con POST /auth/registro")
                sys.exit(1)
        else:
            usuario = db.session.get(Usuario, usuario_id)
            if not usuario:
                print(f"❌ No existe un usuario con ID {usuario_id}.")
                sys.exit(1)

        # Asignar las tareas huérfanas al usuario
        for t in huerfanas:
            t.usuario_id = usuario.id
        db.session.commit()

        print(f"✅ Migración completada:")
        print(f"   - {len(huerfanas)} tarea(s) asignada(s) al usuario '{usuario.email}' (ID {usuario.id}).")


if __name__ == "__main__":
    usuario_id = None
    eliminar = False

    # Parsear argumentos
    for arg in sys.argv[1:]:
        if arg == "--eliminar":
            eliminar = True
        else:
            try:
                usuario_id = int(arg)
            except ValueError:
                print(f"❌ Argumento no válido: {arg}")
                sys.exit(1)

    migrar(usuario_id, eliminar)