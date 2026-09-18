import os
import logging
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

db = SQLAlchemy()
jwt = JWTManager()


def create_app(config_override=None):
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tareas.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JSON_SORT_KEYS"] = False

    # Aplicar configuración extra (para tests)
    if config_override:
        app.config.update(config_override)

    # ... el resto igual

    # ----------------------------------------------------
    # CONFIGURACIÓN DE JWT
    # ----------------------------------------------------
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "clave-de-desarrollo-insegura")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", 3600))

    db.init_app(app)
    jwt.init_app(app)

    # ----------------------------------------------------
    # LOGGING Y MANEJO GLOBAL DE ERRORES
    # ----------------------------------------------------
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("app.log"),
            logging.StreamHandler()
        ]
    )

    @app.errorhandler(500)
    def error_interno(error):
        app.logger.error(f"Error interno: {error}")
        return jsonify({
            "error": "Error interno del servidor.",
            "detalle": "Contacte al administrador si el problema persiste."
        }), 500

    @app.errorhandler(404)
    def ruta_no_encontrada(error):
        return jsonify({"error": "Ruta no encontrada."}), 404

    # ----------------------------------------------------
    # MODELOS Y RUTAS
    # ----------------------------------------------------
    from app import models
    with app.app_context():
        db.create_all()

    # ----------------------------------------------------
    # BLUEPRINTS
    # ----------------------------------------------------
    from app.routes import bp as tareas_bp
    app.register_blueprint(tareas_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    @app.route("/ping")
    def ping():
        return {"mensaje": "pong", "status": "ok"}

    return app