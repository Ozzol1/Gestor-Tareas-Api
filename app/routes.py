from flask import Blueprint, request, jsonify
from app import db
from app.models import Tarea
from app.validators import validar_payload_tarea, validar_id

# Creamos un Blueprint para organizar las rutas
bp = Blueprint("tareas", __name__)


# ====================================================
# GET /tareas - Listar todas las tareas (con filtro opcional)
# ====================================================
@bp.route("/tareas", methods=["GET"])
def listar_tareas():
    query = Tarea.query

    # Filtro opcional: ?completada=true o ?completada=false
    completada_param = request.args.get("completada")
    if completada_param is not None:
        if completada_param.lower() == "true":
            query = query.filter_by(completada=True)
        elif completada_param.lower() == "false":
            query = query.filter_by(completada=False)
        else:
            return jsonify({"error": "El filtro 'completada' debe ser 'true' o 'false'."}), 400

    tareas = query.all()
    return jsonify([t.to_dict() for t in tareas]), 200


# ====================================================
# GET /tareas/<id> - Obtener una tarea por ID
# ====================================================
@bp.route("/tareas/<int:tarea_id>", methods=["GET"])
def obtener_tarea(tarea_id):
    tarea = db.session.get(Tarea, tarea_id)
    if not tarea:
        return jsonify({"error": f"No existe una tarea con ID {tarea_id}."}), 404
    return jsonify(tarea.to_dict()), 200


# ====================================================
# POST /tareas - Crear una nueva tarea
# ====================================================
@bp.route("/tareas", methods=["POST"])
def crear_tarea():
    # Validar que el Content-Type sea JSON
    if not request.is_json:
        return jsonify({"error": "El Content-Type debe ser application/json."}), 400

    data = request.get_json()

    # Validar payload
    es_valido, error = validar_payload_tarea(data, parcial=False)
    if not es_valido:
        return jsonify({"error": error}), 400

    # Crear la tarea
    nueva = Tarea(
        titulo=data["titulo"].strip(),
        descripcion=data.get("descripcion"),
        prioridad=data.get("prioridad", "media"),
        fecha_limite=data.get("fecha_limite"),
        completada=data.get("completada", False),
    )
    db.session.add(nueva)
    db.session.commit()

    return jsonify(nueva.to_dict()), 201


# ====================================================
# PATCH /tareas/<id> - Actualizar campos parciales
# ====================================================
@bp.route("/tareas/<int:tarea_id>", methods=["PATCH"])
def actualizar_tarea(tarea_id):
    tarea = db.session.get(Tarea, tarea_id)
    if not tarea:
        return jsonify({"error": f"No existe una tarea con ID {tarea_id}."}), 404

    if not request.is_json:
        return jsonify({"error": "El Content-Type debe ser application/json."}), 400

    data = request.get_json()

    # Validar solo los campos que vienen (parcial=True)
    es_valido, error = validar_payload_tarea(data, parcial=True)
    if not es_valido:
        return jsonify({"error": error}), 400

    # Aplicar los cambios
    campos_actualizables = ["titulo", "descripcion", "completada", "prioridad", "fecha_limite"]
    for campo in campos_actualizables:
        if campo in data:
            valor = data[campo]
            if campo == "titulo":
                valor = valor.strip()
            setattr(tarea, campo, valor)

    db.session.commit()
    return jsonify(tarea.to_dict()), 200


# ====================================================
# DELETE /tareas/<id> - Eliminar una tarea
# ====================================================
@bp.route("/tareas/<int:tarea_id>", methods=["DELETE"])
def eliminar_tarea(tarea_id):
    tarea = db.session.get(Tarea, tarea_id)
    if not tarea:
        return jsonify({"error": f"No existe una tarea con ID {tarea_id}."}), 404

    db.session.delete(tarea)
    db.session.commit()
    return jsonify({"mensaje": f"Tarea {tarea_id} eliminada correctamente."}), 200