from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
)
from app import db
from app.models import Usuario
from app.validators import validar_registro, validar_login

bp = Blueprint("auth", __name__, url_prefix="/auth")


# ====================================================
# POST /auth/registro - Crear usuario
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

    # Verificar si ya existe
    if Usuario.query.filter_by(email=email).first():
        return jsonify({"error": "El email ya está registrado."}), 409

    # Crear usuario con password hasheada
    nuevo = Usuario(email=email)
    nuevo.set_password(data["password"])
    db.session.add(nuevo)
    db.session.commit()

    return jsonify({
        "mensaje": "Usuario registrado correctamente.",
        "usuario": nuevo.to_dict()
    }), 201


# ====================================================
# POST /auth/login - Iniciar sesión y devolver token
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

    # Credenciales inválidas (no revelamos si el email existe o no)
    if not usuario or not usuario.check_password(data["password"]):
        return jsonify({"error": "Credenciales inválidas."}), 401

    # Creamos el token JWT con el ID del usuario como identidad
    access_token = create_access_token(identity=str(usuario.id))

    return jsonify({
        "mensaje": "Login exitoso.",
        "access_token": access_token,
        "usuario": usuario.to_dict()
    }), 200


# ====================================================
# GET /auth/perfil - Ver datos del usuario autenticado
# ====================================================
@bp.route("/perfil", methods=["GET"])
@jwt_required()
def perfil():
    usuario_id = int(get_jwt_identity())
    usuario = db.session.get(Usuario, usuario_id)

    if not usuario:
        return jsonify({"error": "Usuario no encontrado."}), 404

    return jsonify(usuario.to_dict()), 200