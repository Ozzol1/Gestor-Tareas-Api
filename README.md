# 🚀 Gestor de Tareas - API REST con JWT

API REST para el gestor de tareas con autenticación JWT, integrada con el CRM interno de NovaTech.

## 📋 Stack

- Python 3.10+
- Flask
- Flask-JWT-Extended
- SQLAlchemy + SQLite
- pytest

## 📦 Instalación

```bash
git clone <tu-repo>
cd gestor-tareas-api
py -m pip install -r requirements.txt
```

## 🔐 Configuración

Copia el archivo de ejemplo y ajusta los valores:

```bash
copy .env.example .env
```

Genera una clave secreta segura para `JWT_SECRET_KEY`:

```bash
py -c "import secrets; print(secrets.token_hex(32))"
```

## 🚀 Uso

```bash
py -m flask --app app run --debug
```

La API corre en `http://127.0.0.1:5000`.

## 📚 Endpoints

### Autenticación

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| POST | `/auth/registro` | Crear usuario | ❌ |
| POST | `/auth/login` | Iniciar sesión → devuelve JWT | ❌ |
| GET | `/auth/perfil` | Datos del usuario autenticado | ✅ |

### Tareas (todas requieren JWT)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/tareas` | Listar tareas propias. Filtro: `?completada=true/false` |
| GET | `/tareas/<id>` | Obtener una tarea propia
| POST | `/tareas` | Crear tarea |
| PATCH | `/tareas/<id>` | Actualizar tarea propia |
| DELETE | `/tareas/<id>` | Eliminar tarea propia |

**Nota:** Un usuario **no puede ver ni modificar tareas de otro usuario**. Devuelve `404` por seguridad.

## 🔧 Ejemplos con curl

### 1. Registro

```bash
curl -X POST http://127.0.0.1:5000/auth/registro \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"khale@example.com\",\"password\":\"secreto123\"}"
```

### 2. Login

```bash
curl -X POST http://127.0.0.1:5000/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"khale@example.com\",\"password\":\"secreto123\"}"
```

Copia el `access_token` de la respuesta.

### 3. Crear tarea (con token)

```bash
curl -X POST http://127.0.0.1:5000/tareas \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TU_TOKEN_AQUI" \
  -d "{\"titulo\":\"Mi tarea\",\"prioridad\":\"alta\"}"
```

### 4. Listar mis tareas

```bash
curl http://127.0.0.1:5000/tareas \
  -H "Authorization: Bearer TU_TOKEN_AQUI"
```

## 🧪 Tests

```bash
py -m pytest tests/ -v
```

## 📥 Migración de datos

Si tienes un `tareas.json` del proyecto anterior:

```bash
py migrar_json.py ruta/al/tareas.json
```

Si tienes tareas huérfanas (creadas antes de auth):

```bash
py migrar_usuarios.py           # Al primer usuario registrado
py migrar_usuarios.py 2         # Al usuario con ID 2
py migrar_usuarios.py --eliminar # O bórralas
```

## 🧱 Modelo de datos

- **Usuario**: cada usuario tiene email único y contraseña hasheada con werkzeug.
- **Tarea**: cada tarea **pertenece obligatoriamente a un usuario** (`usuario_id` es `NOT NULL`). No existen tareas huérfanas en el modelo final.

Si migras datos desde un sistema anterior (como `tareas.json`), usa `migrar_json.py` y asegúrate de que las tareas se asignen a un usuario existente. El script de migración `migrar_usuarios.py` **fue eliminado** en la versión final, porque el esquema ahora impide tareas sin dueño.


## 📁 Estructura

```
gestor-tareas-api/
├── app/
│   ├── __init__.py       # Factory + JWT config
│   ├── models.py         # Usuario + Tarea
│   ├── routes.py         # Endpoints de tareas
│   ├── auth.py           # Endpoints de autenticación
│   ├── validators.py     # Validaciones
│   └── utils.py          # Helpers (email, password)
├── tests/
│   └── test_tareas.py
├── migrar_json.py
├── migrar_usuarios.py
├── requirements.txt
├── .env.example
├── README.md
└── .gitignore
```

## 👤 Autor

**Khale Rodríguez** — Desarrollador Junior, NovaTech.