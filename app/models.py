from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class Usuario(db.Model):
    """Modelo de Usuario para autenticación."""
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    fecha_registro = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Recuperación de contraseña
    reset_token = db.Column(db.String(100), nullable=True, index=True)
    reset_token_expires = db.Column(db.DateTime, nullable=True)
    # Verificación de email
    email_verificado = db.Column(db.Boolean, default=False, nullable=False)
    verificacion_token = db.Column(db.String(100), nullable=True, index=True)
    verificacion_token_expires = db.Column(db.DateTime, nullable=True)

    tareas = db.relationship("Tarea", backref="usuario", lazy=True)
    actividades = db.relationship("Actividad", backref="usuario", lazy=True, cascade="all, delete-orphan")    

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "fecha_registro": self.fecha_registro.isoformat() if self.fecha_registro else None,
            "email_verificado": self.email_verificado,
        }

    def __repr__(self):
        return f"<Usuario {self.id}: {self.email}>"


class Tarea(db.Model):
    __tablename__ = "tareas"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    completada = db.Column(db.Boolean, default=False, nullable=False)
    prioridad = db.Column(db.String(10), default="media", nullable=False)
    categoria = db.Column(db.String(50), nullable=False, default="Personal")
    recurrencia = db.Column(db.String(20), default="ninguna", nullable=False)
    orden = db.Column(db.Integer, default=0, nullable=False)
    eliminada = db.Column(db.Boolean, default=False, nullable=False, index=True)
    fecha_eliminacion = db.Column(db.DateTime, nullable=True)
    fecha_limite = db.Column(db.String(10), nullable=True)
    fecha_creacion = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    subtareas = db.relationship("Subtarea", backref="tarea", cascade="all, delete-orphan", lazy=True)

    def to_dict(self):
        return {
            "recurrencia": self.recurrencia,
            "id": self.id,
            "titulo": self.titulo,
            "descripcion": self.descripcion,
            "completada": self.completada,
            "prioridad": self.prioridad,
            "categoria": self.categoria,
            "orden": self.orden,
            "eliminada": self.eliminada,
            "fecha_eliminacion": self.fecha_eliminacion.isoformat() if self.fecha_eliminacion else None,
            "fecha_limite": self.fecha_limite,
            "fecha_creacion": self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            "usuario_id": self.usuario_id,
            "subtareas": [s.to_dict() for s in self.subtareas],  # ← NUEVO
        }

    def __repr__(self):
        return f"<Tarea {self.id}: {self.titulo}>"

class Subtarea(db.Model):
    __tablename__ = "subtareas"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    texto = db.Column(db.String(200), nullable=False)
    completada = db.Column(db.Boolean, default=False, nullable=False)
    tarea_id = db.Column(db.Integer, db.ForeignKey("tareas.id"), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "texto": self.texto,
            "completada": self.completada,
        }
class Actividad(db.Model):
    __tablename__ = "actividades"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    accion = db.Column(db.String(50), nullable=False)  # "crear", "editar", "completar", "eliminar"
    detalle = db.Column(db.String(255), nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "accion": self.accion,
            "detalle": self.detalle,
            "fecha_creacion": self.fecha_creacion.isoformat() if self.fecha_creacion else None,
        }        