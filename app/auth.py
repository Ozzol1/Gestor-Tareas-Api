import secrets
from datetime import datetime, timezone, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import db
from app.models import Usuario
from app.validators import (
    validar_registro,
    validar_login,
    validar_olvide_password,
    validar_reset_password,
)
from app import email_service

bp = Blueprint("auth", __name__, url_prefix="/auth")


# ====================================================
# POST /auth/registro
# ====================================================
@bp.route("/registro", methods=["POST"])
def registro():
    if not request.is_json:
        return jsonify({"error": "El Content-Type debe ser application/json."}), 400

    data = request.get_json()
    es_valido, error = validar_registro(data)
    if not es_valido:
        return jsonify({"error": error}), 400

    email = data["email"].strip().lower()

    if Usuario.query.filter_by(email=email).first():
        return jsonify({"error": "El email ya está registrado."}), 409

    nuevo = Usuario(email=email)
    nuevo.set_password(data["password"])
    db.session.add(nuevo)
    db.session.commit()

    return jsonify({
        "mensaje": "Usuario registrado correctamente.",
        "usuario": nuevo.to_dict()
    }), 201


# ====================================================
# POST /auth/login
# ====================================================
@bp.route("/login", methods=["POST"])
def login():
    if not request.is_json:
        return jsonify({"error": "El Content-Type debe ser application/json."}), 400

    data = request.get_json()
    es_valido, error = validar_login(data)
    if not es_valido:
        return jsonify({"error": error}), 400

    email = data["email"].strip().lower()
    usuario = Usuario.query.filter_by(email=email).first()

    if not usuario or not usuario.check_password(data["password"]):
        return jsonify({"error": "Credenciales inválidas."}), 401

    access_token = create_access_token(identity=str(usuario.id))

    return jsonify({
        "mensaje": "Login exitoso.",
        "access_token": access_token,
        "usuario": usuario.to_dict()
    }), 200


# ====================================================
# GET /auth/perfil
# ====================================================
@bp.route("/perfil", methods=["GET"])
@jwt_required()
def perfil():
    usuario_id = int(get_jwt_identity())
    usuario = db.session.get(Usuario, usuario_id)
    if not usuario:
        return jsonify({"error": "Usuario no encontrado."}), 404
    return jsonify(usuario.to_dict()), 200


# ====================================================
# POST /auth/olvide-password
# ====================================================
@bp.route("/olvide-password", methods=["POST"])
def olvide_password():
    """
    Recibe un email, genera un token y envía un email con el enlace.
    SIEMPRE devuelve 200 para no revelar si el email existe o no.
    """
    if not request.is_json:
        return jsonify({"error": "El Content-Type debe ser application/json."}), 400

    data = request.get_json()
    es_valido, error = validar_olvide_password(data)
    if not es_valido:
        return jsonify({"error": error}), 400

    email = data["email"].strip().lower()
    usuario = Usuario.query.filter_by(email=email).first()

    # Respuesta genérica por seguridad
    respuesta_ok = {
        "mensaje": "Si el email está registrado, recibirás un enlace de recuperación en breve."
    }

    if not usuario:
        # No revelamos que el email no existe
        return jsonify(respuesta_ok), 200

    # Generar token seguro y expiración (1 hora)
    token = secrets.token_urlsafe(32)
    usuario.reset_token = token
    usuario.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)
    db.session.commit()

    # Enviar email
    email_service.enviar_email_recuperacion(usuario.email, token)

    return jsonify(respuesta_ok), 200


# ====================================================
# POST /auth/reset-password/<token>
# ====================================================
@bp.route("/reset-password/<token>", methods=["POST"])
def reset_password(token):
    """
    Valida el token, cambia la contraseña y limpia el token.
    """
    if not request.is_json:
        return jsonify({"error": "El Content-Type debe ser application/json."}), 400

    data = request.get_json()
    es_valido, error = validar_reset_password(data)
    if not es_valido:
        return jsonify({"error": error}), 400

    usuario = Usuario.query.filter_by(reset_token=token).first()

    if not usuario:
        return jsonify({"error": "El enlace es inválido o ya fue utilizado."}), 400

    # Verificar expiración (con timezone-aware)
    ahora = datetime.now(timezone.utc)
    expira = usuario.reset_token_expires
    if expira and expira.tzinfo is None:
        # Si la DB devuelve naive datetime, asumimos UTC
        expira = expira.replace(tzinfo=timezone.utc)

    if not expira or ahora > expira:
        # Limpiar token expirado
        usuario.reset_token = None
        usuario.reset_token_expires = None
        db.session.commit()
        return jsonify({"error": "El enlace ha expirado. Solicita uno nuevo."}), 400

    # Actualizar contraseña y limpiar token
    usuario.set_password(data["password"])
    usuario.reset_token = None
    usuario.reset_token_expires = None
    db.session.commit()

    return jsonify({"mensaje": "Contraseña actualizada correctamente. Ya puedes iniciar sesión."}), 200