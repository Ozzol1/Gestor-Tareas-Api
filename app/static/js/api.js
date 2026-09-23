// URL base de la API (misma origin porque está en el mismo deploy)
const API_URL = "";

/**
 * Wrapper de fetch que añade el token JWT automáticamente.
 */
async function apiFetch(endpoint, options = {}) {
    const { skipAuthRedirect = false, ...fetchOptions } = options;
    const token = localStorage.getItem("access_token");

    const headers = {
        "Content-Type": "application/json",
        ...(fetchOptions.headers || {}),
    };

    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    let response;
    try {
        response = await fetch(`${API_URL}${endpoint}`, {
            ...fetchOptions,
            headers,
            cache: "no-store", // 👈 evita respuestas cacheadas
        });
    } catch (err) {
        return {
            ok: false,
            status: 0,
            data: { error: "No se pudo conectar con el servidor. Verifica tu conexión." },
        };
    }

    if (response.status === 401 && !skipAuthRedirect) {
        localStorage.removeItem("access_token");
        if (window.location.pathname !== "/login") {
            window.location.href = "/login";
        }
    }

    let data = {};
    try {
        data = await response.json();
    } catch (e) {
        data = {};
    }

    return { ok: response.ok, status: response.status, data };
}

// ----------------------------------------------------
// MENSAJES
// ----------------------------------------------------
let timeoutExito = null;

function mostrarError(mensaje) {
    const el = document.getElementById("mensaje-error");
    if (!el) return;
    el.textContent = mensaje;
    el.classList.remove("hidden");
    // También ocultamos el mensaje de éxito si aparece uno nuevo
    ocultarExito();
}

function ocultarError() {
    const el = document.getElementById("mensaje-error");
    if (el) el.classList.add("hidden");
}

function mostrarExito(mensaje) {
    const el = document.getElementById("mensaje-exito");
    if (!el) return;
    el.textContent = mensaje;
    el.classList.remove("hidden");
    ocultarError();

    // Auto-ocultar después de 3 segundos
    if (timeoutExito) clearTimeout(timeoutExito);
    timeoutExito = setTimeout(() => {
        el.classList.add("hidden");
    }, 3000);
}

function ocultarExito() {
    const el = document.getElementById("mensaje-exito");
    if (el) el.classList.add("hidden");
    if (timeoutExito) {
        clearTimeout(timeoutExito);
        timeoutExito = null;
    }
}