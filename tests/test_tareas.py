import pytest
from app import create_app, db
from app.models import Tarea


@pytest.fixture
def cliente():
    """Crea una app de prueba con base de datos en memoria (no toca la real)."""
    app = create_app()
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["TESTING"] = True

    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


# ====================================================
# HAPPY PATHS
# ====================================================

def test_ping(cliente):
    """El endpoint /ping debe responder pong."""
    resp = cliente.get("/ping")
    assert resp.status_code == 200
    assert resp.get_json()["mensaje"] == "pong"


def test_listar_tareas_vacio(cliente):
    """Al inicio no hay tareas."""
    resp = cliente.get("/tareas")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_crear_tarea(cliente):
    """Crear una tarea válida debe devolver 201 y los datos."""
    resp = cliente.post("/tareas", json={
        "titulo": "Test tarea",
        "prioridad": "alta",
        "fecha_limite": "2026-12-31"
    })
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["titulo"] == "Test tarea"
    assert data["prioridad"] == "alta"
    assert data["completada"] is False
    assert "id" in data


def test_obtener_tarea_por_id(cliente):
    """Debe devolver una tarea existente."""
    cliente.post("/tareas", json={"titulo": "Mi tarea"})
    resp = cliente.get("/tareas/1")
    assert resp.status_code == 200
    assert resp.get_json()["titulo"] == "Mi tarea"


def test_actualizar_tarea_patch(cliente):
    """PATCH debe actualizar solo los campos enviados."""
    cliente.post("/tareas", json={"titulo": "Original", "prioridad": "baja"})
    resp = cliente.patch("/tareas/1", json={"completada": True, "prioridad": "alta"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["completada"] is True
    assert data["prioridad"] == "alta"
    assert data["titulo"] == "Original"  # No cambió


def test_eliminar_tarea(cliente):
    """DELETE debe eliminar y devolver 200."""
    cliente.post("/tareas", json={"titulo": "A eliminar"})
    resp = cliente.delete("/tareas/1")
    assert resp.status_code == 200

    # Verificar que ya no existe
    resp = cliente.get("/tareas/1")
    assert resp.status_code == 404


def test_filtro_completada(cliente):
    """El filtro ?completada=true/false debe funcionar."""
    cliente.post("/tareas", json={"titulo": "Pendiente"})
    cliente.post("/tareas", json={"titulo": "Completada"})
    cliente.patch("/tareas/2", json={"completada": True})

    resp = cliente.get("/tareas?completada=true")
    assert resp.status_code == 200
    assert len(resp.get_json()) == 1
    assert resp.get_json()[0]["titulo"] == "Completada"

    resp = cliente.get("/tareas?completada=false")
    assert len(resp.get_json()) == 1
    assert resp.get_json()[0]["titulo"] == "Pendiente"


# ====================================================
# CASOS DE ERROR
# ====================================================

def test_crear_tarea_sin_titulo(cliente):
    """Sin título debe devolver 400."""
    resp = cliente.post("/tareas", json={"descripcion": "sin titulo"})
    assert resp.status_code == 400
    assert "titulo" in resp.get_json()["error"].lower()


def test_crear_tarea_titulo_vacio(cliente):
    """Título vacío debe devolver 400."""
    resp = cliente.post("/tareas", json={"titulo": "   "})
    assert resp.status_code == 400


def test_crear_tarea_fecha_invalida(cliente):
    """Fecha con formato incorrecto debe devolver 400."""
    resp = cliente.post("/tareas", json={"titulo": "Prueba", "fecha_limite": "31/12/2026"})
    assert resp.status_code == 400
    assert "YYYY-MM-DD" in resp.get_json()["error"]


def test_crear_tarea_prioridad_invalida(cliente):
    """Prioridad fuera del enum debe devolver 400."""
    resp = cliente.post("/tareas", json={"titulo": "Prueba", "prioridad": "urgente"})
    assert resp.status_code == 400


def test_obtener_tarea_inexistente(cliente):
    """ID inexistente debe devolver 404."""
    resp = cliente.get("/tareas/999")
    assert resp.status_code == 404


def test_eliminar_tarea_inexistente(cliente):
    """Eliminar ID inexistente debe devolver 404."""
    resp = cliente.delete("/tareas/999")
    assert resp.status_code == 404


def test_post_sin_json(cliente):
    """POST sin Content-Type JSON debe devolver 400."""
    resp = cliente.post("/tareas", data="no soy json", content_type="text/plain")
    assert resp.status_code == 400