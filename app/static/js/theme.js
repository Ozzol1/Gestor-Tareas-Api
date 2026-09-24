// ====================================================
// SISTEMA DE TEMA (MODO CLARO / OSCURO)
// ====================================================
(function () {
    const STORAGE_KEY = "theme";
    const DEFAULT_THEME = "light";

    // Aplicar tema ANTES de que el DOM esté listo (evita el "flash")
    const guardado = localStorage.getItem(STORAGE_KEY) || DEFAULT_THEME;
    document.documentElement.setAttribute("data-theme", guardado);
})();

function toggleTheme() {
    const actual = document.documentElement.getAttribute("data-theme") || "light";
    const nuevo = actual === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", nuevo);
    localStorage.setItem("theme", nuevo);
    actualizarIconoTema();
}

function actualizarIconoTema() {
    const actual = document.documentElement.getAttribute("data-theme") || "light";
    document.querySelectorAll(".theme-toggle .icono-tema").forEach(el => {
        el.textContent = actual === "dark" ? "☀️" : "🌙";
    });
    document.querySelectorAll(".theme-toggle").forEach(btn => {
        btn.setAttribute(
            "title",
            actual === "dark" ? "Cambiar a modo claro" : "Cambiar a modo oscuro"
        );
        btn.setAttribute(
            "aria-label",
            actual === "dark" ? "Cambiar a modo claro" : "Cambiar a modo oscuro"
        );
    });
}

document.addEventListener("DOMContentLoaded", () => {
    actualizarIconoTema();
    document.querySelectorAll(".theme-toggle").forEach(btn => {
        btn.addEventListener("click", toggleTheme);
    });
});