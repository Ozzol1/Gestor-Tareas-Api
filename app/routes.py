from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Tarea, Usuario, Subtarea
from app.validators import validar_payload_tarea
from app import exports
from datetime import datetime, timezone, timedelta
import calendar
from io import BytesIO
from app.models import Tarea, Usuario, Subtarea, Actividad

bp = Blueprint("tareas", __name__)


def _calcular_siguiente_fecha(fecha_str, recurrencia):
    """
    Calcula la siguiente fecha según la recurrencia.
    Devuelve string YYYY-MM-DD o None si la recurrencia no aplica.
    """
    if not fecha_str or recurrencia == "ninguna":
        return None

    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
    except ValueError:
        return None

    if recurrencia == "diaria":
        nueva = fecha + timedelta(days=1)
    elif recurrencia == "semanal":
        nueva = fecha + timedelta(weeks=1)
    elif recurrencia == "mensual":
        mes = fecha.month + 1
        anio = fecha.year
        if mes > 12:
            mes = 1
            anio += 1
        ultimo_dia = calendar.monthrange(anio, mes)[1]
        dia = min(fecha.day, ultimo_dia)
        nueva = fecha.replace(year=anio, month=mes, day=dia)
    elif recurrencia == "anual":
        try:
            nueva = fecha.replace(year=fecha.year + 1)
        except ValueError:
            nueva = fecha.replace(year=fecha.year + 1, day=28)
    else:
        return None

    return nueva.strftime("%Y-%m-%d")

def _registrar_actividad(usuario_id, accion, detalle):
    """Guarda una actividad en el historial del usuario."""
    nueva = Actividad(
        accion=accion,
        detalle=detalle,
        usuario_id=usuario_id
    )
    db.session.add(nueva)

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

    ultimo = Tarea.query.filter_by(usuario_id=usuario_id).order_by(Tarea.orden.desc()).first()
    siguiente_orden = (ultimo.orden + 1) if ultimo else 0

    nueva = Tarea(
        titulo=data["titulo"].strip(),
        descripcion=data.get("descripcion"),
        prioridad=data.get("prioridad", "media"),
        categoria=data.get("categoria", "Personal").strip(),
        recurrencia=data.get("recurrencia", "ninguna"),
        orden=siguiente_orden,
        fecha_limite=data.get("fecha_limite"),
        completada=data.get("completada", False),
        usuario_id=usuario_id,
        estado=data.get("estado", "pendiente"),
    )
    db.session.add(nueva)
    db.session.flush()  # Para obtener el ID de la tarea antes del commit

    # Procesar subtareas si vienen en el payload
    subtareas_data = data.get("subtareas", [])
    for sub in subtareas_data:
        if sub.get("texto", "").strip():
            nueva_sub = Subtarea(
                texto=sub["texto"].strip(),
                completada=sub.get("completada", False),
                tarea_id=nueva.id
            )
            db.session.add(nueva_sub)

    _registrar_actividad(usuario_id, "crear", f"Creó la tarea '{nueva.titulo}'")
    db.session.commit()
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

    estaba_pendiente = not tarea.completada
    se_marca_completada = data.get("completada") is True and estaba_pendiente

    # 1. Aplicar cambios a los campos normales
    for campo in ["titulo", "descripcion", "completada", "prioridad", "categoria", "recurrencia", "fecha_limite", "estado"]:
        if campo in data:
            valor = data[campo]
            if campo == "titulo":
                valor = valor.strip()
            elif campo == "categoria":
                valor = valor.strip() if valor else "Personal"
            setattr(tarea, campo, valor)

    # 2. Sincronizar estado y completada
    if "estado" in data:
        if data["estado"] == "completado":
            tarea.completada = True
        else:
            tarea.completada = False
    elif "completada" in data:
        if data["completada"] == True:
            tarea.estado = "completado"
        else:
            tarea.estado = "pendiente"

    # 3. Procesar subtareas
    if "subtareas" in data:
        for sub in tarea.subtareas:
            db.session.delete(sub)
        for sub in data["subtareas"]:
            if sub.get("texto", "").strip():
                nueva_sub = Subtarea(
                    texto=sub["texto"].strip(),
                    completada=sub.get("completada", False),
                    tarea_id=tarea.id
                )
                db.session.add(nueva_sub)

    # 4. Manejar recurrencia
    nueva_tarea = None
    if se_marca_completada and tarea.recurrencia != "ninguna":
        siguiente_fecha = _calcular_siguiente_fecha(tarea.fecha_limite, tarea.recurrencia)

        if siguiente_fecha:
            ultimo = Tarea.query.filter_by(usuario_id=usuario_id, eliminada=False)\
                .order_by(Tarea.orden.desc()).first()
            siguiente_orden = (ultimo.orden + 1) if ultimo else 0

            nueva_tarea = Tarea(
                titulo=tarea.titulo,
                descripcion=tarea.descripcion,
                prioridad=tarea.prioridad,
                categoria=tarea.categoria,
                recurrencia=tarea.recurrencia,
                orden=siguiente_orden,
                fecha_limite=siguiente_fecha,
                completada=False,
                usuario_id=usuario_id,
            )
            db.session.add(nueva_tarea)
            
            # Auto-archivar la completada
            tarea.eliminada = True
            tarea.fecha_eliminacion = datetime.now(timezone.utc)

    # 5. Registrar actividad en el historial
    if se_marca_completada:
        _registrar_actividad(usuario_id, "completar", f"Completó la tarea '{tarea.titulo}'")
    elif "titulo" in data or "descripcion" in data or "prioridad" in data or "categoria" in data:
        _registrar_actividad(usuario_id, "editar", f"Editó la tarea '{tarea.titulo}'")

    db.session.commit()

    respuesta = tarea.to_dict()
    if nueva_tarea:
        respuesta["nueva_tarea_recurrente"] = nueva_tarea.to_dict()

    return jsonify(respuesta), 200

# ====================================================
# ELIMINAR (soft delete)
# ====================================================
@bp.route("/tareas/<int:tarea_id>", methods=["DELETE"])
@jwt_required()
def eliminar_tarea(tarea_id):
    usuario_id = int(get_jwt_identity())
    tarea = Tarea.query.filter_by(id=tarea_id, usuario_id=usuario_id, eliminada=False).first()
    if not tarea:
        return jsonify({"error": f"No existe una tarea con ID {tarea_id}."}), 404

    tarea.eliminada = True
    tarea.fecha_eliminacion = datetime.now(timezone.utc)
    _registrar_actividad(usuario_id, "eliminar", f"Moviste a la papelera la tarea '{tarea.titulo}'")
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
        BytesIO(pdf_bytes),
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
        BytesIO(xlsx_bytes),
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

    return send_file(
        BytesIO(xlsx_bytes),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=nombre,
    )


# ====================================================
# REORDENAR TAREAS (drag & drop)
# ====================================================
@bp.route("/tareas/reordenar", methods=["PATCH"])
@jwt_required()
def reordenar_tareas():
    usuario_id = int(get_jwt_identity())

    if not request.is_json:
        return jsonify({"error": "El Content-Type debe ser application/json."}), 400

    data = request.get_json()
    orden_ids = data.get("orden")

    if not isinstance(orden_ids, list) or not orden_ids:
        return jsonify({"error": "El campo 'orden' debe ser una lista de IDs."}), 400

    tareas_usuario = Tarea.query.filter_by(usuario_id=usuario_id).all()
    ids_usuario = {t.id for t in tareas_usuario}

    if not set(orden_ids).issubset(ids_usuario):
        return jsonify({"error": "Una o más tareas no te pertenecen."}), 403

    for i, tarea_id in enumerate(orden_ids):
        tarea = next((t for t in tareas_usuario if t.id == tarea_id), None)
        if tarea:
            tarea.orden = i

    db.session.commit()

    return jsonify({"mensaje": "Orden actualizado correctamente."}), 200


# ====================================================
# PAPELERA - Listar
# ====================================================
@bp.route("/tareas/papelera", methods=["GET"])
@jwt_required()
def listar_papelera():
    usuario_id = int(get_jwt_identity())
    tareas = Tarea.query.filter_by(usuario_id=usuario_id, eliminada=True)\
        .order_by(Tarea.fecha_eliminacion.desc()).all()

    return jsonify([t.to_dict() for t in tareas]), 200


# ====================================================
# PAPELERA - Restaurar
# ====================================================
@bp.route("/tareas/<int:tarea_id>/restaurar", methods=["POST"])
@jwt_required()
def restaurar_tarea(tarea_id):
    usuario_id = int(get_jwt_identity())
    tarea = Tarea.query.filter_by(id=tarea_id, usuario_id=usuario_id, eliminada=True).first()

    if not tarea:
        return jsonify({"error": f"No existe una tarea eliminada con ID {tarea_id}."}), 404

    ultimo = Tarea.query.filter_by(usuario_id=usuario_id, eliminada=False)\
        .order_by(Tarea.orden.desc()).first()
    tarea.orden = (ultimo.orden + 1) if ultimo else 0

    tarea.eliminada = False
    tarea.fecha_eliminacion = None
    db.session.commit()

    return jsonify(tarea.to_dict()), 200


# ====================================================
# PAPELERA - Eliminar definitivamente
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
# PAPELERA - Vaciar
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

# ====================================================
# GET /actividades - Obtener historial de actividad
# ====================================================
@bp.route("/actividades", methods=["GET"])
@jwt_required()
def listar_actividades():
    usuario_id = int(get_jwt_identity())
    
    # Traer las últimas 50 actividades ordenadas por fecha descendente
    actividades = Actividad.query.filter_by(usuario_id=usuario_id)\
        .order_by(Actividad.fecha_creacion.desc()).limit(50).all()
        
    return jsonify([a.to_dict() for a in actividades]), 200