from datetime import datetime
from app.utils import email_valido, password_valida

PRIORIDADES_VALIDAS = ["alta", "media", "baja"]


def validar_payload_tarea(data, parcial=False):
    if not isinstance(data, dict):
        return False, "El cuerpo debe ser un objeto JSON válido."

    if not parcial or "titulo" in data:
        if not parcial and "titulo" not in data:
            return False, "El campo 'titulo' es obligatorio."
        if "titulo" in data:
            if not isinstance(data["titulo"], str) or not data["titulo"].strip():
                return False, "El campo 'titulo' no puede estar vacío."

    if "prioridad" in data:
        if data["prioridad"] not in PRIORIDADES_VALIDAS:
            return False, f"Prioridad inválida. Debe ser una de: {', '.join(PRIORIDADES_VALIDAS)}."

    if "fecha_limite" in data and data["fecha_limite"] is not None:
        try:
            datetime.strptime(data["fecha_limite"], "%Y-%m-%d")
        except (ValueError, TypeError):
            return False, "El campo 'fecha_limite' debe tener formato YYYY-MM-DD."

    if "completada" in data and not isinstance(data["completada"], bool):
        return False, "El campo 'completada' debe ser true o false."

    if "descripcion" in data and data["descripcion"] is not None:
        if not isinstance(data["descripcion"], str):
            return False, "El campo 'descripcion' debe ser texto."

    return True, None


def validar_id(id_str):
    try:
        id_int = int(id_str)
        if id_int <= 0:
            return None
        return id_int
    except (ValueError, TypeError):
        return None


def validar_registro(data):
    if not isinstance(data, dict):
        return False, "El cuerpo debe ser un objeto JSON válido."

    email = data.get("email")
    password = data.get("password")

    if not email:
        return False, "El campo 'email' es obligatorio."
    if not email_valido(email):
        return False, "El formato del email no es válido."

    if not password:
        return False, "El campo 'password' es obligatorio."
    if not password_valida(password):
        return False, "La contraseña debe tener al menos 8 caracteres."

    return True, None


def validar_login(data):
    if not isinstance(data, dict):
        return False, "El cuerpo debe ser un objeto JSON válido."

    if not data.get("email"):
        return False, "El campo 'email' es obligatorio."
    if not data.get("password"):
        return False, "El campo 'password' es obligatorio."

    return True, None


def validar_olvide_password(data):
    if not isinstance(data, dict):
        return False, "El cuerpo debe ser un objeto JSON válido."

    email = data.get("email")
    if not email:
        return False, "El campo 'email' es obligatorio."
    if not email_valido(email):
        return False, "El formato del email no es válido."

    return True, None


def validar_reset_password(data):
    if not isinstance(data, dict):
        return False, "El cuerpo debe ser un objeto JSON válido."

    password = data.get("password")
    if not password:
        return False, "El campo 'password' es obligatorio."
    if not password_valida(password):
        return False, "La contraseña debe tener al menos 8 caracteres."

    return True, None