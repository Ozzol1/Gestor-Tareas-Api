// ====================================================
// ESTADO GLOBAL
// ====================================================
let tareas = [];
let filtroActual = "todas";
let tareaEditandoId = null;

// ====================================================
// INICIALIZACIÓN
// ====================================================
document.addEventListener("DOMContentLoaded", async () => {
    const token = localStorage.getItem("access_token");
    if (!token) {
        window.location.href = "/login";
        return;
    }

    // Asegurar que el modal esté cerrado al cargar
    document.getElementById("modal-editar").classList.add("hidden");
    tareaEditandoId = null;

    cargarPerfil();
    await cargarTareas();
    configurarEventos();
});

async function cargarPerfil() {
    const { ok, data } = await apiFetch("/auth/perfil");
    if (ok) {
        document.getElementById("user-email").textContent = data.email;
    }
}

// ====================================================
// CARGAR TAREAS
// ====================================================
async function cargarTareas() {
    const lista = document.getElementById("lista-tareas");
    lista.innerHTML = '<div class="loading">Cargando tareas...</div>';

    const { ok, data } = await apiFetch("/tareas");

    if (ok) {
        tareas = data;
        renderizarTareas();
    } else {
        lista.innerHTML = '<div class="loading">Error al cargar tareas</div>';
    }
}

// ====================================================
// RENDERIZAR
// ====================================================
function renderizarTareas() {
    const lista = document.getElementById("lista-tareas");

    let filtradas = tareas;
    if (filtroActual === "pendientes") {
        filtradas = tareas.filter(t => !t.completada);
    } else if (filtroActual === "completadas") {
        filtradas = tareas.filter(t => t.completada);
    }

    if (filtradas.length === 0) {
        lista.innerHTML = '<div class="empty-state">📭 No hay tareas que mostrar</div>';
        return;
    }

    lista.innerHTML = filtradas.map(t => {
        const clases = ["tarea-card"];
        if (t.completada) clases.push("completada");
        clases.push(`prioridad-${t.prioridad}`);

        return `
            <div class="${clases.join(' ')}">
                <div class="tarea-header">
                    <h3>${escapeHtml(t.titulo)}</h3>
                    <span class="badge badge-${t.prioridad}">${t.prioridad}</span>
                </div>
                ${t.descripcion ? `<p class="tarea-desc">${escapeHtml(t.descripcion)}</p>` : ""}
                ${t.fecha_limite ? `<p class="tarea-fecha">📅 ${t.fecha_limite}</p>` : ""}
                <div class="tarea-actions">
                    <button class="btn-toggle" data-id="${t.id}">
                        ${t.completada ? "↩️ Reabrir" : "✅ Completar"}
                    </button>
                    <button class="btn-edit" data-id="${t.id}">✏️ Editar</button>
                    <button class="btn-delete" data-id="${t.id}">🗑️ Eliminar</button>
                </div>
            </div>
        `;
    }).join("");

    lista.querySelectorAll(".btn-toggle").forEach(btn => {
        btn.addEventListener("click", () => toggleCompletada(parseInt(btn.dataset.id)));
    });
    lista.querySelectorAll(".btn-edit").forEach(btn => {
        btn.addEventListener("click", () => abrirModalEditar(parseInt(btn.dataset.id)));
    });
    lista.querySelectorAll(".btn-delete").forEach(btn => {
        btn.addEventListener("click", () => eliminarTarea(parseInt(btn.dataset.id)));
    });
}

// ====================================================
// CREAR TAREA
// ====================================================
async function crearTarea(e) {
    e.preventDefault();
    ocultarError();

    const titulo = document.getElementById("titulo").value.trim();
    const descripcion = document.getElementById("descripcion").value.trim() || null;
    const prioridad = document.getElementById("prioridad").value;
    const fecha_limite = document.getElementById("fecha_limite").value || null;

    if (!titulo) {
        mostrarError("El título no puede estar vacío");
        return;
    }

    const boton = document.querySelector("#form-nueva-tarea button[type='submit']");
    boton.disabled = true;
    boton.textContent = "Creando...";

    const { ok, data } = await apiFetch("/tareas", {
        method: "POST",
        body: JSON.stringify({ titulo, descripcion, prioridad, fecha_limite }),
    });

    boton.disabled = false;
    boton.textContent = "Crear Tarea";

    if (ok) {
        document.getElementById("form-nueva-tarea").reset();
        tareas.push(data);
        renderizarTareas();
        mostrarExito("✅ Tarea creada exitosamente");
    } else {
        mostrarError(data.error || "Error al crear la tarea");
    }
}

// ====================================================
// TOGGLE COMPLETADA
// ====================================================
async function toggleCompletada(id) {
    const tarea = tareas.find(t => t.id === id);
    if (!tarea) return;

    const { ok, data } = await apiFetch(`/tareas/${id}`, {
        method: "PATCH",
        body: JSON.stringify({ completada: !tarea.completada }),
    });

    if (ok) {
        // Actualizar localmente sin re-fetch
        tarea.completada = !tarea.completada;
        renderizarTareas();
        mostrarExito(tarea.completada ? "✅ Tarea completada" : "↩️ Tarea reabierta");
    } else {
        mostrarError(data.error || "Error al actualizar");
    }
}

// ====================================================
// MODAL DE EDICIÓN
// ====================================================
function abrirModalEditar(id) {
    const tarea = tareas.find(t => t.id === id);
    if (!tarea) {
        console.error("No se encontró la tarea con ID:", id);
        return;
    }

    tareaEditandoId = tarea.id;

    document.getElementById("edit-id").value = tarea.id;
    document.getElementById("edit-titulo").value = tarea.titulo;
    document.getElementById("edit-descripcion").value = tarea.descripcion || "";
    document.getElementById("edit-prioridad").value = tarea.prioridad;
    document.getElementById("edit-fecha_limite").value = tarea.fecha_limite || "";

    document.getElementById("modal-editar").classList.remove("hidden");
    document.getElementById("edit-titulo").focus();
}

function cerrarModalEditar() {
    document.getElementById("modal-editar").classList.add("hidden");
    tareaEditandoId = null;
}

async function guardarEdicion(e) {
    e.preventDefault();
    ocultarError();

    const id = tareaEditandoId;

    if (!id) {
        mostrarError("Error: no se encontró el ID de la tarea");
        return;
    }

    const titulo = document.getElementById("edit-titulo").value.trim();
    const descripcion = document.getElementById("edit-descripcion").value.trim() || null;
    const prioridad = document.getElementById("edit-prioridad").value;
    const fecha_limite = document.getElementById("edit-fecha_limite").value || null;

    if (!titulo) {
        mostrarError("El título no puede estar vacío");
        return;
    }

    const boton = document.getElementById("btn-guardar-edicion");
    boton.disabled = true;
    boton.textContent = "Guardando...";

    const { ok, data } = await apiFetch(`/tareas/${id}`, {
        method: "PATCH",
        body: JSON.stringify({ titulo, descripcion, prioridad, fecha_limite }),
    });

    boton.disabled = false;
    boton.textContent = "Guardar";

    if (ok) {
        // ✅ Actualizar el array local con los datos devueltos por la API
        const index = tareas.findIndex(t => t.id === id);
        if (index !== -1) {
            tareas[index] = data;
        }

        // Cerrar modal y re-renderizar inmediatamente
        cerrarModalEditar();
        renderizarTareas();
        mostrarExito("✅ Tarea editada exitosamente");
    } else {
        mostrarError(data.error || "Error al guardar cambios");
    }
}

// ====================================================
// ELIMINAR
// ====================================================
async function eliminarTarea(id) {
    if (!confirm("¿Estás seguro de eliminar esta tarea?")) return;

    const { ok, data } = await apiFetch(`/tareas/${id}`, {
        method: "DELETE",
    });

    if (ok) {
        tareas = tareas.filter(t => t.id !== id);
        renderizarTareas();
        mostrarExito("🗑️ Tarea eliminada");
    } else {
        mostrarError(data.error || "Error al eliminar");
    }
}

// ====================================================
// FILTROS
// ====================================================
function configurarFiltros() {
    document.querySelectorAll(".filtro-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".filtro-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            filtroActual = btn.dataset.filtro;
            renderizarTareas();
        });
    });
}

// ====================================================
// EVENTOS
// ====================================================
function configurarEventos() {
    document.getElementById("form-nueva-tarea").addEventListener("submit", crearTarea);
    document.getElementById("form-editar").addEventListener("submit", guardarEdicion);
    document.getElementById("btn-cancelar-edicion").addEventListener("click", cerrarModalEditar);
    configurarFiltros();
}

// ====================================================
// UTILIDADES
// ====================================================
function escapeHtml(texto) {
    const div = document.createElement("div");
    div.textContent = texto || "";
    return div.innerHTML;
}