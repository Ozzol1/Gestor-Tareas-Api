from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Tarea, Usuario
from app.validators import validar_payload_tarea
from app import exports

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
    query = Tarea.query.filter_by(usuario_id=usuario_id)

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

    nueva = Tarea(
        titulo=data["titulo"].strip(),
        descripcion=data.get("descripcion"),
        prioridad=data.get("prioridad", "media"),
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

    for campo in ["titulo", "descripcion", "completada", "prioridad", "fecha_limite"]:
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
    tarea = Tarea.query.filter_by(id=tarea_id, usuario_id=usuario_id).first()
    if not tarea:
        return jsonify({"error": f"No existe una tarea con ID {tarea_id}."}), 404
    db.session.delete(tarea)
    db.session.commit()
    return jsonify({"mensaje": f"Tarea {tarea_id} eliminada correctamente."}), 200


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