import pytest
import io
from app import create_app, db
from app.models import Usuario, Tarea, Subtarea, Comentario, Archivo


@pytest.fixture
def cliente():
    """Crea una app de prueba con base de datos en memoria."""
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "JWT_SECRET_KEY": "clave-de-test-suficientemente-larga-para-32-bytes-o-mas",
        "JWT_ACCESS_TOKEN_EXPIRES": 3600,
        "APP_URL": "http://localhost:5000",
    })

    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


@pytest.fixture
def auth_headers(cliente):
    """Registra un usuario, hace login y devuelve los headers con el token."""
    cliente.post("/auth/registro", json={
        "email": "test@ejemplo.com",
        "password": "secreto123"
    })
    resp = cliente.post("/auth/login", json={
        "email": "test@ejemplo.com",
        "password": "secreto123"
    })
    token = resp.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ====================================================
# TESTS DE AUTENTICACIÓN
# ====================================================
def test_registro_exitoso(cliente):
    resp = cliente.post("/auth/registro", json={"email": "nuevo@ejemplo.com", "password": "secreto123"})
    assert resp.status_code == 201
    assert "password" not in resp.get_json()["usuario"]


def test_login_exitoso(cliente):
    cliente.post("/auth/registro", json={"email": "test@ejemplo.com", "password": "secreto123"})
    resp = cliente.post("/auth/login", json={"email": "test@ejemplo.com", "password": "secreto123"})
    assert resp.status_code == 200
    assert "access_token" in resp.get_json()


def test_cambiar_password(cliente, auth_headers):
    resp = cliente.post("/auth/cambiar-password", headers=auth_headers, json={
        "password_actual": "secreto123",
        "password_nueva": "nuevopass123"
    })
    assert resp.status_code == 200
    
    # Verificar que la nueva contraseña funciona
    resp_login = cliente.post("/auth/login", json={"email": "test@ejemplo.com", "password": "nuevopass123"})
    assert resp_login.status_code == 200


# ====================================================
# TESTS DE TAREAS (CRUD + KANBAN)
# ====================================================
def test_crear_tarea_completa(cliente, auth_headers):
    resp = cliente.post("/tareas", headers=auth_headers, json={
        "titulo": "Tarea Completa",
        "prioridad": "alta",
        "categoria": "Trabajo",
        "recurrencia": "semanal",
        "estado": "pendiente"
    })
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["titulo"] == "Tarea Completa"
    assert data["categoria"] == "Trabajo"
    assert data["estado"] == "pendiente"


def test_mover_tarea_kanban(cliente, auth_headers):
    # Crear tarea
    resp = cliente.post("/tareas", headers=auth_headers, json={"titulo": "Mover en Kanban"})
    tarea_id = resp.get_json()["id"]

    # Mover a "En Progreso"
    resp_patch = cliente.patch(f"/tareas/{tarea_id}", headers=auth_headers, json={"estado": "en_progreso"})
    assert resp_patch.status_code == 200
    assert resp_patch.get_json()["estado"] == "en_progreso"
    assert resp_patch.get_json()["completada"] is False

    # Mover a "Completado"
    resp_patch2 = cliente.patch(f"/tareas/{tarea_id}", headers=auth_headers, json={"estado": "completado"})
    assert resp_patch2.status_code == 200
    assert resp_patch2.get_json()["estado"] == "completado"
    assert resp_patch2.get_json()["completada"] is True


# ====================================================
# TESTS DE PAPELERA
# ====================================================
def test_soft_delete_y_restaurar(cliente, auth_headers):
    cliente.post("/tareas", headers=auth_headers, json={"titulo": "A borrar"})

    cliente.delete("/tareas/1", headers=auth_headers)
    assert len(cliente.get("/tareas", headers=auth_headers).get_json()) == 0
    assert len(cliente.get("/tareas/papelera", headers=auth_headers).get_json()) == 1

    cliente.post("/tareas/1/restaurar", headers=auth_headers)
    assert len(cliente.get("/tareas", headers=auth_headers).get_json()) == 1


# ====================================================
# TESTS DE COMENTARIOS
# ====================================================
def test_comentarios_tarea(cliente, auth_headers):
    # Crear tarea
    resp_tarea = cliente.post("/tareas", headers=auth_headers, json={"titulo": "Tarea con comentario"})
    tarea_id = resp_tarea.get_json()["id"]

    # Crear comentario
    resp = cliente.post(f"/tareas/{tarea_id}/comentarios", headers=auth_headers, json={"texto": "Hola mundo"})
    assert resp.status_code == 201
    assert resp.get_json()["texto"] == "Hola mundo"
    comentario_id = resp.get_json()["id"]

    # Listar comentarios
    resp_list = cliente.get(f"/tareas/{tarea_id}/comentarios", headers=auth_headers)
    assert len(resp_list.get_json()) == 1

    # Eliminar comentario
    resp_delete = cliente.delete(f"/comentarios/{comentario_id}", headers=auth_headers)
    assert resp_delete.status_code == 200

    # Verificar que ya no hay comentarios
    resp_list2 = cliente.get(f"/tareas/{tarea_id}/comentarios", headers=auth_headers)
    assert len(resp_list2.get_json()) == 0


# ====================================================
# TESTS DE ARCHIVOS ADJUNTOS
# ====================================================
def test_subir_y_eliminar_archivo(cliente, auth_headers):
    # Crear tarea
    resp_tarea = cliente.post("/tareas", headers=auth_headers, json={"titulo": "Tarea con archivo"})
    tarea_id = resp_tarea.get_json()["id"]

    # Subir un archivo falso
    archivo_falso = (io.BytesIO(b"contenido de prueba"), "documento_prueba.txt")
    resp = cliente.post(
        f"/tareas/{tarea_id}/archivos",
        headers=auth_headers,
        data={"archivo": archivo_falso},
        content_type="multipart/form-data"
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["nombre_original"] == "documento_prueba.txt"
    archivo_id = data["id"]

    # Verificar que la tarea ahora tiene 1 archivo
    tarea_actualizada = cliente.get(f"/tareas/{tarea_id}", headers=auth_headers).get_json()
    assert len(tarea_actualizada["archivos"]) == 1

    # Eliminar archivo
    resp_delete = cliente.delete(f"/archivos/{archivo_id}", headers=auth_headers)
    assert resp_delete.status_code == 200


# ====================================================
# TESTS DE HISTORIAL
# ====================================================
def test_historial_actividad(cliente, auth_headers):
    resp_crear = cliente.post("/tareas", headers=auth_headers, json={"titulo": "Tarea historial"})
    tarea_id = resp_crear.get_json()["id"]

    cliente.patch(f"/tareas/{tarea_id}", headers=auth_headers, json={"titulo": "Tarea editada"})

    resp = cliente.get("/actividades", headers=auth_headers)
    assert resp.status_code == 200
    historial = resp.get_json()
    assert len(historial) >= 2
    assert any("creó" in h["detalle"].lower() for h in historial)


# ====================================================
# TESTS DE EXPORTACIÓN
# ====================================================
def test_export_pdf(cliente, auth_headers):
    cliente.post("/tareas", headers=auth_headers, json={"titulo": "Para exportar"})
    resp = cliente.get("/tareas/export/pdf", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.mimetype == "application/pdf"


def test_export_excel(cliente, auth_headers):
    cliente.post("/tareas", headers=auth_headers, json={"titulo": "Para exportar"})
    resp = cliente.get("/tareas/export/excel", headers=auth_headers)
    assert resp.status_code == 200
    assert "spreadsheetml" in resp.mimetype