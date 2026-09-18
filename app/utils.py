import re

# Regex simple para validar emails (suficiente para este proyecto)
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def email_valido(email):
    """Devuelve True si el email tiene formato válido."""
    if not isinstance(email, str):
        return False
    return bool(EMAIL_REGEX.match(email.strip()))


def password_valida(password):
    """Devuelve True si la contraseña tiene mínimo 8 caracteres."""
    if not isinstance(password, str):
        return False
    return len(password) >= 8