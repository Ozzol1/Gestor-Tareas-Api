# 🚀 Gestor de Tareas - API REST

API REST para el gestor de tareas, integrada con el CRM interno de NovaTech. Migra la persistencia de JSON a SQLite y expone los endpoints para consumo externo.

## 📋 Stack

- Python 3.10+
- Flask
- SQLAlchemy
- SQLite
- pytest

## 📦 Instalación

```bash
pip install -r requirements.txt
```

## 🚀 Uso

```bash
py -m flask --app app run --debug
```

La API corre en `http://127.0.0.1:5000`.

## 📚 Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/tareas` | Listar tareas. Filtro opcional: `?completada=true/false` |
| GET | `/tareas/<id>` | Obtener una tarea por ID |
| POST | `/tareas` | Crear tarea |
| PATCH | `/tareas/<id>` | Actualizar campos parciales |
| DELETE | `/tareas/<id>` | Eliminar tarea |

## 🔧 Ejemplos con curl

### Crear una tarea

```bash
curl -X POST http://127.0.0.1:5000/tareas \
  -H "Content-Type: application/json" \
  -d "{\"titulo\":\"Estudiar Flask\",\"prioridad\":\"alta\"}"
```

### Listar todas las tareas

```bash
curl http://127.0.0.1:5000/tareas
```

### Marcar como completada

```bash
curl -X PATCH http://127.0.0.1:5000/tareas/1 \
  -H "Content-Type: application/json" \
  -d "{\"completada\":true}"
```

### Eliminar una tarea

```bash
curl -X DELETE http://127.0.0.1:5000/tareas/1
```

## 📥 Migración desde JSON

```bash
py migrar_json.py ruta/al/tareas.json
```

## 🧪 Tests

```bash
py -m pytest tests/ -v
```

## 📁 Estructura

```
gestor-tareas-api/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   └── validators.py
├── tests/
│   └── test_tareas.py
├── migrar_json.py
├── requirements.txt
├── README.md
└── .gitignore
```

## 👤 Autor

**Khale Rodríguez** — Desarrollador Junior, NovaTech.