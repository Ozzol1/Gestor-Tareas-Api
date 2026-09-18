from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Tarea
from app.validators import validar_payload_tarea

bp = Blueprint("tareas", __name__)


# ====================================================
# GET /tareas - Listar tareas del usuario autenticado
# ====================================================
@bp.route("/tareas", methods=["GET"])
@jwt_required()
def listar_tareas():
    usuario_id = int(get_jwt_identity())

    query = Tarea.query.filter_by(usuario_id=usuario_id)

    # Filtro opcional: ?completada=true/false
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
# GET /tareas/<id> - Obtener una tarea (solo si es tuya)
# ====================================================
@bp.route("/tareas/<int:tarea_id>", methods=["GET"])
@jwt_required()
def obtener_tarea(tarea_id):
    usuario_id = int(get_jwt_identity())
    tarea = Tarea.query.filter_by(id=tarea_id, usuario_id=usuario_id).first()

    if not tarea:
        return jsonify({"error": f"No existe una tarea con ID {tarea_id}."}), 404

    return jsonify(tarea.to_dict()), 200


# ====================================================
# POST /tareas - Crear tarea (asigna usuario_id del token)
# ====================================================
@bp.route("/tareas", methods=["POST"])
@jwt_required()
def crear_tarea():
    usuario_id = int(get_jwt_identity())

    if not request.is_json:
        return jsonify({"error": "El Content-Type debe ser application/json."}), 400

    data = request.get_json()

    es_valido, error = validar_payload_tarea(data, parcial=False)
    if not es_valido:
        return jsonify({"error": error}), 400

    nueva = Tarea(
        titulo=data["titulo"].strip(),
        descripcion=data.get("descripcion"),
        prioridad=data.get("prioridad", "media"),
        fecha_limite=data.get("fecha_limite"),
        completada=data.get("completada", False),
        usuario_id=usuario_id,  # ← Asignación automática
    )
    db.session.add(nueva)
    db.session.commit()

    return jsonify(nueva.to_dict()), 201


# ====================================================
# PATCH /tareas/<id> - Actualizar (solo si es tuya)
# ====================================================
@bp.route("/tareas/<int:tarea_id>", methods=["PATCH"])
@jwt_required()
def actualizar_tarea(tarea_id):
    usuario_id = int(get_jwt_identity())
    tarea = Tarea.query.filter_by(id=tarea_id, usuario_id=usuario_id).first()

    if not tarea:
        return jsonify({"error": f"No existe una tarea con ID {tarea_id}."}), 404

    if not request.is_json:
        return jsonify({"error": "El Content-Type debe ser application/json."}), 400

    data = request.get_json()

    es_valido, error = validar_payload_tarea(data, parcial=True)
    if not es_valido:
        return jsonify({"error": error}), 400

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
# DELETE /tareas/<id> - Eliminar (solo si es tuya)
# ====================================================
@bp.route("/tareas/<int:tarea_id>", methods=["DELETE"])
@jwt_required()
def eliminar_tarea(tarea_id):
    usuario_id = int(get_jwt_identity())
    tarea = Tarea.query.filter_by(id=tarea_id, usuario_id=usuario_id).first()

    if not tarea:
        return jsonify({"error": f"No existe una tarea con ID {tarea_id}."}), 404

    db.session.delete(tarea)
    db.session.commit()
    return jsonify({"mensaje": f"Tarea {tarea_id} eliminada correctamente."}), 200