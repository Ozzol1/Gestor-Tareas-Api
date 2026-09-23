// URL base de la API (misma origin porque está en el mismo deploy)
const API_URL = "";

/**
 * Wrapper de fetch que añade el token JWT automáticamente.
 */
async function apiFetch(endpoint, options = {}) {
    const token = localStorage.getItem("access_token");

    const headers = {
        "Content-Type": "application/json",
        ...(options.headers || {}),
    };

    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_URL}${endpoint}`, {
        ...options,
        headers,
    });

    // Si el token expiró o es inválido, redirigimos a login
    if (response.status === 401) {
        localStorage.removeItem("access_token");
        if (window.location.pathname !== "/login") {
            window.location.href = "/login";
        }
        throw new Error("Sesión expirada. Inicia sesión de nuevo.");
    }

    const data = await response.json().catch(() => ({}));
    return { ok: response.ok, status: response.status, data };
}

function mostrarError(mensaje) {
    const el = document.getElementById("mensaje-error");
    if (el) {
        el.textContent = mensaje;
        el.classList.remove("hidden");
        setTimeout(() => el.classList.add("hidden"), 5000);
    }
}

function ocultarError() {
    const el = document.getElementById("mensaje-error");
    if (el) el.classList.add("hidden");
}