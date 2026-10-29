import pytest
from app import create_app, db
from app.models import Usuario, Tarea, Subtarea


@pytest.fixture
def cliente():
    """Crea una app de prueba con base de datos en memoria."""
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "JWT_SECRET_KEY": "clave-de-test-suficientemente-larga-para-32-bytes-o-mas",
        "JWT_ACCESS_TOKEN_EXPIRES": 3600,
        "APP_URL": "http://localhost:5000",  # Para que auto-verifique el email en test
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


def test_cambiar_password_incorrecta(cliente, auth_headers):
    resp = cliente.post("/auth/cambiar-password", headers=auth_headers, json={
        "password_actual": "incorrecta",
        "password_nueva": "nuevopass123"
    })
    assert resp.status_code == 400


# ====================================================
# TESTS DE TAREAS (CRUD BÁSICO)
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
    assert data["recurrencia"] == "semanal"
    assert data["estado"] == "pendiente"


def test_crear_tarea_con_subtareas(cliente, auth_headers):
    resp = cliente.post("/tareas", headers=auth_headers, json={
        "titulo": "Compras",
        "subtareas": [
            {"texto": "Leche", "completada": False},
            {"texto": "Pan", "completada": True}
        ]
    })
    assert resp.status_code == 201
    data = resp.get_json()
    assert len(data["subtareas"]) == 2
    assert data["subtareas"][0]["texto"] == "Leche"


def test_actualizar_tarea(cliente, auth_headers):
    cliente.post("/tareas", headers=auth_headers, json={"titulo": "Original"})
    resp = cliente.patch("/tareas/1", headers=auth_headers, json={"titulo": "Editada", "estado": "en_progreso"})
    assert resp.status_code == 200
    assert resp.get_json()["titulo"] == "Editada"
    assert resp.get_json()["estado"] == "en_progreso"


def test_listar_tareas(cliente, auth_headers):
    cliente.post("/tareas", headers=auth_headers, json={"titulo": "Tarea 1"})
    cliente.post("/tareas", headers=auth_headers, json={"titulo": "Tarea 2"})
    resp = cliente.get("/tareas", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.get_json()) == 2


# ====================================================
# TESTS DE PAPELERA DE RECICLAJE
# ====================================================

def test_soft_delete_y_restaurar(cliente, auth_headers):
    cliente.post("/tareas", headers=auth_headers, json={"titulo": "A borrar"})

    # Eliminar (Soft Delete)
    resp = cliente.delete("/tareas/1", headers=auth_headers)
    assert resp.status_code == 200

    # La tarea ya no debe estar en la lista principal
    resp_list = cliente.get("/tareas", headers=auth_headers)
    assert len(resp_list.get_json()) == 0

    # Debe estar en la papelera
    resp_papelera = cliente.get("/tareas/papelera", headers=auth_headers)
    assert len(resp_papelera.get_json()) == 1

    # Restaurar
    resp_restaurar = cliente.post("/tareas/1/restaurar", headers=auth_headers)
    assert resp_restaurar.status_code == 200

    # Debe volver a la lista principal
    resp_list2 = cliente.get("/tareas", headers=auth_headers)
    assert len(resp_list2.get_json()) == 1


def test_eliminar_definitivo(cliente, auth_headers):
    cliente.post("/tareas", headers=auth_headers, json={"titulo": "A borrar"})
    cliente.delete("/tareas/1", headers=auth_headers)

    resp = cliente.delete("/tareas/1/definitivo", headers=auth_headers)
    assert resp.status_code == 200

    resp_papelera = cliente.get("/tareas/papelera", headers=auth_headers)
    assert len(resp_papelera.get_json()) == 0


# ====================================================
# TESTS DE TAREAS RECURRENTES
# ====================================================

def test_tarea_recurrente_se_auto_crea(cliente, auth_headers):
    # Crear tarea diaria con fecha
    cliente.post("/tareas", headers=auth_headers, json={
        "titulo": "Regar plantas",
        "recurrencia": "diaria",
        "fecha_limite": "2026-10-15"
    })

    # Completarla
    resp = cliente.patch("/tareas/1", headers=auth_headers, json={"completada": True})
    assert resp.status_code == 200
    data = resp.get_json()

    # Debe devolver la nueva tarea recurrente
    assert "nueva_tarea_recurrente" in data
    nueva_tarea = data["nueva_tarea_recurrente"]
    assert nueva_tarea["titulo"] == "Regar plantas"
    assert nueva_tarea["fecha_limite"] == "2026-10-16"  # 1 día después
    assert nueva_tarea["completada"] is False

    # La tarea original debe estar en la papelera
    resp_papelera = cliente.get("/tareas/papelera", headers=auth_headers)
    assert len(resp_papelera.get_json()) == 1


# ====================================================
# TESTS DE HISTORIAL DE ACTIVIDAD
# ====================================================

def test_historial_actividad(cliente, auth_headers):
    # 1. Crear tarea y capturar el ID real
    resp_crear = cliente.post("/tareas", headers=auth_headers, json={"titulo": "Tarea historial"})
    assert resp_crear.status_code == 201, f"Error al crear: {resp_crear.get_json()}"
    tarea_id = resp_crear.get_json()["id"]

    # 2. Editar la tarea usando el ID real
    resp_editar = cliente.patch(f"/tareas/{tarea_id}", headers=auth_headers, json={"titulo": "Tarea editada"})
    assert resp_editar.status_code == 200, f"Error al editar: {resp_editar.get_json()}"

    # 3. Obtener historial
    resp = cliente.get("/actividades", headers=auth_headers)
    assert resp.status_code == 200, f"Error al obtener historial: {resp.get_json()}"
    historial = resp.get_json()
    
    # 4. Verificar que sea una lista y tenga los registros
    assert isinstance(historial, list), f"Se esperaba lista, se obtuvo: {type(historial)}"
    assert len(historial) >= 2, f"Se esperaban 2+ registros, se obtuvieron {len(historial)}: {historial}"
    
    # 5. Verificar que la palabra "creó" esté en algún detalle
    assert any("creó" in h["detalle"].lower() for h in historial), f"No se encontró 'creó' en: {historial}"


# ====================================================
# TESTS DE EXPORTACIÓN (Solo status code)
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