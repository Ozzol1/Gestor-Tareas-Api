import pytest
from app import create_app, db
from app.models import Usuario, Tarea


@pytest.fixture
def cliente():
    """Crea una app de prueba con base de datos en memoria."""
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "JWT_SECRET_KEY": "clave-de-test-suficientemente-larga-para-32-bytes-o-mas",
        "JWT_ACCESS_TOKEN_EXPIRES": 3600,
    })

    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


def registrar(cliente, email, password):
    """Helper: registra un usuario y devuelve la respuesta."""
    return cliente.post("/auth/registro", json={"email": email, "password": password})


def login(cliente, email, password):
    """Helper: hace login y devuelve el token."""
    resp = cliente.post("/auth/login", json={"email": email, "password": password})
    return resp.get_json()["access_token"]


def auth_header(token):
    """Helper: devuelve el header de autorización."""
    return {"Authorization": f"Bearer {token}"}


# ====================================================
# TESTS DE AUTENTICACIÓN
# ====================================================

def test_registro_exitoso(cliente):
    resp = registrar(cliente, "khale@example.com", "secreto123")
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["usuario"]["email"] == "khale@example.com"
    assert "password" not in data["usuario"]
    assert "password_hash" not in data["usuario"]


def test_registro_email_duplicado(cliente):
    registrar(cliente, "khale@example.com", "secreto123")
    resp = registrar(cliente, "khale@example.com", "otro12345")
    assert resp.status_code == 409


def test_registro_password_corta(cliente):
    resp = registrar(cliente, "khale@example.com", "123")
    assert resp.status_code == 400
    assert "8 caracteres" in resp.get_json()["error"]


def test_registro_email_invalido(cliente):
    resp = registrar(cliente, "no-es-email", "secreto123")
    assert resp.status_code == 400


def test_login_exitoso(cliente):
    registrar(cliente, "khale@example.com", "secreto123")
    resp = cliente.post("/auth/login", json={"email": "khale@example.com", "password": "secreto123"})
    assert resp.status_code == 200
    assert "access_token" in resp.get_json()


def test_login_credenciales_malas(cliente):
    registrar(cliente, "khale@example.com", "secreto123")
    resp = cliente.post("/auth/login", json={"email": "khale@example.com", "password": "wrongpass"})
    assert resp.status_code == 401


def test_perfil_sin_token(cliente):
    resp = cliente.get("/auth/perfil")
    assert resp.status_code == 401


def test_perfil_con_token(cliente):
    registrar(cliente, "khale@example.com", "secreto123")
    token = login(cliente, "khale@example.com", "secreto123")
    resp = cliente.get("/auth/perfil", headers=auth_header(token))
    assert resp.status_code == 200
    assert resp.get_json()["email"] == "khale@example.com"


# ====================================================
# TESTS DE TAREAS (con autenticación)
# ====================================================

def test_tareas_sin_token(cliente):
    resp = cliente.get("/tareas")
    assert resp.status_code == 401


def test_crear_tarea_con_token(cliente):
    registrar(cliente, "khale@example.com", "secreto123")
    token = login(cliente, "khale@example.com", "secreto123")

    resp = cliente.post("/tareas", headers=auth_header(token),
                        json={"titulo": "Estudiar JWT", "prioridad": "alta"})
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["titulo"] == "Estudiar JWT"
    assert data["usuario_id"] is not None


def test_listar_tareas_propias(cliente):
    registrar(cliente, "khale@example.com", "secreto123")
    token = login(cliente, "khale@example.com", "secreto123")

    cliente.post("/tareas", headers=auth_header(token), json={"titulo": "Tarea 1"})
    cliente.post("/tareas", headers=auth_header(token), json={"titulo": "Tarea 2"})

    resp = cliente.get("/tareas", headers=auth_header(token))
    assert resp.status_code == 200
    assert len(resp.get_json()) == 2


def test_aislamiento_entre_usuarios(cliente):
    """Usuario A no puede ver tareas de Usuario B."""
    # Khale crea una tarea
    registrar(cliente, "khale@example.com", "secreto123")
    token_khale = login(cliente, "khale@example.com", "secreto123")
    resp = cliente.post("/tareas", headers=auth_header(token_khale), json={"titulo": "Tarea de Khale"})
    tarea_id = resp.get_json()["id"]

    # María intenta verla
    registrar(cliente, "maria@example.com", "maria12345")
    token_maria = login(cliente, "maria@example.com", "maria12345")

    resp = cliente.get(f"/tareas/{tarea_id}", headers=auth_header(token_maria))
    assert resp.status_code == 404

    # María intenta listar -> solo ve las suyas
    resp = cliente.get("/tareas", headers=auth_header(token_maria))
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_maria_no_puede_eliminar_tarea_de_khale(cliente):
    registrar(cliente, "khale@example.com", "secreto123")
    token_khale = login(cliente, "khale@example.com", "secreto123")
    resp = cliente.post("/tareas", headers=auth_header(token_khale), json={"titulo": "Tarea de Khale"})
    tarea_id = resp.get_json()["id"]

    registrar(cliente, "maria@example.com", "maria12345")
    token_maria = login(cliente, "maria@example.com", "maria12345")

    resp = cliente.delete(f"/tareas/{tarea_id}", headers=auth_header(token_maria))
    assert resp.status_code == 404


def test_patch_tarea_propia(cliente):
    registrar(cliente, "khale@example.com", "secreto123")
    token = login(cliente, "khale@example.com", "secreto123")
    resp = cliente.post("/tareas", headers=auth_header(token), json={"titulo": "Original"})
    tarea_id = resp.get_json()["id"]

    resp = cliente.patch(f"/tareas/{tarea_id}", headers=auth_header(token),
                         json={"completada": True, "prioridad": "alta"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["completada"] is True
    assert data["prioridad"] == "alta"


def test_crear_tarea_titulo_vacio(cliente):
    registrar(cliente, "khale@example.com", "secreto123")
    token = login(cliente, "khale@example.com", "secreto123")
    resp = cliente.post("/tareas", headers=auth_header(token), json={"titulo": "   "})
    assert resp.status_code == 400