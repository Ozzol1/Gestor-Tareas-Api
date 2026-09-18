from datetime import datetime

PRIORIDADES_VALIDAS = ["alta", "media", "baja"]


def validar_payload_tarea(data, parcial=False):
    """
    Valida el payload de una tarea.
    - parcial=False: valida que estén los campos obligatorios (para POST).
    - parcial=True: valida solo los campos que vienen (para PATCH).
    Devuelve (es_valido, mensaje_error).
    """
    if not isinstance(data, dict):
        return False, "El cuerpo debe ser un objeto JSON válido."

    # Validar título (obligatorio en POST, opcional en PATCH)
    if not parcial or "titulo" in data:
        if not parcial and "titulo" not in data:
            return False, "El campo 'titulo' es obligatorio."
        if "titulo" in data:
            if not isinstance(data["titulo"], str) or not data["titulo"].strip():
                return False, "El campo 'titulo' no puede estar vacío."

    # Validar prioridad
    if "prioridad" in data:
        if data["prioridad"] not in PRIORIDADES_VALIDAS:
            return False, f"Prioridad inválida. Debe ser una de: {', '.join(PRIORIDADES_VALIDAS)}."

    # Validar fecha_limite
    if "fecha_limite" in data and data["fecha_limite"] is not None:
        try:
            datetime.strptime(data["fecha_limite"], "%Y-%m-%d")
        except (ValueError, TypeError):
            return False, "El campo 'fecha_limite' debe tener formato YYYY-MM-DD."

    # Validar completada
    if "completada" in data and not isinstance(data["completada"], bool):
        return False, "El campo 'completada' debe ser true o false."

    # Validar descripcion
    if "descripcion" in data and data["descripcion"] is not None:
        if not isinstance(data["descripcion"], str):
            return False, "El campo 'descripcion' debe ser texto."

    return True, None


def validar_id(id_str):
    """Valida que el ID sea un número entero positivo."""
    try:
        id_int = int(id_str)
        if id_int <= 0:
            return None
        return id_int
    except (ValueError, TypeError):
        return None