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
            cache: "no-store",
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

// ====================================================
// SISTEMA DE MENSAJES CON ANIMACIÓN DE SALIDA SUAVE
// ====================================================
let timeoutExito = null;

/**
 * Oculta un elemento con animación de fade-out.
 */
function _ocultarConAnimacion(el) {
    if (!el || el.classList.contains("hidden")) return;

    // Quitar fade-out previo si lo hubiera
    el.classList.remove("fade-out");
    // Forzar reflow para reiniciar la animación
    void el.offsetWidth;
    // Aplicar animación
    el.classList.add("fade-out");

    el.addEventListener("animationend", () => {
        el.classList.add("hidden");
        el.classList.remove("fade-out");
    }, { once: true });
}

/**
 * Muestra un elemento reseteando su estado y animaciones previas.
 */
function _prepararParaMostrar(el, mensaje) {
    if (!el) return;

    // Cancelar cualquier animación de salida en curso
    el.classList.remove("hidden", "fade-out");
    // Forzar reflow para reiniciar la animación de entrada
    void el.offsetWidth;

    el.textContent = mensaje;
}

function mostrarError(mensaje) {
    const el = document.getElementById("mensaje-error");
    if (!el) return;

    _prepararParaMostrar(el, mensaje);
    ocultarExito();
}

function ocultarError() {
    const el = document.getElementById("mensaje-error");
    if (el) _ocultarConAnimacion(el);
}

function mostrarExito(mensaje) {
    const el = document.getElementById("mensaje-exito");
    if (!el) return;

    _prepararParaMostrar(el, mensaje);
    ocultarError();

    // Auto-ocultar después de 3 segundos con animación suave
    if (timeoutExito) clearTimeout(timeoutExito);
    timeoutExito = setTimeout(() => {
        _ocultarConAnimacion(el);
        timeoutExito = null;
    }, 3000);
}

function ocultarExito() {
    const el = document.getElementById("mensaje-exito");
    if (el) _ocultarConAnimacion(el);
    if (timeoutExito) {
        clearTimeout(timeoutExito);
        timeoutExito = null;
    }
}