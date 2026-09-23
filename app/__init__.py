import os
import logging
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
jwt = JWTManager()


def create_app(config_override=None):
    app = Flask(__name__)

    database_url = os.getenv("DATABASE_URL", "sqlite:///tareas.db")
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JSON_SORT_KEYS"] = False

    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "clave-de-desarrollo-insegura")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", 3600))

    if config_override:
        app.config.update(config_override)

    db.init_app(app)
    jwt.init_app(app)

    # Logging a consola (sin FileHandler para Docker)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
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

    from app import models
    with app.app_context():
        db.create_all()

    from app.routes import bp as tareas_bp
    app.register_blueprint(tareas_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    @app.route("/ping")
    def ping():
        return {"mensaje": "pong", "status": "ok"}

    @app.route("/health")
    def health():
        return {"status": "ok"}, 200
    # ----------------------------------------------------
    # RUTAS DEL FRONTEND
    # ----------------------------------------------------
    from flask import render_template

    @app.route("/")
    @app.route("/login")
    def login_page():
        return render_template("login.html")

    @app.route("/registro")
    def registro_page():
        return render_template("registro.html")

    @app.route("/dashboard")
    def dashboard_page():
        return render_template("dashboard.html")
    
    return app