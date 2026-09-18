import logging
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tareas.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JSON_SORT_KEYS"] = False

    db.init_app(app)

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

    from app.routes import bp as tareas_bp
    app.register_blueprint(tareas_bp)

    @app.route("/ping")
    def ping():
        return {"mensaje": "pong", "status": "ok"}

    return app