// ====================================================
// ESTADO GLOBAL
// ====================================================
let tareas = [];
let filtroEstado = "todas";
let filtroPrioridad = "todas";
let busquedaActual = "";
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
// CARGAR TAREAS
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
// ACTUALIZAR ESTADÍSTICAS
// ====================================================
function actualizarEstadisticas() {
    const total = tareas.length;
    const completadas = tareas.filter(t => t.completada).length;
    const pendientes = total - completadas;
    const vencidas = tareas.filter(t => estaVencida(t)).length;

    animarNumero("stat-total", total);
    animarNumero("stat-pendientes", pendientes);
    animarNumero("stat-completadas", completadas);
    animarNumero("stat-vencidas", vencidas);
}

function animarNumero(idElemento, valorFinal) {
    const el = document.getElementById(idElemento);
    if (!el) return;

    const valorActual = parseInt(el.textContent) || 0;
    if (valorActual === valorFinal) return;

    const duracion = 400;
    const pasos = 20;
    const incremento = (valorFinal - valorActual) / pasos;
    let paso = 0;

    const timer = setInterval(() => {
        paso++;
        el.textContent = Math.round(valorActual + incremento * paso);
        if (paso >= pasos) {
            el.textContent = valorFinal;
            clearInterval(timer);
        }
    }, duracion / pasos);
}

function estaVencida(tarea) {
    if (!tarea.fecha_limite || tarea.completada) return false;
    const hoy = new Date();
    hoy.setHours(0, 0, 0, 0);
    const fecha = new Date(tarea.fecha_limite + "T00:00:00");
    return fecha < hoy;
}

// ====================================================
// APLICAR FILTROS
// ====================================================
function tareasFiltradas() {
    return tareas.filter(t => {
        // Filtro por estado
        if (filtroEstado === "pendientes" && t.completada) return false;
        if (filtroEstado === "completadas" && !t.completada) return false;

        // Filtro por prioridad
        if (filtroPrioridad !== "todas" && t.prioridad !== filtroPrioridad) return false;

        // Búsqueda (título o descripción)
        if (busquedaActual) {
            const q = busquedaActual.toLowerCase();
            const titulo = (t.titulo || "").toLowerCase();
            const desc = (t.descripcion || "").toLowerCase();
            if (!titulo.includes(q) && !desc.includes(q)) return false;
        }

        return true;
    });
}

function hayFiltrosActivos() {
    return filtroEstado !== "todas" ||
           filtroPrioridad !== "todas" ||
           busquedaActual !== "";
}

// ====================================================
// RENDERIZAR
// ====================================================
function renderizarTareas() {
    const lista = document.getElementById("lista-tareas");
    const filtradas = tareasFiltradas();

    actualizarEstadisticas();
    actualizarContadorResultados(filtradas.length);

    if (tareas.length === 0) {
        lista.innerHTML = renderizarEmptyStateGeneral();
        return;
    }

    if (filtradas.length === 0) {
        lista.innerHTML = renderizarEmptyStateFiltros();
        return;
    }

    lista.innerHTML = filtradas.map((t, i) => {
        const clases = ["tarea-card"];
        if (t.completada) clases.push("completada");
        clases.push(`prioridad-${t.prioridad}`);
        if (estaVencida(t)) clases.push("vencida");

        const fechaTexto = t.fecha_limite
            ? (estaVencida(t) ? `📅 ${t.fecha_limite} (vencida)` : `📅 ${t.fecha_limite}`)
            : "";

        return `
            <div class="${clases.join(' ')}" style="animation-delay: ${i * 0.04}s">
                <div class="tarea-header">
                    <h3>${escapeHtml(t.titulo)}</h3>
                    <span class="badge badge-${t.prioridad}">${t.prioridad}</span>
                </div>
                ${t.descripcion ? `<p class="tarea-desc">${escapeHtml(t.descripcion)}</p>` : ""}
                ${fechaTexto ? `<p class="tarea-fecha">${fechaTexto}</p>` : ""}
                <div class="tarea-actions">
                    <button class="btn-toggle" data-id="${t.id}">
                        ${t.completada ? "↩️ Reabrir" : "✅ Completar"}
                    </button>
                    <button class="btn-edit" data-id="${t.id}">✏️ Editar</button>
                    <button class="btn-export-tarea" data-id="${t.id}" title="Exportar esta tarea">📥</button>
                    <button class="btn-delete" data-id="${t.id}">🗑️</button>
                </div>
            </div>
        `;
    }).join("");

    // Eventos
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

function actualizarContadorResultados(cantidad) {
    const el = document.getElementById("contador-resultados");
    if (!el) return;

    if (!hayFiltrosActivos()) {
        el.classList.add("hidden");
        return;
    }

    el.classList.remove("hidden");
    el.textContent = `🔎 Mostrando ${cantidad} de ${tareas.length} tarea(s)`;
}

function renderizarEmptyStateGeneral() {
    return `
        <div class="empty-state-container">
            <div class="empty-state-icono">📝</div>
            <h3 class="empty-state-titulo">No hay tareas todavía</h3>
            <p class="empty-state-texto">Crea tu primera tarea usando el formulario de arriba.</p>
        </div>
    `;
}

function renderizarEmptyStateFiltros() {
    const iconos = {
        todas: "🔍",
        pendientes: "🎉",
        completadas: "🎯"
    };

    let texto = "No hay tareas que coincidan con tu búsqueda o filtros.";
    if (filtroEstado === "pendientes" && !busquedaActual && filtroPrioridad === "todas") {
        texto = "No tienes tareas pendientes. ¡Buen trabajo!";
    } else if (filtroEstado === "completadas" && !busquedaActual && filtroPrioridad === "todas") {
        texto = "Aún no has completado tareas.";
    }

    return `
        <div class="empty-state-container">
            <div class="empty-state-icono">${iconos[filtroEstado] || "🔍"}</div>
            <h3 class="empty-state-titulo">Sin resultados</h3>
            <p class="empty-state-texto">${texto}</p>
            <button id="btn-limpiar-todo" class="btn-secondary" style="margin-top: 15px; width: auto; padding: 8px 20px;">
                Limpiar filtros
            </button>
        </div>
    `;
}

// ====================================================
// DESCARGAR ARCHIVOS
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
// EXPORTAR TAREA INDIVIDUAL
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
    boton.innerHTML = '<span class="spinner"></span>Creando...';
    
    const [respuesta] = await Promise.all([
        apiFetch("/tareas", {
            method: "POST",
            body: JSON.stringify({ titulo, descripcion, prioridad, fecha_limite }),
        }),
        new Promise(resolve => setTimeout(resolve, 500))
    ]);
    
    const { ok, data } = respuesta;
    
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
    boton.innerHTML = '<span class="spinner"></span>Guardando...';
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
// FILTROS Y BÚSQUEDA
// ====================================================
function configurarFiltros() {
    // Filtros de estado
    document.querySelectorAll(".filtro-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".filtro-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            filtroEstado = btn.dataset.filtro;
            renderizarTareas();
        });
    });

    // Filtro de prioridad
    const selectPrioridad = document.getElementById("filtro-prioridad");
    selectPrioridad.addEventListener("change", () => {
        filtroPrioridad = selectPrioridad.value;
        renderizarTareas();
    });

    // Buscador con debounce
    const buscador = document.getElementById("buscador");
    const btnLimpiar = document.getElementById("btn-limpiar-busqueda");
    let timeoutBusqueda = null;

    buscador.addEventListener("input", (e) => {
        const valor = e.target.value;

        // Mostrar/ocultar botón de limpiar
        if (valor) {
            btnLimpiar.classList.remove("hidden");
        } else {
            btnLimpiar.classList.add("hidden");
        }

        // Debounce: esperar 200ms tras el último tecleo
        clearTimeout(timeoutBusqueda);
        timeoutBusqueda = setTimeout(() => {
            busquedaActual = valor.trim();
            renderizarTareas();
        }, 200);
    });

    // Botón limpiar búsqueda
    btnLimpiar.addEventListener("click", () => {
        buscador.value = "";
        busquedaActual = "";
        btnLimpiar.classList.add("hidden");
        renderizarTareas();
        buscador.focus();
    });

    // Atajo: "/" enfoca el buscador
    document.addEventListener("keydown", (e) => {
        if (e.key === "/" && document.activeElement.tagName !== "INPUT" && document.activeElement.tagName !== "TEXTAREA") {
            e.preventDefault();
            buscador.focus();
        }
    });

    // Botón de limpiar todo (dentro del empty state)
    document.addEventListener("click", (e) => {
        if (e.target.id === "btn-limpiar-todo") {
            limpiarTodosFiltros();
        }
    });
}

function limpiarTodosFiltros() {
    filtroEstado = "todas";
    filtroPrioridad = "todas";
    busquedaActual = "";

    document.getElementById("buscador").value = "";
    document.getElementById("btn-limpiar-busqueda").classList.add("hidden");
    document.getElementById("filtro-prioridad").value = "todas";

    document.querySelectorAll(".filtro-btn").forEach(b => b.classList.remove("active"));
    document.querySelector('.filtro-btn[data-filtro="todas"]').classList.add("active");

    renderizarTareas();
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

    const modalEliminar = document.getElementById("modal-eliminar");
    modalEliminar.addEventListener("click", (e) => {
        if (e.target === modalEliminar) cerrarModalEliminar();
    });

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