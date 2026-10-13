from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Tarea, Usuario
from app.validators import validar_payload_tarea
from app import exports
from datetime import datetime, timezone, timedelta

bp = Blueprint("tareas", __name__)


def _get_usuario_actual():
    """Devuelve el objeto Usuario del token actual."""
    usuario_id = int(get_jwt_identity())
    return Usuario.query.get(usuario_id)


# ====================================================
# LISTAR
# ====================================================
@bp.route("/tareas", methods=["GET"])
@jwt_required()
def listar_tareas():
    usuario_id = int(get_jwt_identity())
    query = Tarea.query.filter_by(usuario_id=usuario_id, eliminada=False)

    completada_param = request.args.get("completada")
    if completada_param is not None:
        if completada_param.lower() == "true":
            query = query.filter_by(completada=True)
        elif completada_param.lower() == "false":
            query = query.filter_by(completada=False)
        else:
            return jsonify({"error": "El filtro 'completada' debe ser 'true' o 'false'."}), 400

    tareas = query.order_by(Tarea.orden.asc(), Tarea.id.asc()).all()
    return jsonify([t.to_dict() for t in tareas]), 200


# ====================================================
# OBTENER UNA
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
# CREAR
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

    # Calcular el siguiente orden (último + 1)
    ultimo = Tarea.query.filter_by(usuario_id=usuario_id).order_by(Tarea.orden.desc()).first()
    siguiente_orden = (ultimo.orden + 1) if ultimo else 0

    nueva = Tarea(
        titulo=data["titulo"].strip(),
        descripcion=data.get("descripcion"),
        prioridad=data.get("prioridad", "media"),
        categoria=data.get("categoria", "Personal").strip(),
        orden=siguiente_orden,  # ← NUEVO
        fecha_limite=data.get("fecha_limite"),
        completada=data.get("completada", False),
        usuario_id=usuario_id,
    )
    db.session.add(nueva)
    db.session.commit()
    return jsonify(nueva.to_dict()), 201


# ====================================================
# ACTUALIZAR
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

    for campo in ["titulo", "descripcion", "completada", "prioridad", "categoria", "fecha_limite"]:
        if campo in data:
            valor = data[campo]
            if campo == "titulo":
                valor = valor.strip()
            setattr(tarea, campo, valor)

    db.session.commit()
    return jsonify(tarea.to_dict()), 200


# ====================================================
# ELIMINAR
# ====================================================
@bp.route("/tareas/<int:tarea_id>", methods=["DELETE"])
@jwt_required()
def eliminar_tarea(tarea_id):
    usuario_id = int(get_jwt_identity())
    tarea = Tarea.query.filter_by(id=tarea_id, usuario_id=usuario_id, eliminada=False).first()
    if not tarea:
        return jsonify({"error": f"No existe una tarea con ID {tarea_id}."}), 404

    # Soft delete
    tarea.eliminada = True
    tarea.fecha_eliminacion = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify({"mensaje": f"Tarea {tarea_id} movida a la papelera."}), 200

# ====================================================
# EXPORTAR TODAS LAS TAREAS
# ====================================================
@bp.route("/tareas/export/pdf", methods=["GET"])
@jwt_required()
def exportar_todas_pdf():
    usuario = _get_usuario_actual()
    tareas = Tarea.query.filter_by(usuario_id=usuario.id).all()

    pdf_bytes = exports.generar_pdf_tareas(tareas, usuario.email)
    nombre = f"tareas_{usuario.email.split('@')[0]}_{len(tareas)}.pdf"
    return send_file(
        __import__("io").BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=nombre,
    )


@bp.route("/tareas/export/excel", methods=["GET"])
@jwt_required()
def exportar_todas_excel():
    usuario = _get_usuario_actual()
    tareas = Tarea.query.filter_by(usuario_id=usuario.id).all()

    xlsx_bytes = exports.generar_excel_tareas(tareas, usuario.email)
    nombre = f"tareas_{usuario.email.split('@')[0]}_{len(tareas)}.xlsx"
    return send_file(
        __import__("io").BytesIO(xlsx_bytes),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=nombre,
    )


# ====================================================
# EXPORTAR UNA TAREA
# ====================================================
@bp.route("/tareas/<int:tarea_id>/export/txt", methods=["GET"])
@jwt_required()
def exportar_tarea_txt(tarea_id):
    usuario_id = int(get_jwt_identity())
    tarea = Tarea.query.filter_by(id=tarea_id, usuario_id=usuario_id).first()
    if not tarea:
        return jsonify({"error": f"No existe una tarea con ID {tarea_id}."}), 404

    usuario = _get_usuario_actual()
    contenido = exports.generar_txt_tarea(tarea, usuario.email)
    nombre = f"tarea_{tarea.id}_{exports.sanitizar_nombre(tarea.titulo)}.txt"

    from io import BytesIO
    return send_file(
        BytesIO(contenido.encode("utf-8")),
        mimetype="text/plain; charset=utf-8",
        as_attachment=True,
        download_name=nombre,
    )


@bp.route("/tareas/<int:tarea_id>/export/pdf", methods=["GET"])
@jwt_required()
def exportar_tarea_pdf(tarea_id):
    usuario_id = int(get_jwt_identity())
    tarea = Tarea.query.filter_by(id=tarea_id, usuario_id=usuario_id).first()
    if not tarea:
        return jsonify({"error": f"No existe una tarea con ID {tarea_id}."}), 404

    usuario = _get_usuario_actual()
    pdf_bytes = exports.generar_pdf_tarea(tarea, usuario.email)
    nombre = f"tarea_{tarea.id}_{exports.sanitizar_nombre(tarea.titulo)}.pdf"

    from io import BytesIO
    return send_file(
        BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=nombre,
    )


@bp.route("/tareas/<int:tarea_id>/export/excel", methods=["GET"])
@jwt_required()
def exportar_tarea_excel(tarea_id):
    usuario_id = int(get_jwt_identity())
    tarea = Tarea.query.filter_by(id=tarea_id, usuario_id=usuario_id).first()
    if not tarea:
        return jsonify({"error": f"No existe una tarea con ID {tarea_id}."}), 404

    usuario = _get_usuario_actual()
    xlsx_bytes = exports.generar_excel_tarea(tarea, usuario.email)
    nombre = f"tarea_{tarea.id}_{exports.sanitizar_nombre(tarea.titulo)}.xlsx"

    from io import BytesIO
    return send_file(
        BytesIO(xlsx_bytes),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=nombre,
    )

# ====================================================
# PATCH /tareas/reordenar - Actualizar el orden de todas las tareas
# ====================================================
@bp.route("/tareas/reordenar", methods=["PATCH"])
@jwt_required()
def reordenar_tareas():
    """
    Recibe una lista de IDs en el nuevo orden.
    Ejemplo: {"orden": [3, 1, 5, 2, 4]}
    """
    usuario_id = int(get_jwt_identity())

    if not request.is_json:
        return jsonify({"error": "El Content-Type debe ser application/json."}), 400

    data = request.get_json()
    orden_ids = data.get("orden")

    if not isinstance(orden_ids, list) or not orden_ids:
        return jsonify({"error": "El campo 'orden' debe ser una lista de IDs."}), 400

    # Verificar que todas las tareas pertenezcan al usuario
    tareas_usuario = Tarea.query.filter_by(usuario_id=usuario_id).all()
    ids_usuario = {t.id for t in tareas_usuario}

    if not set(orden_ids).issubset(ids_usuario):
        return jsonify({"error": "Una o más tareas no te pertenecen."}), 403

    # Actualizar el orden
    for i, tarea_id in enumerate(orden_ids):
        tarea = next((t for t in tareas_usuario if t.id == tarea_id), None)
        if tarea:
            tarea.orden = i

    db.session.commit()

    return jsonify({"mensaje": "Orden actualizado correctamente."}), 200

# ====================================================
# GET /tareas/papelera - Listar tareas eliminadas
# ====================================================
@bp.route("/tareas/papelera", methods=["GET"])
@jwt_required()
def listar_papelera():
    usuario_id = int(get_jwt_identity())
    tareas = Tarea.query.filter_by(usuario_id=usuario_id, eliminada=True)\
        .order_by(Tarea.fecha_eliminacion.desc()).all()

    return jsonify([t.to_dict() for t in tareas]), 200


# ====================================================
# POST /tareas/<id>/restaurar - Restaurar una tarea
# ====================================================
@bp.route("/tareas/<int:tarea_id>/restaurar", methods=["POST"])
@jwt_required()
def restaurar_tarea(tarea_id):
    usuario_id = int(get_jwt_identity())
    tarea = Tarea.query.filter_by(id=tarea_id, usuario_id=usuario_id, eliminada=True).first()

    if not tarea:
        return jsonify({"error": f"No existe una tarea eliminada con ID {tarea_id}."}), 404

    # Calcular el próximo orden (al final de la lista)
    ultimo = Tarea.query.filter_by(usuario_id=usuario_id, eliminada=False)\
        .order_by(Tarea.orden.desc()).first()
    tarea.orden = (ultimo.orden + 1) if ultimo else 0

    tarea.eliminada = False
    tarea.fecha_eliminacion = None
    db.session.commit()

    return jsonify(tarea.to_dict()), 200

# ====================================================
# DELETE /tareas/<id>/definitivo - Eliminar permanentemente
# ====================================================
@bp.route("/tareas/<int:tarea_id>/definitivo", methods=["DELETE"])
@jwt_required()
def eliminar_definitivo(tarea_id):
    usuario_id = int(get_jwt_identity())
    tarea = Tarea.query.filter_by(id=tarea_id, usuario_id=usuario_id, eliminada=True).first()

    if not tarea:
        return jsonify({"error": f"No existe una tarea eliminada con ID {tarea_id}."}), 404

    db.session.delete(tarea)
    db.session.commit()

    return jsonify({"mensaje": f"Tarea {tarea_id} eliminada permanentemente."}), 200


# ====================================================
# DELETE /tareas/papelera/vaciar - Vaciar la papelera
# ====================================================
@bp.route("/tareas/papelera/vaciar", methods=["DELETE"])
@jwt_required()
def vaciar_papelera():
    usuario_id = int(get_jwt_identity())
    eliminadas = Tarea.query.filter_by(usuario_id=usuario_id, eliminada=True).all()

    count = len(eliminadas)
    for t in eliminadas:
        db.session.delete(t)
    db.session.commit()

    return jsonify({"mensaje": f"{count} tarea(s) eliminada(s) permanentemente."}), 200