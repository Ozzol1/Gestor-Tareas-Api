// ---------- LOGIN ----------
const loginForm = document.getElementById("login-form");
if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        ocultarError();

        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value;

        const { ok, data } = await apiFetch("/auth/login", {
            method: "POST",
            body: JSON.stringify({ email, password }),
        });

        if (ok) {
            localStorage.setItem("access_token", data.access_token);
            window.location.href = "/dashboard";
        } else {
            mostrarError(data.error || "Error al iniciar sesión");
        }
    });
}

// ---------- REGISTRO ----------
const registroForm = document.getElementById("registro-form");
if (registroForm) {
    registroForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        ocultarError();

        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value;

        const { ok, data } = await apiFetch("/auth/registro", {
            method: "POST",
            body: JSON.stringify({ email, password }),
        });

        if (ok) {
            alert("¡Cuenta creada! Ahora inicia sesión.");
            window.location.href = "/login";
        } else {
            mostrarError(data.error || "Error al registrarse");
        }
    });
}

// ---------- LOGOUT ----------
const btnLogout = document.getElementById("btn-logout");
if (btnLogout) {
    btnLogout.addEventListener("click", () => {
        localStorage.removeItem("access_token");
        window.location.href = "/login";
    });
}

// ---------- PROTECCIÓN DE DASHBOARD ----------
if (window.location.pathname === "/dashboard") {
    const token = localStorage.getItem("access_token");
    if (!token) {
        window.location.href = "/login";
    }
}