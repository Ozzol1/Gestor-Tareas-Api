// ====================================================
// ESTADO GLOBAL
// ====================================================
let tareas = [];
let filtroActual = "todas";
let tareaEditandoId = null;
let tareaExportandoId = null;
let tareaEliminandoId = null;

// ====================================================
// INICIALIZACIÓN
// ====================================================
document.addEventListener("DOMContentLoaded", async () => {
    const token = localStorage.getItem("access_token");
    if (!token) {
        window.location.href = "/login";
        return;
    }

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
// CARGAR TAREAS (CON SKELETON LOADER)
// ====================================================
async function cargarTareas() {
    const lista = document.getElementById("lista-tareas");
    lista.innerHTML = renderizarSkeletons();

    const { ok, data } = await apiFetch("/tareas");

    if (ok) {
        tareas = data;
        renderizarTareas();
    } else {
        lista.innerHTML = '<div class="loading">Error al cargar tareas</div>';
        mostrarToast("Error al cargar las tareas", "error");
    }
}

function renderizarSkeletons() {
    const skeleton = `
        <div class="skeleton-card">
            <div class="skeleton-header">
                <div class="skeleton-line skeleton-titulo"></div>
                <div class="skeleton-badge"></div>
            </div>
            <div class="skeleton-line skeleton-descripcion"></div>
            <div class="skeleton-line skeleton-fecha"></div>
            <div class="skeleton-actions">
                <div class="skeleton-btn"></div>
                <div class="skeleton-btn"></div>
                <div class="skeleton-btn"></div>
            </div>
        </div>
    `;
    return skeleton.repeat(3);
}

// ====================================================
// RENDERIZAR TAREAS
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
        lista.innerHTML = renderizarEmptyState();
        return;
    }

    lista.innerHTML = filtradas.map((t, i) => {
        const clases = ["tarea-card"];
        if (t.completada) clases.push("completada");
        clases.push(`prioridad-${t.prioridad}`);

        return `
            <div class="${clases.join(' ')}" style="animation-delay: ${i * 0.05}s">
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
                    <button class="btn-export-tarea" data-id="${t.id}" title="Exportar esta tarea">📥 Exportar</button>
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
    lista.querySelectorAll(".btn-export-tarea").forEach(btn => {
        btn.addEventListener("click", () => mostrarMenuExportar(parseInt(btn.dataset.id)));
    });
    lista.querySelectorAll(".btn-delete").forEach(btn => {
        btn.addEventListener("click", () => abrirModalEliminar(parseInt(btn.dataset.id)));
    });
}

function renderizarEmptyState() {
    const mensajes = {
        todas: {
            icono: "📝",
            titulo: "No hay tareas todavía",
            texto: "Crea tu primera tarea usando el formulario de arriba."
        },
        pendientes: {
            icono: "🎉",
            titulo: "¡Todo hecho!",
            texto: "No tienes tareas pendientes. ¡Buen trabajo!"
        },
        completadas: {
            icono: "🎯",
            titulo: "Aún no has completado tareas",
            texto: "Marca tus tareas como completadas para verlas aquí."
        }
    };

    const m = mensajes[filtroActual] || mensajes.todas;

    return `
        <div class="empty-state-container">
            <div class="empty-state-icono">${m.icono}</div>
            <h3 class="empty-state-titulo">${m.titulo}</h3>
            <p class="empty-state-texto">${m.texto}</p>
        </div>
    `;
}

// ====================================================
// DESCARGAR ARCHIVOS (con token JWT)
// ====================================================
async function descargarArchivo(endpoint, nombreSugerido) {
    const token = localStorage.getItem("access_token");
    if (!token) {
        window.location.href = "/login";
        return;
    }

    try {
        const respuesta = await fetch(endpoint, {
            headers: { "Authorization": `Bearer ${token}` },
        });

        if (!respuesta.ok) {
            let errorData = {};
            try { errorData = await respuesta.json(); } catch (e) {}
            mostrarToast(errorData.error || "Error al exportar", "error");
            return;
        }

        const blob = await respuesta.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = nombreSugerido;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);

        mostrarToast("Archivo descargado", "success");
    } catch (err) {
        console.error("Error al descargar:", err);
        mostrarToast("No se pudo descargar el archivo", "error");
    }
}

function exportarTodasPDF() {
    const timestamp = new Date().toISOString().slice(0, 10);
    descargarArchivo("/tareas/export/pdf", `tareas_${timestamp}.pdf`);
}

function exportarTodasExcel() {
    const timestamp = new Date().toISOString().slice(0, 10);
    descargarArchivo("/tareas/export/excel", `tareas_${timestamp}.xlsx`);
}

// ====================================================
// EXPORTAR TAREA INDIVIDUAL (MODAL)
// ====================================================
function mostrarMenuExportar(id) {
    const tarea = tareas.find(t => t.id === id);
    if (!tarea) return;

    tareaExportandoId = tarea.id;
    document.getElementById("exportar-titulo").textContent = `"${tarea.titulo}"`;
    document.getElementById("modal-exportar").classList.remove("hidden");
}

function cerrarModalExportar() {
    document.getElementById("modal-exportar").classList.add("hidden");
    tareaExportandoId = null;
}

function exportarTareaEnFormato(formato) {
    if (!tareaExportandoId) return;

    const tarea = tareas.find(t => t.id === tareaExportandoId);
    if (!tarea) { cerrarModalExportar(); return; }

    const nombreBase = `tarea_${tarea.id}_${tarea.titulo.replace(/[^\w]/g, "_").slice(0, 30)}`;

    const endpoints = {
        txt: { url: `/tareas/${tarea.id}/export/txt`, nombre: `${nombreBase}.txt` },
        pdf: { url: `/tareas/${tarea.id}/export/pdf`, nombre: `${nombreBase}.pdf` },
        excel: { url: `/tareas/${tarea.id}/export/excel`, nombre: `${nombreBase}.xlsx` },
    };

    const config = endpoints[formato];
    if (!config) { cerrarModalExportar(); return; }

    cerrarModalExportar();
    descargarArchivo(config.url, config.nombre);
}

// ====================================================
// CREAR TAREA
// ====================================================
async function crearTarea(e) {
    e.preventDefault();

    const titulo = document.getElementById("titulo").value.trim();
    const descripcion = document.getElementById("descripcion").value.trim() || null;
    const prioridad = document.getElementById("prioridad").value;
    const fecha_limite = document.getElementById("fecha_limite").value || null;

    if (!titulo) {
        mostrarToast("El título no puede estar vacío", "warning");
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
        mostrarToast("Tarea creada exitosamente", "success");
    } else {
        mostrarToast(data.error || "Error al crear la tarea", "error");
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
        tarea.completada = !tarea.completada;
        renderizarTareas();
        mostrarToast(
            tarea.completada ? "Tarea completada" : "Tarea reabierta",
            "success"
        );
    } else {
        mostrarToast(data.error || "Error al actualizar", "error");
    }
}

// ====================================================
// MODAL DE EDICIÓN
// ====================================================
function abrirModalEditar(id) {
    const tarea = tareas.find(t => t.id === id);
    if (!tarea) return;

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

    const id = tareaEditandoId;
    if (!id) return;

    const titulo = document.getElementById("edit-titulo").value.trim();
    const descripcion = document.getElementById("edit-descripcion").value.trim() || null;
    const prioridad = document.getElementById("edit-prioridad").value;
    const fecha_limite = document.getElementById("edit-fecha_limite").value || null;

    if (!titulo) {
        mostrarToast("El título no puede estar vacío", "warning");
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
        const index = tareas.findIndex(t => t.id === id);
        if (index !== -1) tareas[index] = data;
        cerrarModalEditar();
        renderizarTareas();
        mostrarToast("Tarea editada exitosamente", "success");
    } else {
        mostrarToast(data.error || "Error al guardar cambios", "error");
    }
}

// ====================================================
// MODAL DE ELIMINAR
// ====================================================
function abrirModalEliminar(id) {
    const tarea = tareas.find(t => t.id === id);
    if (!tarea) return;

    tareaEliminandoId = tarea.id;
    document.getElementById("eliminar-nombre-tarea").textContent =
        `"${tarea.titulo}" se eliminará permanentemente.`;

    document.getElementById("modal-eliminar").classList.remove("hidden");
}

function cerrarModalEliminar() {
    document.getElementById("modal-eliminar").classList.add("hidden");
    tareaEliminandoId = null;
}

async function confirmarEliminar() {
    const id = tareaEliminandoId;
    if (!id) return;

    const { ok, data } = await apiFetch(`/tareas/${id}`, { method: "DELETE" });

    if (ok) {
        tareas = tareas.filter(t => t.id !== id);
        cerrarModalEliminar();
        renderizarTareas();
        mostrarToast("Tarea eliminada", "success");
    } else {
        mostrarToast(data.error || "Error al eliminar", "error");
        cerrarModalEliminar();
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
    document.getElementById("btn-cancelar-exportar").addEventListener("click", cerrarModalExportar);
    document.getElementById("btn-cancelar-eliminar").addEventListener("click", cerrarModalEliminar);
    document.getElementById("btn-confirmar-eliminar").addEventListener("click", confirmarEliminar);
    document.getElementById("btn-export-pdf").addEventListener("click", exportarTodasPDF);
    document.getElementById("btn-export-excel").addEventListener("click", exportarTodasExcel);

    document.querySelectorAll(".btn-export-opcion").forEach(btn => {
        btn.addEventListener("click", () => exportarTareaEnFormato(btn.dataset.formato));
    });

    // Cerrar modal de eliminar al hacer clic fuera
    const modalEliminar = document.getElementById("modal-eliminar");
    modalEliminar.addEventListener("click", (e) => {
        if (e.target === modalEliminar) cerrarModalEliminar();
    });

    // Cerrar modales con Escape
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            if (!modalEliminar.classList.contains("hidden")) cerrarModalEliminar();
            if (!document.getElementById("modal-exportar").classList.contains("hidden")) cerrarModalExportar();
        }
    });

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