from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tareas.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JSON_SORT_KEYS"] = False

    db.init_app(app)

    from app import models
    with app.app_context():
        db.create_all()
        
    # Registramos el Blueprint con los endpoints
    from app.routes import bp as tareas_bp
    app.register_blueprint(tareas_bp)

    @app.route("/ping")
    def ping():
        return {"mensaje": "pong", "status": "ok"}

    return app